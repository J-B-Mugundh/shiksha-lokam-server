from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date, datetime
from app.models.execution_action import ActionStep, SuccessCriteria


class AIDiagnosis(BaseModel):
    root_cause: str
    contributing_factors: List[str]
    confidence: float


class CorrectiveTimeline(BaseModel):
    deadline: date
    estimated_duration_days: int
    actual_completion_date: Optional[date]


class CorrectiveGamification(BaseModel):
    base_xp: int
    xp_earned: Optional[int]


class CorrectiveActionResponse(BaseModel):
    id: str
    parent_action_id: str
    triggering_result_id: str
    attempt_number: int
    description: str
    rationale: Optional[str]
    specific_steps: List[ActionStep]
    timeline: CorrectiveTimeline
    success_criteria: SuccessCriteria
    status: Literal[
        "pending",
        "accepted",
        "in_progress",
        "completed",
        "failed"
    ]
    gamification: CorrectiveGamification
    ai_diagnosis: Optional[AIDiagnosis]
    user_customized: bool
    created_at: datetime

from pydantic import BaseModel
from typing import Optional, List
from app.models.execution_action import ActionStep


class CustomizeCorrectiveRequest(BaseModel):
    description: Optional[str]
    specific_steps: Optional[List[ActionStep]]
