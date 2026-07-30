from datetime import datetime

from app.database import SessionLocal
from app.models.audit import AuditLog


class AuditLogger:

    def log(self, request_id, request, result):
        db = SessionLocal()

        audit = AuditLog(
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            action=request.get("action"),
            request=str(request),
            decision=result["decision"],
            reason=result["reason"]
        )

        db.add(audit)
        db.commit()
        db.close()