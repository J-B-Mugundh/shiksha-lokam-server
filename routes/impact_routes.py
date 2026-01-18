"""
Impact Management Routes
Handles impact statements and indicators (reusable templates)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

router = APIRouter()

from database import get_database

# ==================== REQUEST/RESPONSE MODELS ====================

class ImpactIndicatorModel(BaseModel):
    indicator_text: str
    baseline_value: Optional[str] = None
    target_value: Optional[str] = None
    measurement_method: Optional[str] = None

class ImpactCreateRequest(BaseModel):
    impact_statement: str = Field(..., description="What change we want to see")
    category: str = Field(..., description="e.g., 'Student Learning', 'Teacher Capacity'")
    indicators: List[ImpactIndicatorModel] = Field(default=[])
    theme_id: Optional[str] = None
    is_template: bool = Field(default=False, description="Is this reusable?")

class ImpactUpdateRequest(BaseModel):
    impact_statement: Optional[str] = None
    category: Optional[str] = None
    indicators: Optional[List[ImpactIndicatorModel]] = None
    is_template: Optional[bool] = None

class ImpactResponse(BaseModel):
    impact_id: str
    impact_statement: str
    category: str
    indicators: List[dict]
    theme_id: Optional[str]
    is_template: bool
    created_by: Optional[str]
    created_at: datetime

# ==================== HELPER FUNCTIONS ====================

def impact_to_response(impact: dict) -> dict:
    """Convert MongoDB impact document to response format"""
    impact["impact_id"] = str(impact.pop("_id"))
    return impact

# ==================== ROUTES ====================

@router.post("/", response_model=ImpactResponse, status_code=201)
async def create_impact(request: ImpactCreateRequest, created_by: Optional[str] = None):
    """Create a new impact statement"""
    db = get_database()
    
    impact_data = {
        "impact_statement": request.impact_statement,
        "category": request.category,
        "indicators": [indicator.dict() for indicator in request.indicators],
        "theme_id": request.theme_id,
        "is_template": request.is_template,
        "created_by": created_by,
        "created_at": datetime.utcnow()
    }
    
    result = db.impacts.insert_one(impact_data)
    impact_data["_id"] = result.inserted_id
    
    return impact_to_response(impact_data)

@router.get("/", response_model=List[ImpactResponse])
async def get_all_impacts(
    category: Optional[str] = None,
    theme_id: Optional[str] = None,
    templates_only: bool = False
):
    """Get all impacts with optional filters"""
    db = get_database()
    
    query = {}
    if category:
        query["category"] = category
    if theme_id:
        query["theme_id"] = theme_id
    if templates_only:
        query["is_template"] = True
    
    impacts = list(db.impacts.find(query).sort("created_at", -1))
    
    return [impact_to_response(impact) for impact in impacts]

@router.get("/templates")
async def get_impact_templates():
    """Get all reusable impact templates"""
    db = get_database()
    
    impacts = list(db.impacts.find({"is_template": True}).sort("category", 1))
    
    # Group by category
    grouped = {}
    for impact in impacts:
        category = impact.get("category", "Other")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(impact_to_response(impact))
    
    return {
        "total_templates": len(impacts),
        "by_category": grouped
    }

@router.get("/{impact_id}", response_model=ImpactResponse)
async def get_impact(impact_id: str):
    """Get impact by ID"""
    db = get_database()
    
    try:
        impact = db.impacts.find_one({"_id": ObjectId(impact_id)})
        if not impact:
            raise HTTPException(status_code=404, detail="Impact not found")
        
        return impact_to_response(impact)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{impact_id}", response_model=ImpactResponse)
async def update_impact(impact_id: str, request: ImpactUpdateRequest):
    """Update impact statement"""
    db = get_database()
    
    try:
        update_data = {}
        if request.impact_statement is not None:
            update_data["impact_statement"] = request.impact_statement
        if request.category is not None:
            update_data["category"] = request.category
        if request.indicators is not None:
            update_data["indicators"] = [ind.dict() for ind in request.indicators]
        if request.is_template is not None:
            update_data["is_template"] = request.is_template
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = db.impacts.update_one(
            {"_id": ObjectId(impact_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Impact not found")
        
        impact = db.impacts.find_one({"_id": ObjectId(impact_id)})
        return impact_to_response(impact)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{impact_id}")
async def delete_impact(impact_id: str):
    """Delete impact (only if not used in any LFA)"""
    db = get_database()
    
    try:
        # Check if impact is used in any LFA
        lfa_count = db.lfas.count_documents({"impacts.impact_id": impact_id})
        if lfa_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete impact used in {lfa_count} LFAs"
            )
        
        result = db.impacts.delete_one({"_id": ObjectId(impact_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Impact not found")
        
        return {"message": "Impact deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/categories/list")
async def get_impact_categories():
    """Get all unique impact categories"""
    db = get_database()
    
    categories = db.impacts.distinct("category")
    
    return {
        "total_categories": len(categories),
        "categories": sorted(categories)
    }