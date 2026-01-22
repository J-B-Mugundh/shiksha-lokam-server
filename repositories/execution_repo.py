from database import db, to_object_id

class ExecutionRepository:

    async def create_from_lfa(self, lfa: dict, session=None) -> dict:
        doc = {
            "lfaId": lfa["_id"],
            "lfaName": lfa["name"],
            "organizationId": lfa["organization_id"],
            "status": "active",
            "currentLevelNumber": 1,
            "overallCompletionPercentage": 0,
            "totalXpEarned": 0,
            "stats": {
                "totalLevels": 0,
                "completedLevels": 0,
                "totalActions": 0,
                "completedActions": 0,
                "actionsWithCorrections": 0,
                "escalatedActions": 0,
                "averageAchievementPercentage": 0,
                "onTimeCompletionRate": 0,
            },
            "startedAt": None,
            "createdAt": None,
        }
        res = await db.executions.insert_one(doc, session=session)
        doc["_id"] = res.inserted_id
        return doc

    async def get_by_id(self, execution_id: str):
        return await db.executions.find_one({"_id": to_object_id(execution_id)})

    async def get_by_lfa_id(self, lfa_id: str):
        return await db.executions.find_one({"lfaId": to_object_id(lfa_id)})

    async def update_status(self, execution_id: str, status: str, session=None):
        await db.executions.update_one(
            {"_id": to_object_id(execution_id)},
            {"$set": {"status": status}},
            session=session,
        )

    async def mark_completed(self, execution_id: str, session=None):
        await db.executions.update_one(
            {"_id": to_object_id(execution_id)},
            {"$set": {"status": "completed"}},
            session=session,
        )
