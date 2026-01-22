from app.repositories.action_repo import ExecutionActionRepository
from app.repositories.level_repo import ExecutionLevelRepository
from app.core.exceptions import DomainError

action_repo = ExecutionActionRepository()
level_repo = ExecutionLevelRepository()

class ActionService:

    async def get_current_action(self, execution_id: str):
        level = await level_repo.get_current_level(execution_id)

        if not level:
            return {"execution_completed": True}

        action = await action_repo.get_first_incomplete(level["_id"])

        if not action:
            return {
                "level_completed": True,
                "level": level
            }

        previous = await action_repo.get_previous(action)

        return {
            "level": level,
            "action": action,
            "previous_action_summary": previous
        }
