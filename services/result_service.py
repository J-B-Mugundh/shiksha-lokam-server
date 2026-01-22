from app.core.exceptions import DomainError
from database import mongo_transaction
from app.domain.evaluation import calculate_results, evaluate_achievement
from app.repositories.action_repo import ExecutionActionRepository
from app.repositories.result_repo import ActionResultRepository
from app.services.corrective_service import CorrectiveService

action_repo = ExecutionActionRepository()
result_repo = ActionResultRepository()
corrective_service = CorrectiveService()

class ResultService:

    async def submit_results(
        self,
        execution_id: str,
        action_id: str,
        payload: dict,
        user: dict,
        is_corrective: bool = False,
        corrective_action_id: str | None = None,
    ) -> dict:

        action = await action_repo.get_by_id(action_id)

        if not action:
            raise DomainError("Action not found")

        if action["status"] != "in_progress":
            raise DomainError("Results can only be submitted for in-progress actions")

        criteria = action["successCriteria"]

        # 1️⃣ Validate indicator
        if payload["indicator"] != criteria["indicator"]:
            raise DomainError("Indicator does not match action success criteria")

        # 2️⃣ Validate baseline
        if payload["values"]["baseline"] != criteria["baseline"]:
            raise DomainError("Baseline mismatch")

        # 3️⃣ Calculate results
        calculated = calculate_results(
            baseline=payload["values"]["baseline"],
            current=payload["values"]["current"],
            target=payload["values"]["target"],
        )

        # 4️⃣ Evaluate achievement
        evaluation = evaluate_achievement(calculated["achievementPercentage"])

        async with mongo_transaction() as session:
            # 5️⃣ Persist result
            result = await result_repo.create(
                execution_id=execution_id,
                action_id=action_id,
                lfa_id=action["lfaId"],
                indicator=payload["indicator"],
                values=payload["values"],
                calculated=calculated,
                evaluation=evaluation,
                submitted_by=user,
                is_corrective=is_corrective,
                corrective_action_id=corrective_action_id,
                session=session,
            )

            # 6️⃣ State transition
            if evaluation["next_action"] == "UNLOCK":
                await action_repo.mark_pending_validation(action_id, session=session)
            else:
                await corrective_service.generate(action, result, session=session)

        return result
