from datetime import datetime

from app.database import SessionLocal
from app.models.audit import AuditLog


class AuditLogger:

    def log(self, request_id, request, result):
        db = SessionLocal()

        matched_rule = result.get("matched_policy_name") or result.get("matched_policy") or "None"
        reason_text = f"Matched Rule: {matched_rule} | Reason: {result.get('reason')}"

        audit = AuditLog(
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            action=request.get("action"),
            request=str(request),
            decision=result["decision"],
            reason=reason_text
        )

        db.add(audit)
        db.commit()
        db.close()