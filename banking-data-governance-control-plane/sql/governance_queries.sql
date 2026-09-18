-- Critical and high findings
SELECT violation_id, rule_id, severity, object_type, object_name, finding, remediation
FROM policy_violations
WHERE severity IN ('CRITICAL', 'HIGH')
ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 ELSE 2 END, rule_id;

-- Access recertification actions
SELECT role_name, dataset_name, privilege, decision, reason_codes
FROM access_review
WHERE decision <> 'KEEP'
ORDER BY decision DESC, role_name, dataset_name;

-- Sensitive columns without masking
SELECT column.dataset_name, column.column_name, column.classification
FROM columns_metadata AS column
WHERE column.classification = 'RESTRICTED'
  AND TRIM(column.masking_policy) = '';

