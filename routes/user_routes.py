"""
User Management Routes
Handles user registration, authentication, profile management
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import bcrypt
import logging
from database import get_database

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])

# ==================== REQUEST/RESPONSE MODELS ====================

class UserRegistrationRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(..., min_length=8)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    platform_role: str
    organizations: List[dict] = []
    gamification: dict
    is_active: bool
    created_at: datetime

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class AddOrganizationRequest(BaseModel):
    organization_id: str
    role: str = Field(..., description="Role in organization, e.g., 'Program Manager'")

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    try:
        salt = bcrypt.gensalt(rounds=10)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password hashing failed"
        )

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

def user_to_response(user: dict) -> UserResponse:
    """Convert MongoDB user document to response format"""
    try:
        # Don't modify the original dict
        user_id = str(user.get("_id", ""))
        
        return UserResponse(
            user_id=user_id,
            email=user.get("email", ""),
            first_name=user.get("first_name", ""),
            last_name=user.get("last_name", ""),
            platform_role=user.get("platform_role", "user"),
            organizations=user.get("organizations", []),
            gamification=user.get("gamification", {}),
            is_active=user.get("is_active", True),
            created_at=user.get("created_at", datetime.utcnow())
        )
    except Exception as e:
        logger.error(f"Error converting user to response: {str(e)}")
        raise

# ==================== ROUTES ====================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: UserRegistrationRequest):
    """
    Register a new user
    
    - **email**: User email address (must be unique)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **password**: Password (minimum 8 characters)
    """
    try:
        db = get_database()
        
        # Validate email is not already registered
        existing_user = db.users.find_one({"email": request.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Create user document - NO google_id field
        user_data = {
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "password_hash": hashed_password,
            "platform_role": "user",
            "organizations": [],
            "gamification": {
                "total_xp": 0,
                "current_level": 1,
                "current_streak": 0,
                "longest_streak": 0,
                "last_activity_date": None
            },
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into database
        result = db.users.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        
        logger.info(f"✅ User registered successfully: {request.email}")
        return user_to_response(user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error during user registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during registration: {str(e)}"
        )

@router.post("/login")
async def login_user(request: UserLoginRequest):
    """
    Login user and return user info
    
    - **email**: User email
    - **password**: User password
    """
    try:
        db = get_database()
        
        # Find user
        user = db.users.find_one({"email": request.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Update last activity
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"gamification.last_activity_date": datetime.utcnow()}}
        )
        
        logger.info(f"✅ User logged in: {request.email}")
        
        return {
            "message": "Login successful",
            "user": user_to_response(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str):
    """Get current logged-in user details"""
    try:
        db = get_database()
        
        # Validate ObjectId format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_to_response(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting current user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str):
    """
    Get user by ID
    
    - **user_id**: MongoDB user ID
    """
    try:
        db = get_database()
        
        # Validate ObjectId format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_to_response(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user"
        )

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, request: UserUpdateRequest):
    """
    Update user profile
    
    - **user_id**: MongoDB user ID
    - **first_name**: New first name (optional)
    - **last_name**: New last name (optional)
    """
    try:
        db = get_database()
        
        # Validate ObjectId format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Build update data
        update_data = {}
        if request.first_name:
            update_data["first_name"] = request.first_name
        if request.last_name:
            update_data["last_name"] = request.last_name
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = db.users.find_one({"_id": ObjectId(user_id)})
        logger.info(f"✅ User updated: {user_id}")
        return user_to_response(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )

@router.post("/{user_id}/organizations", status_code=status.HTTP_200_OK)
async def add_user_to_organization(user_id: str, request: AddOrganizationRequest):
    """
    Add user to an organization
    
    - **user_id**: MongoDB user ID
    - **organization_id**: Organization to add user to
    - **role**: User's role in the organization
    """
    try:
        db = get_database()
        
        # Validate user ID format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Validate organization ID format
        if not ObjectId.is_valid(request.organization_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID format"
            )
        
        # Verify user exists
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify organization exists
        org = db.organizations.find_one({"_id": ObjectId(request.organization_id)})
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Check if user is already in organization
        existing = next(
            (o for o in user.get("organizations", [])
             if o.get("organization_id") == request.organization_id),
            None
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already in this organization"
            )
        
        # Add to user's organizations
        membership = {
            "organization_id": request.organization_id,
            "organization_name": org.get("name", ""),
            "role": request.role,
            "joined_at": datetime.utcnow()
        }
        
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"organizations": membership}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get updated user
        updated_user = db.users.find_one({"_id": ObjectId(user_id)})
        logger.info(f"✅ User {user_id} added to organization {request.organization_id}")
        
        return {
            "message": "User added to organization successfully",
            "user": user_to_response(updated_user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding user to organization: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding user to organization"
        )

@router.get("/{user_id}/gamification")
async def get_user_gamification(user_id: str):
    """Get user's gamification stats"""
    try:
        db = get_database()
        
        # Validate ObjectId format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        user = db.users.find_one(
            {"_id": ObjectId(user_id)},
            {"gamification": 1}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get achievements
        achievements = list(db.user_achievements.find(
            {"user_id": user_id}
        ).sort("earned_at", -1))
        
        for achievement in achievements:
            achievement["achievement_id"] = str(achievement.pop("_id"))
        
        return {
            "gamification": user.get("gamification", {}),
            "achievements": achievements,
            "total_achievements": len(achievements)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting gamification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving gamification stats"
        )

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: str):
    """
    Delete/deactivate user
    
    - **user_id**: MongoDB user ID
    """
    try:
        db = get_database()
        
        # Validate ObjectId format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"✅ User deactivated: {user_id}")
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating user"
        )