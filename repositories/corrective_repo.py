from datetime import datetime
from database import db

class CorrectiveActionRepository:

    async def create(
        self,
        parent_action: dict,
        triggering_result: dict,
        corrective_data: dict,
        attempt_number: int,
        session=None,
    ) -> dict:
        doc = {
            "parentActionId": parent_action["_id"],
            "triggeringResultId": triggering_result["_id"],
            "executionId": parent_action["executionId"],
            "lfaId": parent_action["lfaId"],
            "attemptNumber": attempt_number,
            "description": corrective_data["description"],
            "rationale": corrective_data.get("rationale"),
            "specificSteps": corrective_data.get("specificSteps", []),
            "timeline": corrective_data["timeline"],
            "successCriteria": parent_action["successCriteria"],
            "status": "pending",
            "gamification": {
                "baseXp": int(parent_action.get("gamification", {}).get("baseXp", 1000) * 0.5)
            },
            "aiDiagnosis": corrective_data.get("aiDiagnosis"),
            "userCustomized": False,
            "createdAt": datetime.utcnow(),
        }

        res = await db.corrective_actions.insert_one(doc, session=session)
        doc["_id"] = res.inserted_id
        return doc

    async def get_by_parent_action(self, action_id: str):
        cursor = db.corrective_actions.find(
            {"parentActionId": action_id}
        ).sort("attemptNumber", -1)
        return [doc async for doc in cursor]

    async def count_attempts(self, action_id: str) -> int:
        return await db.corrective_actions.count_documents(
            {"parentActionId": action_id}
        )

    async def get_latest(self, action_id: str) -> dict | None:
        return await db.corrective_actions.find_one(
            {"parentActionId": action_id},
            sort=[("attemptNumber", -1)],
        )

    async def mark_accepted(self, corrective_id: str, session=None):
        await db.corrective_actions.update_one(
            {"_id": corrective_id},
            {
                "$set": {
                    "status": "accepted",
                    "acceptedAt": datetime.utcnow(),
                }
            },
            session=session,
        )

    async def mark_completed(self, corrective_id: str, session=None):
        await db.corrective_actions.update_one(
            {"_id": corrective_id},
            {
                "$set": {
                    "status": "completed",
                    "completedAt": datetime.utcnow(),
                }
            },
            session=session,
        )

    async def mark_failed(self, corrective_id: str, session=None):
        await db.corrective_actions.update_one(
            {"_id": corrective_id},
            {"$set": {"status": "failed"}},
            session=session,
        )
