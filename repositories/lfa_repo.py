from database import db, to_object_id
from datetime import datetime


class LFARepository:

    async def get_by_id(self, lfa_id: str) -> dict | None:
        return await db.lfas.find_one({"_id": to_object_id(lfa_id)})

    async def update_status(
        self,
        lfa_id: str,
        status: str,
        session=None,
    ):
        await db.lfas.update_one(
            {"_id": to_object_id(lfa_id)},
            {
                "$set": {
                    "status": status,
                    "updatedAt": datetime.utcnow(),
                    "lockedAt": datetime.utcnow() if status == "locked" else None,
                }
            },
            session=session,
        )
