from app.db.mongo import db
from datetime import datetime

class ExecutionActionRepository:

    async def bulk_create(
        self,
        execution_id: str,
        level_id: str,
        lfa_id: str,
        actions: list[dict],
        session=None,
    ):
        docs = []
        for a in actions:
            docs.append({
                "executionId": execution_id,
                "executionLevelId": level_id,
                "lfaId": lfa_id,
                "levelNumber": a["levelNumber"],
                "sequenceNumber": a["sequenceNumber"],
                "description": a["description"],
                "detailedSteps": a.get("detailedSteps", []),
                "timeline": a["timeline"],
                "successCriteria": a["successCriteria"],
                "status": "locked",
                "createdAt": datetime.utcnow(),
            })
        if docs:
            await db.execution_actions.insert_many(docs, session=session)

    async def get_first_incomplete(self, level_id: str, session=None):
        return await db.execution_actions.find_one(
            {
                "executionLevelId": level_id,
                "status": {"$ne": "completed"},
            },
            sort=[("sequenceNumber", 1)],
            session=session,
        )


    async def get_by_id(self, action_id: str):
        return await db.execution_actions.find_one({"_id": action_id})

    async def mark_in_progress(self, action_id: str, session=None):
        await db.execution_actions.update_one(
            {"_id": action_id},
            {
                "$set": {
                    "status": "in_progress",
                    "timeline.actualStartDate": datetime.utcnow(),
                }
            },
            session=session,
        )

    async def mark_pending_validation(self, action_id: str, session=None):
        await db.execution_actions.update_one(
            {"_id": action_id},
            {"$set": {"status": "pending_validation"}},
            session=session,
        )

    async def mark_completed(self, action_id: str, session=None):
        await db.execution_actions.update_one(
            {"_id": action_id},
            {
                "$set": {
                    "status": "completed",
                    "timeline.actualCompletionDate": datetime.utcnow(),
                }
            },
            session=session,
        )

    async def mark_corrective_required(self, action_id: str, session=None):
        await db.execution_actions.update_one(
            {"_id": action_id},
            {"$set": {"status": "corrective_required"}},
            session=session,
        )

    async def mark_escalated(self, action_id: str, session=None):
        await db.execution_actions.update_one(
            {"_id": action_id},
            {"$set": {"status": "escalated"}},
            session=session,
        )
