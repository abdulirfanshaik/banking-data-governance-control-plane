# Operations Runbook

1. Export the approved metadata snapshot and identity/grant population.
2. Confirm the assessment date and policy version in `config/policies.json`.
3. Run `make demo` for the synthetic example or call the assessment module with governed inputs.
4. Review critical findings first, followed by high and medium findings.
5. Send grant decisions to the access owner and object findings to the dataset owner.
6. Record approved exceptions outside this demo with owner, expiry and evidence.
7. Rerun after remediation and compare the evidence hashes and scorecard.

In production, retain every assessment run rather than replacing the prior one, restrict evidence access, and require independent certification for control closure.

