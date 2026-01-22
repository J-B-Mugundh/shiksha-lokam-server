from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class ExecutionStats(BaseModel):
    total_levels: int
    completed_levels: int
    total_actions: int
    completed_actions: int
    actions_with_corrections: int
    escalated_actions: int
    average_achievement_percentage: float
    on_time_completion_rate: float


class ExecutionResponse(BaseModel):
    id: str
    lfa_id: str
    lfa_name: str
    organization_id: str
    organization_name: str
    status: Literal["active", "paused", "completed", "abandoned"]
    current_level_number: int
    overall_completion_percentage: int
    total_xp_earned: int
    stats: ExecutionStats
    started_at: Optional[datetime]
    created_at: datetime


class ExecutionSummaryResponse(BaseModel):
    id: str
    lfa_id: str
    lfa_name: str
    status: str
    current_level_number: int
    overall_completion_percentage: int
    created_at: datetime

from pydantic import BaseModel
from typing import Optional, List, Literal


class CreateExecutionRequest(BaseModel):
    lfa_id: str


class ExecutionFilterParams(BaseModel):
    organization_id: Optional[str]
    status: Optional[List[
        Literal["active", "paused", "completed", "abandoned"]
    ]]
