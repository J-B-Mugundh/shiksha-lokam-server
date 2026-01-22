
from database import db
from bson import ObjectId
from datetime import datetime

async def progress(user_id:str):
    user=await db.users.find_one({"_id":ObjectId(user_id)})
    earned=await db.user_achievements.find({"userId":ObjectId(user_id)}).to_list(None)
    earned_ids={e["achievementId"] for e in earned}
    achievements=await db.achievements.find({"isActive":True}).to_list(None)
    out=[]
    for a in achievements:
        if a["_id"] in earned_ids: continue
        key,val=list(a["criteria"].items())[0]
        cur=user["gamification"].get(key,0)
        out.append({"achievement_id":str(a["_id"]),"current":cur,"required":val})
    return out

async def claim(user_id:str, achievement_id:str):
    ach=await db.achievements.find_one({"_id":ObjectId(achievement_id)})
    await db.user_achievements.insert_one({
        "userId":ObjectId(user_id),
        "achievementId":ach["_id"],
        "earnedAt":datetime.utcnow()
    })
    xp=ach.get("xpReward",0)
    await db.users.update_one({"_id":ObjectId(user_id)},{"$inc":{"gamification.totalXp":xp}})
    await db.xp_transactions.insert_one({
        "userId":ObjectId(user_id),
        "amount":xp,
        "reason":"achievement",
        "createdAt":datetime.utcnow()
    })
    return xp
