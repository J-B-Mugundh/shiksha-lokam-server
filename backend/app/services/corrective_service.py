from app.core.exceptions import DomainError
from app.repositories.corrective_repo import CorrectiveActionRepository
from app.repositories.action_repo import ExecutionActionRepository

corrective_repo = CorrectiveActionRepository()
action_repo = ExecutionActionRepository()

class CorrectiveService:

    async def generate(self, parent_action: dict, result: dict, session=None):
        attempts = await corrective_repo.count_attempts(parent_action["_id"])

        if attempts >= 2:
            await action_repo.mark_escalated(parent_action["_id"], session=session)
            return

        # AI placeholder (replace later)
        corrective_data = {
            "description": f"Improve outcome for {parent_action['description']}",
            "rationale": "Initial attempt did not meet target",
            "specificSteps": [],
            "timeline": parent_action["timeline"],
            "aiDiagnosis": {
                "rootCause": "Insufficient implementation fidelity",
                "contributingFactors": ["Training gap", "Time constraints"],
                "confidence": 0.75,
            },
        }

        await corrective_repo.create(
            parent_action=parent_action,
            triggering_result=result,
            corrective_data=corrective_data,
            attempt_number=attempts + 1,
            session=session,
        )

        await action_repo.mark_corrective_required(parent_action["_id"], session=session)

    async def get_for_action(self, action_id: str) -> dict:
        corrective = await corrective_repo.get_latest(action_id)
        if not corrective:
            raise DomainError("No corrective action found")
        return corrective

    async def accept(self, corrective_id: str):
        corrective = await corrective_repo.get_by_id(corrective_id)
        if corrective["status"] != "pending":
            raise DomainError("Corrective cannot be accepted")

        await corrective_repo.mark_accepted(corrective_id)
        return corrective

    async def complete(
        self,
        corrective_id: str,
        evaluation: dict,
        session=None,
    ) -> dict:
        corrective = await corrective_repo.get_by_id(corrective_id)

        if evaluation["next_action"] == "UNLOCK":
            await corrective_repo.mark_completed(corrective_id, session=session)
            await action_repo.mark_completed(
                corrective["parentActionId"], session=session
            )
            return {"parent_action_resolved": True}

        attempts = await corrective_repo.count_attempts(corrective["parentActionId"])

        if attempts >= 2:
            await corrective_repo.mark_failed(corrective_id, session=session)
            await action_repo.mark_escalated(
                corrective["parentActionId"], session=session
            )
            return {"parent_action_resolved": False, "escalated": True}

        await corrective_repo.mark_failed(corrective_id, session=session)
        return {"parent_action_resolved": False, "retry": True}
