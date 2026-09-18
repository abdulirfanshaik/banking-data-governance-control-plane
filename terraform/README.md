# Infrastructure-as-Code Deployment Boundary

A production Terraform module would provision the control schema, service principal, secret-store references, scheduled job, least-privilege grants, encrypted evidence storage, log retention and alert destinations. Environment-specific identities and secret values must be injected through the approved deployment platform and must never be committed.

This repository keeps the runnable demo cloud-neutral. That makes the governance rules testable locally while allowing an organization to map them to Databricks, Snowflake, AWS or Azure resources without changing the policy contract.

