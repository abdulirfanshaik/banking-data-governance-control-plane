# Interview Guide

## 90-second explanation

“I built a metadata-driven banking governance control plane because a technically successful data platform can still create risk if ownership, PII classification, masking, access and lineage are incomplete. The project reads a catalog of datasets and columns, lineage edges, role grants and identity assignments. It evaluates policy-as-code for eight categories, including missing owners, restricted fields without masking, access above a role's clearance, stale or expired grants, broken lineage and segregation-of-duties conflicts.

Every finding includes severity, the exact governed object and a remediation action. The platform also makes a keep, review or revoke recommendation for every grant and calculates coverage metrics for ownership, classification, masking and lineage. I deliberately separated software execution from governance certification: the demo runs successfully but returns NON_COMPLIANT because the synthetic catalog contains known negative controls.

For an enterprise implementation, I would ingest metadata from Unity Catalog, Snowflake, DataHub or Apache Atlas, integrate identity data from IAM, publish exceptions to a controlled workflow, and retain immutable evidence. This project demonstrates how I translate regulated-data requirements into automated, testable engineering controls rather than relying on spreadsheet reviews.”

## Strong technical points

- Metadata is the project's primary data product.
- Role clearance and control thresholds are configuration-driven.
- Column-level policy is separate from dataset-level classification.
- Access review considers sensitivity, usage recency and expiry.
- Segregation of duties prevents an administrator from certifying their own changes.
- Evidence hashes support reproducibility and change detection.

## Likely questions

### Why is masking not enough by itself?

Masking protects values in specific access paths, but governance also requires least privilege, ownership, retention, lineage and monitoring. A user may still have direct table access that bypasses a masked view, so grants and policies must be evaluated together.

### How would you integrate Unity Catalog?

I would extract catalogs, schemas, tables, columns, tags, grants and lineage through system tables or approved APIs. I would normalize those into the project's metadata contract, run policy checks by environment, and write findings back to a control schema and workflow queue.

### How do you avoid false positives?

Policies need documented scope, exception metadata, effective dates and ownership. I would distinguish blocking failures from review findings, support approved time-bound exceptions, and test policy changes against representative catalogs before production rollout.

### What would you monitor?

Ownership coverage, classification coverage, restricted masking coverage, unapproved privileged grants, stale access, broken lineage, overdue exceptions, mean time to remediation and policy execution completeness.

## Resume positioning

Present this as a sanitized implementation of governance patterns related to the resume's Unity Catalog, RBAC, PII masking, lineage, auditability, PCI-DSS and BCBS 239 skills. Do not claim the synthetic percentages as employer outcomes.

