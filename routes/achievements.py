
from fastapi import APIRouter
from services.achievement_engine import progress, claim
router=APIRouter()
@router.get("/users/{user_id}/achievements/progress")
async def ach_progress(user_id:str):
    return await progress(user_id)
@router.post("/users/{user_id}/achievements/{achievement_id}/claim")
async def ach_claim(user_id:str, achievement_id:str):
    xp=await claim(user_id,achievement_id)
    return {"xp_awarded":xp}
