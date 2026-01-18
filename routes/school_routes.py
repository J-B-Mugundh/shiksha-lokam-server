"""
School Progress Tracking Routes
Handles school enrollment and progress tracking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

router = APIRouter()

from database import get_database

# ==================== REQUEST/RESPONSE MODELS ====================

class SchoolEnrollRequest(BaseModel):
    school_name: str
    school_code: Optional[str] = None
    district: str
    state: str
    execution_id: str
    primary_contact_name: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    primary_contact_email: Optional[str] = None

class SchoolResponse(BaseModel):
    progress_id: str
    school_name: str
    school_code: Optional[str]
    district: str
    state: str
    execution_id: str
    lfa_id: str
    organization_id: str
    overall_completion_percentage: int
    current_milestone: int
    status: str
    total_xp_earned: int
    enrolled_at: datetime

# ==================== HELPER FUNCTIONS ====================

def school_to_response(school: dict) -> dict:
    """Convert MongoDB school document to response format"""
    school["progress_id"] = str(school.pop("_id"))
    return school

# ==================== ROUTES ====================

@router.post("/enroll", response_model=SchoolResponse, status_code=201)
async def enroll_school(request: SchoolEnrollRequest):
    """Enroll a school in an execution program"""
    db = get_database()
    
    try:
        # Verify execution exists
        execution = db.executions.find_one({"_id": ObjectId(request.execution_id)})
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Get LFA and organization IDs from execution
        lfa_id = execution["lfa_id"]
        organization_id = execution["organization_id"]
        
        # Check if school already enrolled
        existing = db.school_progress.find_one({
            "execution_id": request.execution_id,
            "school_code": request.school_code
        })
        if existing:
            raise HTTPException(status_code=400, detail="School already enrolled in this execution")
        
        # Get actions from execution to initialize school actions
        execution_actions = list(db.execution_actions.find(
            {"execution_id": request.execution_id}
        ).sort("sequence_number", 1))
        
        school_actions = []
        for action in execution_actions:
            school_actions.append({
                "action_id": str(action["_id"]),
                "action_description": action["description"],
                "status": "locked",  # All start locked
                "started_at": None,
                "completed_at": None,
                "result_submitted": False,
                "result_id": None
            })
        
        # Get milestones from execution
        school_milestones = []
        for milestone in execution.get("milestones", []):
            school_milestones.append({
                "milestone_number": milestone["milestone_number"],
                "milestone_name": milestone["name"],
                "is_completed": False,
                "completed_at": None
            })
        
        # Create school progress document
        school_data = {
            "school_name": request.school_name,
            "school_code": request.school_code,
            "district": request.district,
            "state": request.state,
            "execution_id": request.execution_id,
            "lfa_id": lfa_id,
            "organization_id": organization_id,
            "actions": school_actions,
            "milestones": school_milestones,
            "overall_completion_percentage": 0,
            "current_milestone": 1,
            "status": "not_started",
            "total_xp_earned": 0,
            "primary_contact_name": request.primary_contact_name,
            "primary_contact_phone": request.primary_contact_phone,
            "primary_contact_email": request.primary_contact_email,
            "enrolled_at": datetime.utcnow(),
            "started_at": None,
            "last_activity_at": None,
            "completed_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.school_progress.insert_one(school_data)
        school_data["_id"] = result.inserted_id
        
        return school_to_response(school_data)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_all_schools(
    execution_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    status: Optional[str] = None
):
    """Get all schools with optional filters"""
    db = get_database()
    
    query = {}
    if execution_id:
        query["execution_id"] = execution_id
    if organization_id:
        query["organization_id"] = organization_id
    if district:
        query["district"] = district
    if state:
        query["state"] = state
    if status:
        query["status"] = status
    
    schools = list(db.school_progress.find(query).sort("enrolled_at", -1))
    
    return {
        "total": len(schools),
        "schools": [school_to_response(school) for school in schools]
    }

@router.get("/{progress_id}")
async def get_school_progress(progress_id: str):
    """Get detailed school progress"""
    db = get_database()
    
    try:
        school = db.school_progress.find_one({"_id": ObjectId(progress_id)})
        if not school:
            raise HTTPException(status_code=404, detail="School progress not found")
        
        # Get execution details
        execution = db.executions.find_one(
            {"_id": ObjectId(school["execution_id"])},
            {"lfa_name": 1, "current_milestone": 1}
        )
        
        # Get LFA details
        lfa = db.lfas.find_one(
            {"_id": ObjectId(school["lfa_id"])},
            {"name": 1, "theme_id": 1}
        )
        
        return {
            "school": school_to_response(school),
            "execution": {
                "execution_id": str(execution["_id"]),
                "lfa_name": execution["lfa_name"],
                "current_milestone": execution["current_milestone"]
            } if execution else None,
            "lfa": {
                "lfa_id": str(lfa["_id"]),
                "name": lfa["name"]
            } if lfa else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{progress_id}/actions/{action_index}")
async def update_school_action(progress_id: str, action_index: int, status: str):
    """Update a school's action status"""
    db = get_database()
    
    try:
        school = db.school_progress.find_one({"_id": ObjectId(progress_id)})
        if not school:
            raise HTTPException(status_code=404, detail="School progress not found")
        
        if action_index >= len(school["actions"]):
            raise HTTPException(status_code=400, detail="Invalid action index")
        
        # Update action status
        update_field = f"actions.{action_index}.status"
        update_data = {update_field: status, "updated_at": datetime.utcnow()}
        
        if status == "in_progress" and not school["actions"][action_index].get("started_at"):
            update_data[f"actions.{action_index}.started_at"] = datetime.utcnow()
        
        if status == "completed":
            update_data[f"actions.{action_index}.completed_at"] = datetime.utcnow()
        
        db.school_progress.update_one(
            {"_id": ObjectId(progress_id)},
            {"$set": update_data}
        )
        
        # Recalculate completion percentage
        school = db.school_progress.find_one({"_id": ObjectId(progress_id)})
        completed = sum(1 for action in school["actions"] if action["status"] == "completed")
        total = len(school["actions"])
        completion_pct = int((completed / total) * 100) if total > 0 else 0
        
        db.school_progress.update_one(
            {"_id": ObjectId(progress_id)},
            {"$set": {
                "overall_completion_percentage": completion_pct,
                "last_activity_at": datetime.utcnow()
            }}
        )
        
        return {"message": "Action updated successfully", "completion_percentage": completion_pct}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/execution/{execution_id}/summary")
