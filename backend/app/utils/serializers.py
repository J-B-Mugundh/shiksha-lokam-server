from bson import ObjectId

def serialize_execution(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "lfa_id": str(doc["lfaId"]),
        "lfa_name": doc["lfaName"],
        "organization_id": str(doc["organizationId"]),
        "organization_name": doc.get("organizationName"),
        "status": doc["status"],
        "current_level_number": doc["currentLevelNumber"],
        "overall_completion_percentage": doc["overallCompletionPercentage"],
        "total_xp_earned": doc["totalXpEarned"],
        "stats": {
            "total_levels": doc["stats"]["totalLevels"],
            "completed_levels": doc["stats"]["completedLevels"],
            "total_actions": doc["stats"]["totalActions"],
            "completed_actions": doc["stats"]["completedActions"],
            "actions_with_corrections": doc["stats"]["actionsWithCorrections"],
            "escalated_actions": doc["stats"]["escalatedActions"],
            "average_achievement_percentage": doc["stats"]["averageAchievementPercentage"],
            "on_time_completion_rate": doc["stats"]["onTimeCompletionRate"],
        },
        "started_at": doc["startedAt"],
        "created_at": doc["createdAt"],
    }
