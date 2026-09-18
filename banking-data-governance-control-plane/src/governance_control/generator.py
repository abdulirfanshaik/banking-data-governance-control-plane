from __future__ import annotations

import argparse
from pathlib import Path

from .io_utils import write_csv, write_json


DATASETS = [
    ("raw.core_customer", "CUSTOMER", "RAW", "RESTRICTED", "Customer Data Office", 2555, "N"),
    ("raw.card_authorization", "PAYMENTS", "RAW", "RESTRICTED", "Payments Data", 2555, "N"),
    ("raw.account_master", "ACCOUNTS", "RAW", "RESTRICTED", "Core Banking Data", 2555, "N"),
    ("curated.customer_360", "CUSTOMER", "CURATED", "RESTRICTED", "Customer Data Office", 1825, "Y"),
    ("curated.payment_activity", "PAYMENTS", "CURATED", "CONFIDENTIAL", "Payments Data", 1825, "Y"),
    ("curated.account_balances", "ACCOUNTS", "CURATED", "CONFIDENTIAL", "Core Banking Data", 2555, "Y"),
    ("curated.risk_features", "RISK", "CURATED", "CONFIDENTIAL", "Risk Data Office", 1825, "Y"),
    ("reporting.customer_service_view", "CUSTOMER", "REPORTING", "RESTRICTED", "Customer Operations", 365, "Y"),
    ("reporting.risk_portfolio", "RISK", "REPORTING", "CONFIDENTIAL", "Risk Data Office", 2555, "Y"),
    ("reporting.executive_kpis", "FINANCE", "REPORTING", "INTERNAL", "Finance Analytics", 730, "Y"),
    ("sandbox.campaign_analysis", "CUSTOMER", "SANDBOX", "INTERNAL", "Marketing Analytics", 90, "N"),
    ("sandbox.unowned_customer_copy", "CUSTOMER", "SANDBOX", "RESTRICTED", "", 30, "N"),
]

SPECIAL_COLUMNS = {
    "raw.core_customer": [("full_name", "RESTRICTED"), ("email_address", "RESTRICTED"), ("tax_id", "RESTRICTED")],
    "raw.card_authorization": [("card_pan", "RESTRICTED"), ("merchant_id", "CONFIDENTIAL"), ("amount", "CONFIDENTIAL")],
    "raw.account_master": [("account_number", "RESTRICTED"), ("customer_id", "CONFIDENTIAL"), ("balance", "CONFIDENTIAL")],
    "curated.customer_360": [("customer_id", "CONFIDENTIAL"), ("email_address", "RESTRICTED"), ("risk_segment", "CONFIDENTIAL")],
    "curated.payment_activity": [("customer_id", "CONFIDENTIAL"), ("transaction_amount", "CONFIDENTIAL"), ("merchant_category", "INTERNAL")],
    "curated.account_balances": [("account_number", "RESTRICTED"), ("available_balance", "CONFIDENTIAL"), ("product_type", "INTERNAL")],
    "curated.risk_features": [("customer_id", "CONFIDENTIAL"), ("risk_score", "CONFIDENTIAL"), ("risk_reason", "CONFIDENTIAL")],
    "reporting.customer_service_view": [("customer_id", "CONFIDENTIAL"), ("phone_number", "RESTRICTED"), ("account_number", "RESTRICTED")],
    "reporting.risk_portfolio": [("customer_id", "CONFIDENTIAL"), ("aggregate_exposure", "CONFIDENTIAL"), ("risk_band", "INTERNAL")],
    "reporting.executive_kpis": [("business_unit", "INTERNAL"), ("customer_count", "INTERNAL"), ("total_exposure", "CONFIDENTIAL")],
    "sandbox.campaign_analysis": [("customer_segment", "INTERNAL"), ("response_flag", "INTERNAL"), ("channel", "PUBLIC")],
    "sandbox.unowned_customer_copy": [("full_name", "RESTRICTED"), ("email_address", "RESTRICTED"), ("account_number", "RESTRICTED")],
}


