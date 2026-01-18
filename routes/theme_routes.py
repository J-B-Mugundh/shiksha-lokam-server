"""
Theme Management Routes
Handles program themes (FLN, Career Readiness, etc.)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

router = APIRouter()

from database import get_database

# ==================== REQUEST/RESPONSE MODELS ====================

class ThemeCreateRequest(BaseModel):
    name: str = Field(..., description="e.g., 'Foundational Literacy & Numeracy'")
    short_name: str = Field(..., description="e.g., 'FLN'")
    description: str
    challenge_statements: List[str] = Field(default=[], description="Common problems")

class ThemeUpdateRequest(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    description: Optional[str] = None
    challenge_statements: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ThemeResponse(BaseModel):
    theme_id: str
    name: str
    short_name: str
    description: str
    challenge_statements: List[str]
    is_active: bool
    created_at: datetime

# ==================== HELPER FUNCTIONS ====================

def theme_to_response(theme: dict) -> dict:
    """Convert MongoDB theme document to response format"""
    theme["theme_id"] = str(theme.pop("_id"))
    return theme

# ==================== ROUTES ====================

@router.post("/", response_model=ThemeResponse, status_code=201)
async def create_theme(request: ThemeCreateRequest):
    """Create a new theme"""
    db = get_database()
    
    # Check if theme name already exists
    existing = db.themes.find_one({"name": request.name})
    if existing:
        raise HTTPException(status_code=400, detail="Theme with this name already exists")
    
    theme_data = {
        "name": request.name,
        "short_name": request.short_name,
        "description": request.description,
        "challenge_statements": request.challenge_statements,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    result = db.themes.insert_one(theme_data)
    theme_data["_id"] = result.inserted_id
    
    return theme_to_response(theme_data)

@router.get("/", response_model=List[ThemeResponse])
async def get_all_themes(active_only: bool = True):
    """Get all themes"""
    db = get_database()
    
    query = {"is_active": True} if active_only else {}
    themes = list(db.themes.find(query).sort("name", 1))
    
    return [theme_to_response(theme) for theme in themes]

@router.get("/{theme_id}", response_model=ThemeResponse)
async def get_theme(theme_id: str):
    """Get theme by ID"""
    db = get_database()
    
    try:
        theme = db.themes.find_one({"_id": ObjectId(theme_id)})
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        return theme_to_response(theme)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{theme_id}", response_model=ThemeResponse)
async def update_theme(theme_id: str, request: ThemeUpdateRequest):
    """Update theme"""
    db = get_database()
    
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = db.themes.update_one(
            {"_id": ObjectId(theme_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        theme = db.themes.find_one({"_id": ObjectId(theme_id)})
        return theme_to_response(theme)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{theme_id}")
async def delete_theme(theme_id: str):
    """Deactivate theme (soft delete)"""
    db = get_database()
    
    try:
        result = db.themes.update_one(
            {"_id": ObjectId(theme_id)},
            {"$set": {"is_active": False}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        return {"message": "Theme deactivated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{theme_id}/lfas")
async def get_theme_lfas(theme_id: str):
    """Get all LFAs using this theme"""
    db = get_database()
    
    try:
        lfas = list(db.lfas.find({"theme_id": theme_id}).sort("created_at", -1))
        
        for lfa in lfas:
            lfa["lfa_id"] = str(lfa.pop("_id"))
        
        return {
            "theme_id": theme_id,
            "total_lfas": len(lfas),
            "lfas": lfas
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))