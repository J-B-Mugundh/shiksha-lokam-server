from database import db
from datetime import datetime

class ExecutionLevelRepository:

    async def create(
        self,
        execution_id: str,
        lfa_id: str,
        level_data: dict,
        status: str,
        session=None,
    ):
        doc = {
            "executionId": execution_id,
            "lfaId": lfa_id,
            "levelNumber": level_data["levelNumber"],
            "name": level_data["name"],
            "description": level_data.get("description"),
            "mappedImpactIds": level_data.get("mappedImpactIds", []),
            "mappedOutcomeIds": level_data.get("mappedOutcomeIds", []),
            "timeline": level_data["timeline"],
            "status": status,
            "progress": {
                "totalActions": 0,
                "completedActions": 0,
                "completionPercentage": 0,
            },
            "createdAt": datetime.utcnow(),
        }
        res = await db.execution_levels.insert_one(doc, session=session)
        doc["_id"] = res.inserted_id
        return doc

    async def get_current_level(self, execution_id: str):
        return await db.execution_levels.find_one(
            {"executionId": execution_id, "status": "in_progress"}
        )

    async def mark_completed(self, level_id: str, session=None):
        await db.execution_levels.update_one(
            {"_id": level_id},
            {
                "$set": {
                    "status": "completed",
                    "timeline.actualEndDate": datetime.utcnow(),
                }
            },
            session=session,
        )