def generate_catalog(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_rows = [
        {
            "dataset_name": name,
            "domain": domain,
            "layer": layer,
            "classification": classification,
            "owner_team": owner,
            "retention_days": retention,
            "certified": certified,
        }
        for name, domain, layer, classification, owner, retention, certified in DATASETS
    ]
    column_rows: list[dict[str, object]] = []
    missing_masking = {
        ("raw.card_authorization", "card_pan"),
        ("reporting.customer_service_view", "phone_number"),
        ("sandbox.unowned_customer_copy", "account_number"),
    }
    for dataset_name, *_ in DATASETS:
        columns = [
            ("record_id", "INTERNAL"),
            ("source_system", "INTERNAL"),
            ("legal_entity", "CONFIDENTIAL"),
            ("event_ts", "INTERNAL"),
            ("ingest_ts", "INTERNAL"),
            *SPECIAL_COLUMNS[dataset_name],
        ]
        for ordinal, (column_name, classification) in enumerate(columns, start=1):
            masking_policy = ""
            if classification == "RESTRICTED" and (dataset_name, column_name) not in missing_masking:
                masking_policy = "MASK_RESTRICTED"
            column_rows.append(
                {
                    "dataset_name": dataset_name,
                    "column_name": column_name,
                    "ordinal_position": ordinal,
                    "classification": classification,
                    "masking_policy": masking_policy,
                    "description": f"Governed {column_name.replace('_', ' ')} field",
                }
            )

    lineage_rows = [
        ("raw.core_customer", "curated.customer_360", "customer standardization"),
        ("raw.account_master", "curated.customer_360", "account relationship enrichment"),
        ("raw.card_authorization", "curated.payment_activity", "payment standardization"),
        ("raw.account_master", "curated.account_balances", "balance standardization"),
        ("curated.customer_360", "curated.risk_features", "customer risk enrichment"),
        ("curated.payment_activity", "curated.risk_features", "payment behavior features"),
        ("curated.customer_360", "reporting.customer_service_view", "service projection"),
        ("curated.account_balances", "reporting.customer_service_view", "account service projection"),
        ("curated.risk_features", "reporting.risk_portfolio", "portfolio aggregation"),
        ("curated.account_balances", "reporting.executive_kpis", "financial aggregation"),
        ("curated.customer_360", "sandbox.campaign_analysis", "approved de-identified export"),
        ("missing.legacy_customer", "sandbox.unowned_customer_copy", "unregistered legacy copy"),
    ]
    lineage = [
        {"source_dataset": source, "target_dataset": target, "transformation": transformation}
        for source, target, transformation in lineage_rows
    ]

    grants = [
        ("GRANT-001", "BUSINESS_ANALYST", "reporting.executive_kpis", "SELECT", "2026-09-10", "2027-01-01"),
        ("GRANT-002", "RISK_ANALYST", "reporting.risk_portfolio", "SELECT", "2026-09-15", "2027-01-01"),
        ("GRANT-003", "COMPLIANCE_ANALYST", "curated.customer_360", "SELECT", "2026-09-12", "2027-01-01"),
        ("GRANT-004", "DATA_ENGINEER", "raw.core_customer", "MODIFY", "2026-09-18", "2027-01-01"),
        ("GRANT-005", "BUSINESS_ANALYST", "reporting.customer_service_view", "SELECT", "2026-09-16", "2027-01-01"),
        ("GRANT-006", "PUBLIC_READER", "sandbox.campaign_analysis", "SELECT", "2026-09-01", "2027-01-01"),
        ("GRANT-007", "RISK_ANALYST", "curated.risk_features", "SELECT", "2026-05-01", "2027-01-01"),
        ("GRANT-008", "COMPLIANCE_ANALYST", "reporting.customer_service_view", "SELECT", "2026-09-01", "2026-08-31"),
        ("GRANT-009", "DATA_ENGINEER", "raw.card_authorization", "MODIFY", "2026-09-18", "2027-01-01"),
        ("GRANT-010", "BUSINESS_ANALYST", "curated.payment_activity", "SELECT", "2026-09-17", "2027-01-01"),
        ("GRANT-011", "PLATFORM_ADMIN", "raw.account_master", "OWN", "2026-09-18", "2027-01-01"),
        ("GRANT-012", "DATA_CERTIFIER", "reporting.executive_kpis", "CERTIFY", "2026-09-18", "2027-01-01"),
    ]
    grant_rows = [
        {
            "grant_id": grant_id,
            "role_name": role,
            "dataset_name": dataset,
            "privilege": privilege,
            "last_used_date": last_used,
            "expires_on": expires,
        }
        for grant_id, role, dataset, privilege, last_used, expires in grants
    ]

    identities = [
        {"identity_id": "USR-001", "display_name": "Data Engineer A", "roles": "DATA_ENGINEER"},
        {"identity_id": "USR-002", "display_name": "Risk Analyst A", "roles": "RISK_ANALYST"},
        {"identity_id": "USR-003", "display_name": "Compliance Analyst A", "roles": "COMPLIANCE_ANALYST"},
        {"identity_id": "USR-004", "display_name": "Control Administrator", "roles": "PLATFORM_ADMIN|DATA_CERTIFIER"},
        {"identity_id": "USR-005", "display_name": "Business Analyst A", "roles": "BUSINESS_ANALYST"},
        {"identity_id": "SVC-001", "display_name": "Pipeline Service", "roles": "DATA_ENGINEER"},
    ]

    write_csv(output_dir / "datasets.csv", dataset_rows, list(dataset_rows[0].keys()))
    write_csv(output_dir / "columns.csv", column_rows, list(column_rows[0].keys()))
    write_csv(output_dir / "lineage.csv", lineage, list(lineage[0].keys()))
    write_csv(output_dir / "grants.csv", grant_rows, list(grant_rows[0].keys()))
    write_csv(output_dir / "identities.csv", identities, list(identities[0].keys()))
    manifest = {
        "synthetic_data": True,
        "datasets": len(dataset_rows),
        "columns": len(column_rows),
        "lineage_edges": len(lineage),
        "access_grants": len(grant_rows),
        "identities": len(identities),
    }
    write_json(output_dir / "catalog_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a deterministic synthetic banking metadata catalog.")
    parser.add_argument("--output", type=Path, default=Path("data/input"))
    args = parser.parse_args()
    manifest = generate_catalog(args.output)
    print(f"Generated {manifest['datasets']} datasets and {manifest['columns']} columns")


if __name__ == "__main__":
    main()

