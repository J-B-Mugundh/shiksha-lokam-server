"""
Organization Management Routes
Handles NGO/CSO organization CRUD operations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

router = APIRouter()

from database import get_database

# ==================== REQUEST/RESPONSE MODELS ====================

class OrganizationCreateRequest(BaseModel):
    name: str
    org_type: str = Field(..., description="ngo|cso|foundation|govt|other")
    state: Optional[str] = None
    district: Optional[str] = None
    focus_areas: List[str] = Field(default=[], description="e.g., ['FLN', 'Career Readiness']")

class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    focus_areas: Optional[List[str]] = None

class OrganizationResponse(BaseModel):
    org_id: str
    name: str
    org_type: str
    state: Optional[str]
    district: Optional[str]
    focus_areas: List[str]
    is_verified: bool
    total_lfas: int
    created_at: datetime

# ==================== HELPER FUNCTIONS ====================

def org_to_response(org: dict) -> dict:
    """Convert MongoDB org document to response format"""
    org["org_id"] = str(org.pop("_id"))
    return org

# ==================== ROUTES ====================

@router.post("/", response_model=OrganizationResponse, status_code=201)
async def create_organization(request: OrganizationCreateRequest):
    """Create a new organization"""
    db = get_database()
    
    # Check if org name already exists
    existing = db.organizations.find_one({"name": request.name})
    if existing:
        raise HTTPException(status_code=400, detail="Organization with this name already exists")
    
    org_data = {
        "name": request.name,
        "org_type": request.org_type,
        "state": request.state,
        "district": request.district,
        "focus_areas": request.focus_areas,
        "is_verified": False,
        "total_lfas": 0,
        "created_at": datetime.utcnow()
    }
    
    result = db.organizations.insert_one(org_data)
    org_data["_id"] = result.inserted_id
    
    return org_to_response(org_data)

@router.get("/", response_model=List[OrganizationResponse])
async def get_all_organizations(
    org_type: Optional[str] = None,
    state: Optional[str] = None,
    verified_only: bool = False
):
    """Get all organizations with optional filters"""
    db = get_database()
    
    query = {}
    if org_type:
        query["org_type"] = org_type
    if state:
        query["state"] = state
    if verified_only:
        query["is_verified"] = True
    
    organizations = list(db.organizations.find(query).sort("created_at", -1))
    
    return [org_to_response(org) for org in organizations]

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: str):
    """Get organization by ID"""
    db = get_database()
    
    try:
        org = db.organizations.find_one({"_id": ObjectId(org_id)})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return org_to_response(org)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(org_id: str, request: OrganizationUpdateRequest):
    """Update organization details"""
    db = get_database()
    
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = db.organizations.update_one(
            {"_id": ObjectId(org_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        org = db.organizations.find_one({"_id": ObjectId(org_id)})
        return org_to_response(org)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{org_id}/verify")
async def verify_organization(org_id: str):
    """Mark organization as verified"""
    db = get_database()
    
    try:
        result = db.organizations.update_one(
            {"_id": ObjectId(org_id)},
            {"$set": {"is_verified": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return {"message": "Organization verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{org_id}/lfas")
async def get_organization_lfas(org_id: str):
    """Get all LFAs created by this organization"""
    db = get_database()
    
    try:
        lfas = list(db.lfas.find(
            {"organization_id": org_id}
        ).sort("created_at", -1))
        
        for lfa in lfas:
            lfa["lfa_id"] = str(lfa.pop("_id"))
        
        return {
            "organization_id": org_id,
            "total_lfas": len(lfas),
            "lfas": lfas
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{org_id}/stats")
async def get_organization_stats(org_id: str):
    """Get organization statistics"""
    db = get_database()
    
    try:
        # Verify org exists
        org = db.organizations.find_one({"_id": ObjectId(org_id)})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Count LFAs by status
        total_lfas = db.lfas.count_documents({"organization_id": org_id})
        draft_lfas = db.lfas.count_documents({"organization_id": org_id, "status": "draft"})
        approved_lfas = db.lfas.count_documents({"organization_id": org_id, "status": "approved"})
        in_execution = db.lfas.count_documents({"organization_id": org_id, "status": "in_execution"})
        
        # Count schools enrolled
        total_schools = db.school_progress.count_documents({"organization_id": org_id})
        
        return {
            "organization_id": org_id,
            "organization_name": org["name"],
            "total_lfas": total_lfas,
            "lfas_by_status": {
                "draft": draft_lfas,
                "approved": approved_lfas,
                "in_execution": in_execution
            },
            "total_schools_enrolled": total_schools
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{org_id}")
async def delete_organization(org_id: str):
    """Delete organization (only if no LFAs exist)"""
    db = get_database()
    
    try:
        # Check if org has any LFAs
        lfa_count = db.lfas.count_documents({"organization_id": org_id})
        if lfa_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete organization with {lfa_count} LFAs. Delete LFAs first."
            )
        
        result = db.organizations.delete_one({"_id": ObjectId(org_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return {"message": "Organization deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))