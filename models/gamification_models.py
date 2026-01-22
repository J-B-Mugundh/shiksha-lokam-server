
from pydantic import BaseModel
from typing import Optional, Dict

class XPBreakdown(BaseModel):
    baseAmount: Optional[int]
    qualityMultiplier: Optional[float]
    timeBonus: Optional[int]
    timePenalty: Optional[int]
    correctivePenalty: Optional[int]
