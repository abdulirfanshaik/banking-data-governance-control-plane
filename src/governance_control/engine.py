from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import date
from pathlib import Path

from .io_utils import read_csv, read_json, sha256_file, write_csv, write_json


def _reset_output(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for child in output_dir.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def _violation(
    violations: list[dict[str, object]],
    rule_id: str,
    severity: str,
    object_type: str,
    object_name: str,
    finding: str,
    remediation: str,
) -> None:
    violations.append(
        {
            "violation_id": f"VIO-{len(violations) + 1:04d}",
            "rule_id": rule_id,
            "severity": severity,
            "object_type": object_type,
            "object_name": object_name,
            "finding": finding,
            "remediation": remediation,
            "status": "OPEN",
        }
    )


def assess_governance(input_dir: Path, output_dir: Path, policy_path: Path) -> dict[str, object]:
    _reset_output(output_dir)
    policy = read_json(policy_path)
    as_of = date.fromisoformat(policy["as_of_date"])
    datasets = read_csv(input_dir / "datasets.csv")
    columns = read_csv(input_dir / "columns.csv")
    lineage = read_csv(input_dir / "lineage.csv")
    grants = read_csv(input_dir / "grants.csv")
    identities = read_csv(input_dir / "identities.csv")
    dataset_index = {row["dataset_name"]: row for row in datasets}
    ranks = policy["classification_rank"]
    violations: list[dict[str, object]] = []

    for dataset in datasets:
        if not dataset["owner_team"].strip():
            _violation(
                violations,
                "GOV-OWNER-001",
                "HIGH",
                "DATASET",
                dataset["dataset_name"],
                "Dataset has no accountable owner.",
                "Assign an approved domain owner before access or certification.",
            )

    required_masking = set(policy["masking_required_for"])
    for column in columns:
        if column["classification"] in required_masking and not column["masking_policy"].strip():
            _violation(
                violations,
                "GOV-MASK-001",
                "HIGH",
                "COLUMN",
                f"{column['dataset_name']}.{column['column_name']}",
                "Restricted column has no masking policy.",
                "Attach the approved restricted-data masking policy and retest access paths.",
            )

    access_review: list[dict[str, object]] = []
    for grant in grants:
        dataset = dataset_index[grant["dataset_name"]]
        max_classification = policy["role_max_classification"][grant["role_name"]]
        exceeds_clearance = ranks[dataset["classification"]] > ranks[max_classification]
        last_used = date.fromisoformat(grant["last_used_date"])
        stale = (as_of - last_used).days > int(policy["maximum_inactivity_days"])
        expired = date.fromisoformat(grant["expires_on"]) < as_of
        reasons: list[str] = []
        if exceeds_clearance:
            reasons.append("CLASSIFICATION_EXCEEDS_ROLE")
            _violation(
                violations,
                "GOV-ACCESS-001",
                "HIGH",
                "GRANT",
                grant["grant_id"],
                f"{grant['role_name']} may access up to {max_classification}, but {grant['dataset_name']} is {dataset['classification']}.",
                "Remove direct access or use an approved masked/minimized view.",
            )
        if stale:
            reasons.append("STALE_USAGE")
            _violation(
                violations,
                "GOV-ACCESS-002",
                "MEDIUM",
                "GRANT",
                grant["grant_id"],
                f"Grant has been unused for {(as_of - last_used).days} days.",
                "Validate continued business need during access recertification.",
            )
        if expired:
            reasons.append("EXPIRED")
            _violation(
                violations,
                "GOV-ACCESS-003",
                "HIGH",
                "GRANT",
                grant["grant_id"],
                "Grant expiry date is before the assessment date.",
                "Revoke the grant or obtain a time-bound approved renewal.",
            )
        decision = "REVOKE" if exceeds_clearance or expired else "REVIEW" if stale else "KEEP"
        access_review.append({**grant, "decision": decision, "reason_codes": "|".join(reasons) or "COMPLIANT"})

    known_datasets = set(dataset_index)
    targets_with_lineage = {row["target_dataset"] for row in lineage if row["source_dataset"] in known_datasets}
    for edge in lineage:
        missing = [name for name in (edge["source_dataset"], edge["target_dataset"]) if name not in known_datasets]
        if missing:
            _violation(
                violations,
                "GOV-LINEAGE-001",
                "HIGH",
                "LINEAGE_EDGE",
                f"{edge['source_dataset']}->{edge['target_dataset']}",
                f"Lineage references unregistered dataset(s): {', '.join(missing)}.",
                "Register the dataset or remove the invalid lineage edge.",
            )
    for dataset in datasets:
        if dataset["layer"] in policy["lineage_required_layers"] and dataset["dataset_name"] not in targets_with_lineage:
            _violation(
                violations,
                "GOV-LINEAGE-002",
                "HIGH",
                "DATASET",
                dataset["dataset_name"],
                "Governed curated/reporting dataset has no registered upstream lineage.",
                "Capture source-to-target lineage before certification.",
            )

    forbidden_pairs = [set(pair) for pair in policy["forbidden_role_pairs"]]
    for identity in identities:
        roles = set(identity["roles"].split("|"))
        for forbidden in forbidden_pairs:
            if forbidden.issubset(roles):
                _violation(
                    violations,
                    "GOV-SOD-001",
                    "CRITICAL",
                    "IDENTITY",
                    identity["identity_id"],
                    f"Identity combines forbidden roles: {' + '.join(sorted(forbidden))}.",
                    "Separate platform administration from data certification duties.",
                )

    restricted_columns = [row for row in columns if row["classification"] in required_masking]
    masked_columns = [row for row in restricted_columns if row["masking_policy"].strip()]
    required_lineage = [row for row in datasets if row["layer"] in policy["lineage_required_layers"]]
    covered_lineage = [row for row in required_lineage if row["dataset_name"] in targets_with_lineage]
    summary = {
        "as_of_date": policy["as_of_date"],
        "population": {
            "datasets": len(datasets),
            "columns": len(columns),
            "lineage_edges": len(lineage),
            "access_grants": len(grants),
            "identities": len(identities),
        },
        "coverage": {
            "dataset_ownership_pct": round(100 * sum(bool(row["owner_team"].strip()) for row in datasets) / len(datasets), 2),
            "column_classification_pct": round(100 * sum(bool(row["classification"].strip()) for row in columns) / len(columns), 2),
            "restricted_masking_pct": round(100 * len(masked_columns) / len(restricted_columns), 2),
            "required_lineage_pct": round(100 * len(covered_lineage) / len(required_lineage), 2),
        },
        "violations": {
            "total": len(violations),
            "critical": sum(row["severity"] == "CRITICAL" for row in violations),
            "high": sum(row["severity"] == "HIGH" for row in violations),
            "medium": sum(row["severity"] == "MEDIUM" for row in violations),
        },
        "access_review": {
            "keep": sum(row["decision"] == "KEEP" for row in access_review),
            "review": sum(row["decision"] == "REVIEW" for row in access_review),
            "revoke": sum(row["decision"] == "REVOKE" for row in access_review),
        },
        "certification_status": "NON_COMPLIANT" if violations else "COMPLIANT",
    }

    write_csv(output_dir / "policy_violations.csv", violations, list(violations[0].keys()))
    write_csv(output_dir / "access_review.csv", access_review, list(access_review[0].keys()))
    write_json(output_dir / "governance_summary.json", summary)
    (output_dir / "governance_scorecard.md").write_text(_scorecard(summary), encoding="utf-8")
    evidence = {
        "input_sha256": {
            path.name: sha256_file(path)
            for path in sorted(input_dir.glob("*"))
            if path.is_file()
        },
        "policy_sha256": sha256_file(policy_path),
        "summary": summary,
    }
    write_json(output_dir / "control_evidence.json", evidence)
    _write_database(output_dir / "governance_controls.db", datasets, columns, lineage, grants, identities, violations, access_review)
    return summary


def _write_database(path: Path, datasets, columns, lineage, grants, identities, violations, access_review) -> None:
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        for table_name, rows in {
            "datasets": datasets,
            "columns_metadata": columns,
            "lineage": lineage,
            "grants_metadata": grants,
            "identities": identities,
            "policy_violations": violations,
            "access_review": access_review,
        }.items():
            fields = list(rows[0].keys())
            column_definitions = ", ".join(f'"{field}" TEXT' for field in fields)
            connection.execute(f'CREATE TABLE "{table_name}" ({column_definitions})')
            connection.executemany(
                f'INSERT INTO "{table_name}" VALUES ({", ".join("?" for _ in fields)})',
                [[str(row.get(field, "")) for field in fields] for row in rows],
            )
        connection.commit()
    finally:
        connection.close()


def _scorecard(summary: dict[str, object]) -> str:
    population = summary["population"]
    coverage = summary["coverage"]
    violations = summary["violations"]
    access = summary["access_review"]
    return f"""# Governance Control Scorecard

**Assessment date:** {summary['as_of_date']}  
**Certification:** **{summary['certification_status']}**

## Catalog population

| Measure | Count |
| --- | ---: |
| Datasets | {population['datasets']} |
| Columns | {population['columns']} |
| Lineage edges | {population['lineage_edges']} |
| Access grants | {population['access_grants']} |
| Identities | {population['identities']} |

## Coverage

| Control | Coverage |
| --- | ---: |
| Dataset ownership | {coverage['dataset_ownership_pct']:.2f}% |
| Column classification | {coverage['column_classification_pct']:.2f}% |
| Restricted-column masking | {coverage['restricted_masking_pct']:.2f}% |
| Required lineage | {coverage['required_lineage_pct']:.2f}% |

## Findings

| Measure | Count |
| --- | ---: |
| Total violations | {violations['total']} |
| Critical | {violations['critical']} |
| High | {violations['high']} |
| Medium | {violations['medium']} |
| Grants to keep | {access['keep']} |
| Grants requiring review | {access['review']} |
| Grants to revoke | {access['revoke']} |

The demonstration intentionally includes negative-control scenarios. `NON_COMPLIANT` proves that blocking governance issues are detected and routed; it does not indicate a software failure.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Assess governance, privacy, lineage and access controls.")
    parser.add_argument("--input", type=Path, default=Path("data/input"))
    parser.add_argument("--output", type=Path, default=Path("data/output"))
    parser.add_argument("--policy", type=Path, default=Path("config/policies.json"))
    args = parser.parse_args()
    summary = assess_governance(args.input, args.output, args.policy)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

