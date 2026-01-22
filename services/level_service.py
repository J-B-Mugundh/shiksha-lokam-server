from app.core.exceptions import DomainError
from database import mongo_transaction
from app.repositories.level_repo import ExecutionLevelRepository

level_repo = ExecutionLevelRepository()

class LevelService:

    async def get_levels(self, execution_id: str):
        cursor = level_repo.collection().find(
            {"executionId": execution_id}
        ).sort("levelNumber", 1)

        return [lvl async for lvl in cursor]

    async def unlock_next_level(self, execution_id: str):
        next_level = await level_repo.get_next_locked_level(execution_id)
        if not next_level:
            return

        await level_repo.mark_in_progress(next_level["_id"])

    async def is_level_complete(self, level_id: str) -> bool:
        count = await level_repo.collection().count_documents({
            "executionLevelId": level_id,
            "status": {"$ne": "completed"}
        })
        return count == 0

    async def complete_level(self, level_id: str):
        level = await level_repo.get_by_id(level_id)

        if level["status"] != "in_progress":
            raise DomainError("Level not in progress")

        async with mongo_transaction():
            await level_repo.mark_completed(level_id)
            await self.unlock_next_level(level["executionId"])
