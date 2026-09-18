# Unity Catalog Integration Mapping

An enterprise adapter would normalize these Unity Catalog concepts into the local contract:

| Unity Catalog concept | Local field |
| --- | --- |
| Catalog, schema and table name | `dataset_name` |
| Table owner | `owner_team` |
| Tags/comments | domain, classification and description |
| Column tags | column classification |
| Row filters and column masks | `masking_policy` |
| Grants | role, object and privilege |
| System lineage | source and target dataset edge |

Use a service principal with metadata-read permissions, write assessment results to a restricted control schema, and keep policy changes under pull-request approval. The local project deliberately avoids requiring a Databricks workspace or credentials.

