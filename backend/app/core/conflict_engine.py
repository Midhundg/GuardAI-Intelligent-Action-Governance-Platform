from app.models.policy import Policy


class ConflictEngine:
    def find_conflicts(self, policies: list[Policy]):
        conflicts = []

        for i in range(len(policies)):
            for j in range(i + 1, len(policies)):
                p1 = policies[i]
                p2 = policies[j]

                if (
                    p1.action == p2.action
                    and p1.condition_type == p2.condition_type
                    and p1.condition_value == p2.condition_value
                    and p1.decision != p2.decision
                ):
                    conflicts.append(
                        {
                            "policy_1": p1.name,
                            "policy_2": p2.name,
                            "reason": (
                                "Both policies match the same action and "
                                "condition but have different decisions."
                            ),
                        }
                    )

        return conflicts