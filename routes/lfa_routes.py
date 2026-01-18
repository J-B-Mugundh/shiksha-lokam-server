"""
LFA (Logical Framework Approach) Routes
Core LFA creation, editing, review, and approval workflows
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import logging

from database import get_database

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["lfas"])

# ==================== REQUEST/RESPONSE MODELS ====================

class ImpactIndicatorInput(BaseModel):
    indicator_text: str
    baseline_value: Optional[str] = None
    target_value: Optional[str] = None
    measurement_method: Optional[str] = None

class LFAImpactInput(BaseModel):
    impact_id: str = Field(..., description="FK to impacts collection")
    custom_indicators: List[ImpactIndicatorInput] = Field(default=[])

class OutcomeIndicatorInput(BaseModel):
    indicator_text: str
    baseline_value: Optional[str] = None
    target_value: Optional[str] = None
    measurement_method: Optional[str] = None

class LFAOutcomeInput(BaseModel):
    outcome_id: str = Field(..., description="FK to outcomes collection")
    custom_indicators: List[OutcomeIndicatorInput] = Field(default=[])

class LFACreateRequest(BaseModel):
    name: str
    organization_id: str
    created_by: str
    target_grades: List[str] = Field(default=[])
    theme_id: Optional[str] = None
    challenge_statement: str
    challenge_context: Optional[str] = None
    program_name: Optional[str] = None
    program_description: Optional[str] = None
    inputs: Optional[List[dict]] = Field(default=[])
    activities: Optional[List[dict]] = Field(default=[])
    outputs: Optional[List[dict]] = Field(default=[])
    impact_ids: List[str] = Field(default=[])  # CHANGED: Just IDs
    outcome_ids: List[str] = Field(default=[])  # CHANGED: Just IDs

class LFAUpdateRequest(BaseModel):
    name: Optional[str] = None
    target_grades: Optional[List[str]] = None
    challenge_statement: Optional[str] = None
    challenge_context: Optional[str] = None
    program_name: Optional[str] = None
    program_description: Optional[str] = None
    inputs: Optional[List[dict]] = None
    activities: Optional[List[dict]] = None
    outputs: Optional[List[dict]] = None
    impact_ids: Optional[List[str]] = None  # CHANGED: Just IDs
    outcome_ids: Optional[List[str]] = None  # CHANGED: Just IDs

class ReviewFeedbackItem(BaseModel):
    section: str = Field(..., description="e.g., 'impacts', 'outcomes'")
    comment: str

class SubmitReviewRequest(BaseModel):
    decision: str = Field(..., description="approved|changes_requested|rejected")
    summary_feedback: str
    detailed_feedback: List[ReviewFeedbackItem] = Field(default=[])

# ==================== HELPER FUNCTIONS ====================

def lfa_to_response(lfa: dict) -> dict:
    """Convert MongoDB LFA document to response format"""
    lfa_copy = lfa.copy()
    lfa_copy["lfa_id"] = str(lfa_copy.pop("_id"))
    return lfa_copy

async def populate_lfa_references(db, lfa: dict) -> dict:
    """Populate full impact/outcome objects from IDs for API responses"""
    
    # Populate impact objects
    impacts_full = []
    for impact_id in lfa.get("impact_ids", []):
        try:
            impact = db.impacts.find_one({"_id": ObjectId(impact_id)})
            if impact:
                impacts_full.append({
                    "impact_id": impact_id,
                    "impact_statement": impact["impact_statement"],
                    "category": impact.get("category", "")
                })
        except Exception as e:
            logger.warning(f"Could not populate impact: {e}")
    lfa["impacts"] = impacts_full
    
    # Populate outcome objects
    outcomes_full = []
    for outcome_id in lfa.get("outcome_ids", []):
        try:
            outcome = db.outcomes.find_one({"_id": ObjectId(outcome_id)})
            if outcome:
                outcomes_full.append({
                    "outcome_id": outcome_id,
                    "outcome_statement": outcome["outcome_statement"],
                    "stakeholder_type": outcome.get("stakeholder_type", "")
                })
        except Exception as e:
            logger.warning(f"Could not populate outcome: {e}")
    lfa["outcomes"] = outcomes_full
    
    return lfa

# ==================== ROUTES ====================

@router.post("/", status_code=201)
async def create_lfa(request: LFACreateRequest):
    """Create a new LFA"""
    db = get_database()
    
    try:
        # Verify organization exists
        org = db.organizations.find_one({"_id": ObjectId(request.organization_id)})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Verify user exists
        user = db.users.find_one({"_id": ObjectId(request.created_by)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify all impacts exist
        for impact_id in request.impact_ids:
            impact = db.impacts.find_one({"_id": ObjectId(impact_id)})
            if not impact:
                raise HTTPException(status_code=404, detail=f"Impact {impact_id} not found")
        
        # Verify all outcomes exist
        for outcome_id in request.outcome_ids:
            outcome = db.outcomes.find_one({"_id": ObjectId(outcome_id)})
            if not outcome:
                raise HTTPException(status_code=404, detail=f"Outcome {outcome_id} not found")
        
        # Create LFA document (storing only IDs)
        lfa_data = {
            "name": request.name,
            "organization_id": request.organization_id,
            "created_by": request.created_by,
            "target_grades": request.target_grades,
            "theme_id": request.theme_id,
            "challenge_statement": request.challenge_statement,
            "challenge_context": request.challenge_context,
            "program_name": request.program_name,
            "program_description": request.program_description,
            "inputs": request.inputs or [],
            "activities": request.activities or [],
            "outputs": request.outputs or [],
            "impact_ids": request.impact_ids,  # Store only IDs
            "outcome_ids": request.outcome_ids,  # Store only IDs
            "status": "draft",
            "collaborators": [],
            "version": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "approved_at": None,
            "execution_started_at": None
        }
        
        result = db.lfas.insert_one(lfa_data)
        lfa_data["_id"] = result.inserted_id
        
        # Update organization LFA count
        db.organizations.update_one(
            {"_id": ObjectId(request.organization_id)},
            {"$inc": {"total_lfas": 1}}
        )
        
        logger.info(f"✅ LFA created successfully: {result.inserted_id}")
        
        return {
            "lfa_id": str(result.inserted_id),
            "name": request.name,
            "organization_id": request.organization_id,
            "status": "draft",
            "created_at": lfa_data["created_at"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating LFA: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_all_lfas(
    organization_id: Optional[str] = None,
    created_by: Optional[str] = None,
    status: Optional[str] = None,
    theme_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """Get all LFAs with optional filters"""
    db = get_database()
    
    query = {}
    if organization_id:
        query["organization_id"] = organization_id
    if created_by:
        query["created_by"] = created_by
    if status:
        query["status"] = status
    if theme_id:
        query["theme_id"] = theme_id
    
    total = db.lfas.count_documents(query)
    lfas = list(db.lfas.find(query).sort("created_at", -1).skip(skip).limit(limit))
    
    return {
        "total": total,
        "limit": limit,
        "skip": skip,
        "lfas": [lfa_to_response(lfa) for lfa in lfas]
    }

@router.get("/{lfa_id}")
async def get_lfa(lfa_id: str):
    """Get LFA by ID with full details"""
    db = get_database()
    
    try:
        if not ObjectId.is_valid(lfa_id):
            raise HTTPException(status_code=400, detail="Invalid LFA ID format")
        
        lfa = db.lfas.find_one({"_id": ObjectId(lfa_id)})
        if not lfa:
            raise HTTPException(status_code=404, detail="LFA not found")
        
        # Populate impact and outcome full objects
        lfa = await populate_lfa_references(db, lfa)
        
        # Get creator info
        creator = db.users.find_one({"_id": ObjectId(lfa["created_by"])}, {"first_name": 1, "last_name": 1, "email": 1})
        
        # Get organization info
        org = db.organizations.find_one({"_id": ObjectId(lfa["organization_id"])}, {"name": 1, "org_type": 1})
        
        return {
            "lfa": lfa_to_response(lfa),
            "creator": {
                "user_id": str(creator["_id"]),
                "name": f"{creator['first_name']} {creator['last_name']}",
                "email": creator["email"]
            } if creator else None,
            "organization": {
                "org_id": str(org["_id"]),
                "name": org["name"],
                "org_type": org["org_type"]
            } if org else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting LFA: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{lfa_id}")
async def update_lfa(lfa_id: str, request: LFAUpdateRequest):
    """Update LFA (only in draft or changes_requested status)"""
    db = get_database()
    
    try:
        if not ObjectId.is_valid(lfa_id):
            raise HTTPException(status_code=400, detail="Invalid LFA ID format")
        
        # Get existing LFA
        lfa = db.lfas.find_one({"_id": ObjectId(lfa_id)})
        if not lfa:
            raise HTTPException(status_code=404, detail="LFA not found")
        
        # Check if editable
        if lfa["status"] not in ["draft", "under_review"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot edit LFA in '{lfa['status']}' status"
            )
        
        update_data = {}
        
        if request.name is not None:
            update_data["name"] = request.name
        if request.target_grades is not None:
            update_data["target_grades"] = request.target_grades
        if request.challenge_statement is not None:
            update_data["challenge_statement"] = request.challenge_statement
        if request.challenge_context is not None:
            update_data["challenge_context"] = request.challenge_context
        if request.program_name is not None:
            update_data["program_name"] = request.program_name
        if request.program_description is not None:
            update_data["program_description"] = request.program_description
        if request.inputs is not None:
            update_data["inputs"] = request.inputs
        if request.activities is not None:
            update_data["activities"] = request.activities
        if request.outputs is not None:
            update_data["outputs"] = request.outputs
        if request.impact_ids is not None:
            # Verify all impacts exist
            for impact_id in request.impact_ids:
                impact = db.impacts.find_one({"_id": ObjectId(impact_id)})
                if not impact:
                    raise HTTPException(status_code=404, detail=f"Impact {impact_id} not found")
            update_data["impact_ids"] = request.impact_ids
        if request.outcome_ids is not None:
            # Verify all outcomes exist
            for outcome_id in request.outcome_ids:
                outcome = db.outcomes.find_one({"_id": ObjectId(outcome_id)})
                if not outcome:
                    raise HTTPException(status_code=404, detail=f"Outcome {outcome_id} not found")
            update_data["outcome_ids"] = request.outcome_ids
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow()
        
        db.lfas.update_one(
            {"_id": ObjectId(lfa_id)},
            {"$set": update_data}
        )
        
        logger.info(f"✅ LFA updated: {lfa_id}")
        return {"message": "LFA updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating LFA: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{lfa_id}/submit")
async def submit_lfa_for_review(lfa_id: str):
    """Submit LFA for review"""
    db = get_database()
    
    try:
        if not ObjectId.is_valid(lfa_id):
            raise HTTPException(status_code=400, detail="Invalid LFA ID format")
        
        lfa = db.lfas.find_one({"_id": ObjectId(lfa_id)})
        if not lfa:
            raise HTTPException(status_code=404, detail="LFA not found")
        
        if lfa["status"] != "draft":
            raise HTTPException(status_code=400, detail="Only draft LFAs can be submitted for review")
        
        # Validate LFA has minimum required data
        if not lfa.get("impact_ids") or len(lfa["impact_ids"]) == 0:
            raise HTTPException(status_code=400, detail="LFA must have at least one impact")
        if not lfa.get("outcome_ids") or len(lfa["outcome_ids"]) == 0:
            raise HTTPException(status_code=400, detail="LFA must have at least one outcome")
        
        db.lfas.update_one(
            {"_id": ObjectId(lfa_id)},
            {"$set": {"status": "under_review", "updated_at": datetime.utcnow()}}
        )
        
        logger.info(f"✅ LFA submitted for review: {lfa_id}")
        return {"message": "LFA submitted for review successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error submitting LFA: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{lfa_id}/reviews")
async def submit_review(lfa_id: str, reviewer_id: str, request: SubmitReviewRequest):
    """Submit a review for an LFA"""
    db = get_database()
    
    try:
        if not ObjectId.is_valid(lfa_id):
            raise HTTPException(status_code=400, detail="Invalid LFA ID format")
        
        lfa = db.lfas.find_one({"_id": ObjectId(lfa_id)})
        if not lfa:
            raise HTTPException(status_code=404, detail="LFA not found")
        
        if lfa["status"] != "under_review":
            raise HTTPException(status_code=400, detail="LFA is not under review")
        
        # Verify reviewer exists
        reviewer = db.users.find_one({"_id": ObjectId(reviewer_id)})
        if not reviewer:
            raise HTTPException(status_code=404, detail="Reviewer not found")
        
        # Create review document
        review_data = {
            "lfa_id": lfa_id,
            "lfa_version": lfa["version"],
            "reviewer_id": reviewer_id,
            "decision": request.decision,
            "summary_feedback": request.summary_feedback,
            "detailed_feedback": [item.dict() for item in request.detailed_feedback],
            "created_at": datetime.utcnow()
        }
        
        db.lfa_reviews.insert_one(review_data)
        
        # Update LFA status based on decision
        new_status = lfa["status"]
        if request.decision == "approved":
            new_status = "approved"
            approved_at = datetime.utcnow()
            db.lfas.update_one(
                {"_id": ObjectId(lfa_id)},
                {"$set": {
                    "status": new_status,
                    "approved_at": approved_at,
                    "updated_at": datetime.utcnow()
                }}
            )
            logger.info(f"✅ LFA approved: {lfa_id}")
        elif request.decision == "changes_requested":
            new_status = "draft"
            db.lfas.update_one(
                {"_id": ObjectId(lfa_id)},
                {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
            )
            logger.info(f"✅ Changes requested for LFA: {lfa_id}")
        elif request.decision == "rejected":
            new_status = "draft"
            db.lfas.update_one(
                {"_id": ObjectId(lfa_id)},
                {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
            )
            logger.info(f"✅ LFA rejected: {lfa_id}")
        
        return {
            "message": "Review submitted successfully",
            "new_status": new_status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error submitting review: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{lfa_id}/reviews")
async def get_lfa_reviews(lfa_id: str):
    """Get all reviews for an LFA"""
    db = get_database()
    
    try:
        if not ObjectId.is_valid(lfa_id):
            raise HTTPException(status_code=400, detail="Invalid LFA ID format")
        
        reviews = list(db.lfa_reviews.find({"lfa_id": lfa_id}).sort("created_at", -1))
        
        for review in reviews:
            review["review_id"] = str(review.pop("_id"))
            # Get reviewer info
            reviewer = db.users.find_one(
                {"_id": ObjectId(review["reviewer_id"])},
                {"first_name": 1, "last_name": 1, "email": 1}
            )
            if reviewer:
                review["reviewer_name"] = f"{reviewer['first_name']} {reviewer['last_name']}"
        
        return {
            "lfa_id": lfa_id,
            "total_reviews": len(reviews),
            "reviews": reviews
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting reviews: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{lfa_id}")
async def delete_lfa(lfa_id: str):
    """Delete LFA (only if in draft status)"""
    db = get_database()
    
    try:
        if not ObjectId.is_valid(lfa_id):
            raise HTTPException(status_code=400, detail="Invalid LFA ID format")
        
        lfa = db.lfas.find_one({"_id": ObjectId(lfa_id)})
        if not lfa:
            raise HTTPException(status_code=404, detail="LFA not found")
        
        if lfa["status"] != "draft":
            raise HTTPException(status_code=400, detail="Only draft LFAs can be deleted")
        
        db.lfas.delete_one({"_id": ObjectId(lfa_id)})
        
        # Update organization LFA count
        db.organizations.update_one(
            {"_id": ObjectId(lfa["organization_id"])},
            {"$inc": {"total_lfas": -1}}
        )
        
        logger.info(f"✅ LFA deleted: {lfa_id}")
        return {"message": "LFA deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting LFA: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))