
from database import db
from bson import ObjectId

LEVELS=[0,1000,2500,5000,10000]

def calc_level(xp:int):
    lvl=1
    for i,v in enumerate(LEVELS):
        if xp>=v: lvl=i+1
    nxt=LEVELS[lvl] if lvl<len(LEVELS) else LEVELS[-1]*2
    return lvl, max(nxt-xp,0)

async def get_user_xp(user_id:str):
    u=await db.users.find_one({"_id":ObjectId(user_id)})
    xp=u["gamification"]["totalXp"]
    lvl,to_next=calc_level(xp)
    return xp,lvl,to_next
