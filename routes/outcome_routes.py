"""
Outcome Management Routes
Handles stakeholder outcomes and indicators (reusable templates)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

router = APIRouter()

from database import get_database

# ==================== REQUEST/RESPONSE MODELS ====================

class OutcomeIndicatorModel(BaseModel):
    indicator_text: str
    baseline_value: Optional[str] = None
    target_value: Optional[str] = None
    measurement_method: Optional[str] = None

class OutcomeCreateRequest(BaseModel):
    outcome_statement: str = Field(..., description="What the stakeholder will achieve")
    stakeholder_type: str = Field(..., description="e.g., 'Teachers', 'Students', 'Principals'")
    indicators: List[OutcomeIndicatorModel] = Field(default=[])
    is_template: bool = Field(default=False)

class OutcomeUpdateRequest(BaseModel):
    outcome_statement: Optional[str] = None
    stakeholder_type: Optional[str] = None
    indicators: Optional[List[OutcomeIndicatorModel]] = None
    is_template: Optional[bool] = None

class OutcomeResponse(BaseModel):
    outcome_id: str
    outcome_statement: str
    stakeholder_type: str
    indicators: List[dict]
    is_template: bool
    created_by: Optional[str]
    created_at: datetime

# ==================== HELPER FUNCTIONS ====================

def outcome_to_response(outcome: dict) -> dict:
    """Convert MongoDB outcome document to response format"""
    outcome["outcome_id"] = str(outcome.pop("_id"))
    return outcome

# ==================== ROUTES ====================

@router.post("/", response_model=OutcomeResponse, status_code=201)
async def create_outcome(request: OutcomeCreateRequest, created_by: Optional[str] = None):
    """Create a new outcome statement"""
    db = get_database()
    
    outcome_data = {
        "outcome_statement": request.outcome_statement,
        "stakeholder_type": request.stakeholder_type,
        "indicators": [indicator.dict() for indicator in request.indicators],
        "is_template": request.is_template,
        "created_by": created_by,
        "created_at": datetime.utcnow()
    }
    
    result = db.outcomes.insert_one(outcome_data)
    outcome_data["_id"] = result.inserted_id
    
    return outcome_to_response(outcome_data)

@router.get("/", response_model=List[OutcomeResponse])
async def get_all_outcomes(
    stakeholder_type: Optional[str] = None,
    templates_only: bool = False
):
    """Get all outcomes with optional filters"""
    db = get_database()
    
    query = {}
    if stakeholder_type:
        query["stakeholder_type"] = stakeholder_type
    if templates_only:
        query["is_template"] = True
    
    outcomes = list(db.outcomes.find(query).sort("created_at", -1))
    
    return [outcome_to_response(outcome) for outcome in outcomes]

@router.get("/templates")
async def get_outcome_templates():
    """Get all reusable outcome templates"""
    db = get_database()
    
    outcomes = list(db.outcomes.find({"is_template": True}).sort("stakeholder_type", 1))
    
    # Group by stakeholder type
    grouped = {}
    for outcome in outcomes:
        stakeholder = outcome.get("stakeholder_type", "Other")
        if stakeholder not in grouped:
            grouped[stakeholder] = []
        grouped[stakeholder].append(outcome_to_response(outcome))
    
    return {
        "total_templates": len(outcomes),
        "by_stakeholder": grouped
    }

@router.get("/{outcome_id}", response_model=OutcomeResponse)
async def get_outcome(outcome_id: str):
    """Get outcome by ID"""
    db = get_database()
    
    try:
        outcome = db.outcomes.find_one({"_id": ObjectId(outcome_id)})
        if not outcome:
            raise HTTPException(status_code=404, detail="Outcome not found")
        
        return outcome_to_response(outcome)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{outcome_id}", response_model=OutcomeResponse)
async def update_outcome(outcome_id: str, request: OutcomeUpdateRequest):
    """Update outcome statement"""
    db = get_database()
    
    try:
        update_data = {}
        if request.outcome_statement is not None:
            update_data["outcome_statement"] = request.outcome_statement
        if request.stakeholder_type is not None:
            update_data["stakeholder_type"] = request.stakeholder_type
        if request.indicators is not None:
            update_data["indicators"] = [ind.dict() for ind in request.indicators]
        if request.is_template is not None:
            update_data["is_template"] = request.is_template
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = db.outcomes.update_one(
            {"_id": ObjectId(outcome_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Outcome not found")
        
        outcome = db.outcomes.find_one({"_id": ObjectId(outcome_id)})
        return outcome_to_response(outcome)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{outcome_id}")
async def delete_outcome(outcome_id: str):
    """Delete outcome (only if not used in any LFA)"""
    db = get_database()
    
    try:
        # Check if outcome is used in any LFA
        lfa_count = db.lfas.count_documents({"outcomes.outcome_id": outcome_id})
        if lfa_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete outcome used in {lfa_count} LFAs"
            )
        
        result = db.outcomes.delete_one({"_id": ObjectId(outcome_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Outcome not found")
        
        return {"message": "Outcome deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stakeholders/list")
async def get_stakeholder_types():
    """Get all unique stakeholder types"""
    db = get_database()
    
    stakeholder_types = db.outcomes.distinct("stakeholder_type")
    
    return {
        "total_types": len(stakeholder_types),
        "stakeholder_types": sorted(stakeholder_types)
    }