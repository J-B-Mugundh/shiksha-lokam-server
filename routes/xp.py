
from fastapi import APIRouter
from services.xp_service import get_user_xp
router=APIRouter()
@router.get("/users/{user_id}/xp")
async def xp(user_id:str):
    xp,lvl,to_next=await get_user_xp(user_id)
    return {"total_xp":xp,"level":lvl,"xp_to_next_level":to_next}
