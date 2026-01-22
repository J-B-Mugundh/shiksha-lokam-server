from datetime import datetime
from database import db

class ActionResultRepository:

    async def create(
        self,
        execution_id: str,
        action_id: str,
        lfa_id: str,
        indicator: str,
        values: dict,
        calculated: dict,
        evaluation: dict,
        submitted_by: dict,
        is_corrective: bool = False,
        corrective_action_id: str | None = None,
        session=None,
    ) -> dict:
        doc = {
            "executionId": execution_id,
            "executionActionId": action_id,
            "lfaId": lfa_id,
            "indicator": indicator,
            "values": values,
            "calculated": calculated,
            "evaluation": evaluation,
            "isCorrectiveResult": is_corrective,
            "correctiveActionId": corrective_action_id,
            "submittedBy": submitted_by["_id"],
            "submittedByName": submitted_by.get("displayName"),
            "submittedAt": datetime.utcnow(),
        }

        res = await db.action_results.insert_one(doc, session=session)
        doc["_id"] = res.inserted_id
        return doc

    async def get_latest(self, action_id: str) -> dict | None:
        return await db.action_results.find_one(
            {"executionActionId": action_id},
            sort=[("submittedAt", -1)],
        )
