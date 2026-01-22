
from fastapi import APIRouter
from database import db
router=APIRouter(prefix="/admin")
@router.get("/analytics/completion")
async def completion():
    total=await db.lfas.count_documents({})
    completed=await db.lfas.count_documents({"status":"completed"})
    return {"total_lfas":total,"completed_lfas":completed}
