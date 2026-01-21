from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date


class LevelTimeline(BaseModel):
    expected_start_date: date
    expected_end_date: date
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]


class LevelProgress(BaseModel):
    total_actions: int
    completed_actions: int
    completion_percentage: int


class LevelGamification(BaseModel):
    base_xp: int
    completion_bonus_xp: int
    xp_earned: int


class ExecutionLevelResponse(BaseModel):
    id: str
    execution_id: str
    level_number: int
    name: str
    description: Optional[str]
    status: Literal["locked", "in_progress", "completed"]
    timeline: LevelTimeline
    progress: LevelProgress
    gamification: Optional[LevelGamification]
    mapped_impact_ids: List[str]
    mapped_outcome_ids: List[str]


class LevelListResponse(BaseModel):
    levels: List[ExecutionLevelResponse]
