# GuardAI Policy Engine Rules

GuardAI uses a declarative rule engine to evaluate actions. This document explains the core policies.

## 1. Action Type Policy
Restricts specific highly destructive operations from being executed automatically.
- **Rule:** If `action_type == "delete_database"` or `action_type == "drop_table"`.
- **Result:** Automatically escalate to `CRITICAL` risk level and `BLOCK`.

## 2. Record Count Limit Policy
Prevents bulk data manipulation.
- **Rule:** If `parameters.record_count > 100`.
- **Result:** Flag as policy violation and `BLOCK`.
*(Note: If the record count is between 50 and 100, the system may route it to `FLAG_FOR_REVIEW` for human approval depending on the strictness level).*

## 3. External Domain Egress Policy
Prevents unauthorized data exfiltration to unrecognized domains.
- **Rule:** If `action_type == "http_request"` and `parameters.domain` is not in the allowed `WHITELIST`.
- **Result:** `BLOCK`.

## Customizing Policies
Currently, policies are evaluated in `backend/app/core/policies.yaml` (or via database seed). You can adjust the thresholds (e.g., changing the limit from 100 to 500) dynamically without needing to recompile the application code.
