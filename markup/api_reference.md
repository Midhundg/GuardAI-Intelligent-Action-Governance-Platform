# GuardAI API Reference

This document provides examples of how to interact with the GuardAI REST API.

## 🚀 Evaluate Action Endpoint
**URL:** `POST /api/v1/evaluate`

Evaluates an AI-generated action against the policy engine.

### Example Request (cURL)
```bash
curl -X POST "http://localhost:8000/api/v1/evaluate" \
     -H "Content-Type: application/json" \
     -d '{
           "request_id": "req_123456",
           "agent_id": "agent_data_processor",
           "action_type": "delete_database",
           "parameters": {
               "record_count": 150,
               "target_table": "users"
           },
           "dry_run": false
         }'
```

### Example Response (Blocked)
```json
{
  "status": "success",
  "verdict": "BLOCK",
  "risk_level": "CRITICAL",
  "reason": "Policy Violation: Record count of 150 exceeds the maximum allowed limit of 100.",
  "timestamp": "2026-07-31T14:30:00Z"
}
```

## 🕵️ Shadow Mode (Dry Run)
To test an action without generating side-effects (like writing to the approval queue or blocking live workflows), simply set `"dry_run": true` in your JSON payload. The system will return `"[WOULD] BLOCK"` or `"[WOULD] ALLOW"`.