async def get_execution_schools_summary(execution_id: str):
    """Get summary of all schools in an execution"""
    db = get_database()
    
    try:
        schools = list(db.school_progress.find({"execution_id": execution_id}))
        
        if not schools:
            return {
                "execution_id": execution_id,
                "total_schools": 0,
                "average_completion": 0,
                "schools_by_status": {}
            }
        
        # Calculate statistics
        total_schools = len(schools)
        average_completion = sum(s["overall_completion_percentage"] for s in schools) / total_schools
        
        # Count by status
        status_counts = {}
        for school in schools:
            status = school["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Find top performers
        top_schools = sorted(schools, key=lambda x: x["overall_completion_percentage"], reverse=True)[:5]
        
        return {
            "execution_id": execution_id,
            "total_schools": total_schools,
            "average_completion": round(average_completion, 2),
            "schools_by_status": status_counts,
            "top_performers": [
                {
                    "school_name": s["school_name"],
                    "completion": s["overall_completion_percentage"],
                    "xp_earned": s["total_xp_earned"]
                }
                for s in top_schools
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{progress_id}")
async def remove_school(progress_id: str):
    """Remove a school from an execution"""
    db = get_database()
    
    try:
        school = db.school_progress.find_one({"_id": ObjectId(progress_id)})
        if not school:
            raise HTTPException(status_code=404, detail="School progress not found")
        
        # Only allow deletion if not started or very minimal progress
        if school["overall_completion_percentage"] > 10:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove school with significant progress. Set to 'on_hold' instead."
            )
        
        db.school_progress.delete_one({"_id": ObjectId(progress_id)})
        
        return {"message": "School removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))