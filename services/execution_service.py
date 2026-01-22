from datetime import datetime
from app.core.exceptions import DomainError
from database import mongo_transaction

from datetime import datetime, timedelta

from app.core.exceptions import DomainError
from database import mongo_transaction

from app.repositories.execution_repo import ExecutionRepository
from app.repositories.level_repo import ExecutionLevelRepository
from app.repositories.action_repo import ExecutionActionRepository
from app.repositories.lfa_repo import LFARepository



execution_repo = ExecutionRepository()
level_repo = ExecutionLevelRepository()
action_repo = ExecutionActionRepository()
lfa_repo = LFARepository()

class ExecutionService:

    async def get(self, execution_id: str) -> dict:
        execution = await execution_repo.get_by_id(execution_id)
        if not execution:
            raise DomainError("Execution not found")
        return execution

    async def list(self, filters, pagination, user):
        query = {}

        if filters.organization_id:
            query["organizationId"] = filters.organization_id

        if filters.status:
            query["status"] = {"$in": filters.status}

        cursor = (
            execution_repo.collection()
            .find(query)
            .skip(pagination.offset)
            .limit(pagination.limit)
            .sort("createdAt", -1)
        )

        items = [doc async for doc in cursor]
        total = await execution_repo.collection().count_documents(query)

        return {
            "items": items,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit,
        }

    async def pause(self, execution_id: str):
        execution = await self.get(execution_id)

        if execution["status"] != "active":
            raise DomainError("Only active executions can be paused")

        await execution_repo.update_status(execution_id, "paused")

    async def resume(self, execution_id: str):
        execution = await self.get(execution_id)

        if execution["status"] != "paused":
            raise DomainError("Only paused executions can be resumed")

        await execution_repo.update_status(execution_id, "active")

    async def abandon(self, execution_id: str):
        execution = await self.get(execution_id)

        if execution["status"] not in ["active", "paused"]:
            raise DomainError("Execution cannot be abandoned")

        await execution_repo.update_status(execution_id, "abandoned")

    async def check_and_complete(self, execution_id: str):
        current_level = await level_repo.get_current_level(execution_id)

        if current_level:
            return  # still running

        await execution_repo.mark_completed(execution_id)

    async def create_execution(self, payload, user):
        """
        POST /executions
        Deterministic execution bootstrap (NO AI)
        Fully aligned with Sections 5, 6, 7
        """

        async with mongo_transaction() as session:

            # ------------------------------------------------------------------
            # 1️⃣ Load and validate LFA
            # ------------------------------------------------------------------
            lfa = await lfa_repo.get_by_id(payload.lfa_id)
            if not lfa:
                raise DomainError("LFA not found")
            print(lfa)
            if lfa["status"] != "locked":
                raise DomainError("Only locked LFAs can be executed")

            # ------------------------------------------------------------------
            # 2️⃣ Prevent duplicate execution
            # ------------------------------------------------------------------
            existing = await execution_repo.get_by_lfa_id(lfa["_id"])
            if existing:
                raise DomainError("Execution already exists for this LFA")

            now = datetime.utcnow()

            # ------------------------------------------------------------------
            # 3️⃣ Create execution root (repo-driven)
            # ------------------------------------------------------------------
            execution = await execution_repo.create_from_lfa(lfa, session=session)

            # Set timestamps explicitly (repo leaves them null)
            await execution_repo.update_status(
                execution["_id"],
                "active",
                session=session
            )

            # ------------------------------------------------------------------
            # 4️⃣ Deterministic execution plan (repo-compatible)
            # ------------------------------------------------------------------
            plan = [
                {
                    "levelNumber": 1,
                    "name": "Foundation",
                    "timeline": {
                        "expectedStartDate": now,
                        "expectedEndDate": now + timedelta(days=30),
                    },
                    "actions": [
                        {
                            "levelNumber": 1,
                            "sequenceNumber": 1,
                            "description": "Baseline assessment and preparation",
                            "timeline": {
                                "deadline": now + timedelta(days=14),
                                "estimatedDurationDays": 7,
                            },
                            "successCriteria": {
                                "indicator": "Baseline readiness",
                                "indicatorType": "impact",
                                "baseline": 0,
                                "target": 100,
                                "minimumAcceptable": 80,
                            },
                        }
                    ],
                },
                {
                    "levelNumber": 2,
                    "name": "Launch",
                    "timeline": {
                        "expectedStartDate": now + timedelta(days=30),
                        "expectedEndDate": now + timedelta(days=60),
                    },
                    "actions": [
                        {
                            "levelNumber": 2,
                            "sequenceNumber": 1,
                            "description": "Initial rollout and monitoring",
                            "timeline": {
                                "deadline": now + timedelta(days=45),
                                "estimatedDurationDays": 10,
                            },
                            "successCriteria": {
                                "indicator": "Launch effectiveness",
                                "indicatorType": "outcome",
                                "baseline": 0,
                                "target": 100,
                                "minimumAcceptable": 80,
                            },
                        }
                    ],
                },
            ]

            # ------------------------------------------------------------------
            # 5️⃣ Create levels + actions
            # ------------------------------------------------------------------
            first_level_id = None

            for idx, level_data in enumerate(plan):
                is_first_level = idx == 0

                level = await level_repo.create(
                    execution_id=execution["_id"],
                    lfa_id=lfa["_id"],
                    level_data=level_data,
                    status="in_progress" if is_first_level else "locked",
                    session=session,
                )

                if is_first_level:
                    first_level_id = level["_id"]

                # Bulk create actions (ALL start locked)
                await action_repo.bulk_create(
                    execution_id=execution["_id"],
                    level_id=level["_id"],
                    lfa_id=lfa["_id"],
                    actions=level_data["actions"],
                    session=session,
                )

            # ------------------------------------------------------------------
            # 6️⃣ Explicitly unlock first action
            # ------------------------------------------------------------------
            first_action = await action_repo.get_first_incomplete(first_level_id, session=session)
            if not first_action:
                raise DomainError("No actions created for first level")

            await action_repo.mark_in_progress(
                first_action["_id"],
                session=session,
            )

            # ------------------------------------------------------------------
            # 7️⃣ Update LFA status → in_execution
            # ------------------------------------------------------------------
            await lfa_repo.update_status(
                lfa["_id"],
                "in_execution",
                session=session,
            )

            return execution
