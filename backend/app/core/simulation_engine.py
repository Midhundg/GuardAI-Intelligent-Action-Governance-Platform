import time
import uuid

from app.core.policy_engine import PolicyEngine
from app.services.audit_logger import AuditLogger

class SimulationEngine:

    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.audit_logger = AuditLogger()

    def simulate(self, action_data: dict):

        start_time = time.perf_counter()

        # Evaluate using existing Policy Engine
        result = self.policy_engine.evaluate(action_data)

        end_time = time.perf_counter()

        evaluation_time_ms = round(
            (end_time - start_time) * 1000,
            2
        )
        
        sim_id = str(uuid.uuid4())
        
        # Log the evaluation
        self.audit_logger.log(sim_id, action_data, result)

        return {
            "simulation_id": sim_id,
            "decision": result["decision"],
            "reason": result["reason"],
            "matched_policy": result["matched_policy"],
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "confidence": result["confidence"],
            "explanation": result["explanation"],
            "evaluation_time_ms": evaluation_time_ms,
            "would_execute": False,
        }