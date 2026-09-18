# Architecture and Control Design

## Assessment inputs

| Input | Grain | Purpose |
| --- | --- | --- |
| Dataset catalog | One row per dataset | Domain, layer, sensitivity, owner, retention and certification |
| Column catalog | One row per column | Classification, masking policy and description |
| Lineage | One row per directed edge | Registered source-to-target dependency |
| Grants | One row per role/dataset privilege | Access recertification and least privilege |
| Identities | One row per identity | Role assignment and segregation of duties |

## Policy checks

- `GOV-OWNER-001`: missing accountable dataset owner;
- `GOV-MASK-001`: restricted column without masking;
- `GOV-ACCESS-001`: dataset sensitivity exceeds role clearance;
- `GOV-ACCESS-002`: inactive grant beyond the configured period;
- `GOV-ACCESS-003`: expired grant;
- `GOV-LINEAGE-001`: edge references an unregistered dataset;
- `GOV-LINEAGE-002`: governed dataset lacks upstream lineage;
- `GOV-SOD-001`: identity combines forbidden roles.

## Design decisions

Policy thresholds and role clearance are configuration rather than application code. Every finding identifies the exact governed object and remediation. The engine reviews the full population in one execution, writes a queryable evidence database, and hashes its inputs so the assessment can be reproduced.

## Enterprise mapping

| Demo | Enterprise implementation |
| --- | --- |
| CSV catalog | Unity Catalog Information Schema, DataHub or Apache Atlas API |
| JSON policy | Versioned policy-as-code repository with approval workflow |
| Local RBAC grants | Snowflake grants, Unity Catalog privileges and IAM groups |
| SQLite evidence | Governed control schema and immutable audit store |
| Markdown scorecard | Power BI/Tableau governance dashboard |
| CSV findings | ServiceNow/Jira remediation workflow |

## Regulatory relevance

The project demonstrates the technical controls that support privacy, PCI-DSS scope reduction and BCBS 239 principles such as ownership, accuracy, completeness, traceability and controlled access. It is not a claim of formal compliance certification.

