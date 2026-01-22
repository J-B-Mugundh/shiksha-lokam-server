from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date, datetime


class ActionStep(BaseModel):
    step_number: int
    description: str


class ActionTimeline(BaseModel):
    deadline: date
    estimated_duration_days: int
    actual_start_date: Optional[date]
    actual_completion_date: Optional[date]
    days_remaining: int
    is_overdue: bool


class SuccessCriteria(BaseModel):
    indicator: str
    indicator_id: Optional[str]
    indicator_type: Literal["impact", "outcome"]
    measurement_method: str
    baseline: float
    target: float
    minimum_acceptable: float
    data_source: Optional[str]
    sample_size: Optional[int]


class ActionGamification(BaseModel):
    base_xp: int
    xp_earned: Optional[int]
    potential_xp: int


class CorrectiveTracking(BaseModel):
    attempts_used: int
    max_attempts: int
    can_have_more_corrective: bool


class ExecutionActionResponse(BaseModel):
    id: str
    execution_id: str
    execution_level_id: str
    level_number: int
    sequence_number: int
    description: str
    detailed_steps: List[ActionStep]
    timeline: ActionTimeline
    success_criteria: SuccessCriteria
    status: str
    gamification: ActionGamification
    corrective: CorrectiveTracking
    predecessor_action_id: Optional[str]
    created_at: datetime


class ActionSummary(BaseModel):
    id: str
    description: str
    status: str


class ExecutionLevelSummary(BaseModel):
    id: str
    level_number: int
    name: str
    status: str


class CurrentActionResponse(BaseModel):
    level: Optional[ExecutionLevelSummary]
    action: Optional[ExecutionActionResponse]
    previous_action_summary: Optional[ActionSummary]
    execution_completed: Optional[bool] = False
    level_completed: Optional[bool] = False
