from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class ResultValues(BaseModel):
    baseline: float
    current: float
    target: float


class CalculatedResults(BaseModel):
    improvement: float
    target_improvement: float
    achievement_percentage: float


class EvaluationResult(BaseModel):
    result: Literal[
        "excellent",
        "satisfactory",
        "below_target",
        "unsatisfactory"
    ]
    message: str
    next_action: Literal[
        "UNLOCK",
        "CORRECTIVE_REQUIRED",
        "CORRECTIVE_MANDATORY"
    ]


class ResultResponse(BaseModel):
    id: str
    execution_action_id: str
    indicator: str
    values: ResultValues
    calculated: CalculatedResults
    evaluation: EvaluationResult
    submitted_by: str
    submitted_at: datetime


from pydantic import BaseModel
from typing import Optional
from datetime import date


class ResultValuesRequest(BaseModel):
    baseline: float
    current: float
    target: float


class MeasurementDetailsRequest(BaseModel):
    method: str
    sample_size: Optional[int]
    data_source: Optional[str]
    collection_date: date


class SubmitResultsRequest(BaseModel):
    indicator: str
    values: ResultValuesRequest
    measurement: MeasurementDetailsRequest
    evidence_urls: Optional[list[str]] = []
    notes: Optional[str]
