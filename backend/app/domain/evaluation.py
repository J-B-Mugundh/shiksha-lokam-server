def calculate_results(baseline: float, current: float, target: float) -> dict:
    improvement = current - baseline
    target_improvement = target - baseline

    if target_improvement <= 0:
        achievement_percentage = 0
    else:
        achievement_percentage = (improvement / target_improvement) * 100

    return {
        "improvement": improvement,
        "targetImprovement": target_improvement,
        "achievementPercentage": round(achievement_percentage, 2),
    }


def evaluate_achievement(achievement_percentage: float) -> dict:
    if achievement_percentage >= 100:
        return {
            "result": "excellent",
            "next_action": "UNLOCK",
            "message": "Target fully achieved",
        }
    elif achievement_percentage >= 80:
        return {
            "result": "satisfactory",
            "next_action": "UNLOCK",
            "message": "Minimum acceptable target achieved",
        }
    elif achievement_percentage >= 50:
        return {
            "result": "below_target",
            "next_action": "CORRECTIVE_REQUIRED",
            "message": "Below target, corrective required",
        }
    else:
        return {
            "result": "unsatisfactory",
            "next_action": "CORRECTIVE_MANDATORY",
            "message": "Significantly below target",
        }
