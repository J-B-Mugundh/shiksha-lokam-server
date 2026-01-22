
from pydantic import BaseModel
from typing import List

class GenerateLevelsRequest(BaseModel):
    lfa_id: str
    lfa_content: dict

class GeneratedAction(BaseModel):
    sequence_number: int
    description: str
    success_indicator: str
    mapped_indicator_ids: List[str]
    confidence: float
    rationale: str

class GeneratedLevel(BaseModel):
    level_number: int
    name: str
    description: str
    timeline_months: int
    mapped_impact_ids: List[str]
    mapped_outcome_ids: List[str]
    confidence: float
    rationale: str
    actions: List[GeneratedAction]
