"""
MongoDB Schemas for Shiksha Lokam - Educational Program Design Platform
Clean, minimal schema design focusing on core functionality
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

# ==================== ENUMS ====================

class PlatformRole(str, Enum):
    USER = "user"
    REVIEWER = "reviewer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class OrganizationType(str, Enum):
    NGO = "ngo"
    CSO = "cso"
    FOUNDATION = "foundation"
    GOVT = "govt"
    OTHER = "other"

class LFAStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    IN_EXECUTION = "in_execution"
    COMPLETED = "completed"

class ReviewDecision(str, Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"

class ActionStatus(str, Enum):
    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_CORRECTION = "needs_correction"

class SchoolProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

# ==================== MASTER DATA COLLECTIONS ====================

class ImpactIndicator(BaseModel):
    """Embedded in Impact"""
    indicator_text: str
    baseline_value: Optional[str] = None
    target_value: Optional[str] = None
    measurement_method: Optional[str] = None

class Impact(BaseModel):
    """Separate collection - reusable impacts"""
    impact_id: Optional[str] = Field(default=None, alias="_id")
    impact_statement: str = Field(..., description="What change we want to see")
    category: str = Field(..., description="e.g., 'Student Learning', 'Teacher Capacity'")
    indicators: List[ImpactIndicator] = Field(default=[], description="How we measure this impact")
    theme_id: Optional[str] = Field(default=None, description="FK to themes if needed")
    is_template: bool = Field(default=False, description="Is this a reusable template?")
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OutcomeIndicator(BaseModel):
    """Embedded in Outcome"""
    indicator_text: str
    baseline_value: Optional[str] = None
    target_value: Optional[str] = None
    measurement_method: Optional[str] = None

class Outcome(BaseModel):
    """Separate collection - stakeholder outcomes"""
    outcome_id: Optional[str] = Field(default=None, alias="_id")
    outcome_statement: str = Field(..., description="What the stakeholder will achieve")
    stakeholder_type: str = Field(..., description="e.g., 'Teachers', 'Students', 'Principals'")
    indicators: List[OutcomeIndicator] = Field(default=[], description="How we measure success")
    is_template: bool = Field(default=False)
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Theme(BaseModel):
    """Master data - program themes"""
    theme_id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., description="e.g., 'Foundational Literacy & Numeracy'")
    short_name: str = Field(..., description="e.g., 'FLN'")
    description: str
    challenge_statements: List[str] = Field(default=[], description="Common problems in this theme")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ==================== USER MANAGEMENT ====================

class OrganizationMembership(BaseModel):
    """Embedded in User"""
    organization_id: str
    organization_name: str
    role: str = Field(..., description="Role within this org, e.g., 'Program Manager'")
    joined_at: datetime = Field(default_factory=datetime.utcnow)

class UserGamification(BaseModel):
    """Embedded in User"""
    total_xp: int = Field(default=0)
    current_level: int = Field(default=1)
    current_streak: int = Field(default=0)
    longest_streak: int = Field(default=0)
    last_activity_date: Optional[datetime] = None

class User(BaseModel):
    """User collection"""
    user_id: Optional[str] = Field(default=None, alias="_id")
    email: str = Field(..., description="Unique email")
    first_name: str
    last_name: str
    password_hash: Optional[str] = None
    google_id: Optional[str] = None
    platform_role: PlatformRole = Field(default=PlatformRole.USER)
    organizations: List[OrganizationMembership] = Field(default=[])
    gamification: UserGamification = Field(default_factory=UserGamification)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Organization(BaseModel):
    """Organization collection"""
    org_id: Optional[str] = Field(default=None, alias="_id")
    name: str
    org_type: OrganizationType
    state: Optional[str] = None
    district: Optional[str] = None
    focus_areas: List[str] = Field(default=[], description="e.g., ['FLN', 'Career Readiness']")
    is_verified: bool = Field(default=False)
    total_lfas: int = Field(default=0, description="Denormalized count")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ==================== LFA (LOGICAL FRAMEWORK APPROACH) ====================

class LFAImpactRef(BaseModel):
    """Embedded in LFA - references Impact collection"""
    impact_id: str = Field(..., description="FK to impacts collection")
    impact_statement: str = Field(..., description="Denormalized for quick access")
    custom_indicators: List[ImpactIndicator] = Field(default=[], description="LFA-specific indicators")

class LFAOutcomeRef(BaseModel):
    """Embedded in LFA - references Outcome collection"""
    outcome_id: str = Field(..., description="FK to outcomes collection")
    outcome_statement: str = Field(..., description="Denormalized for quick access")
    stakeholder_type: str
    custom_indicators: List[OutcomeIndicator] = Field(default=[], description="LFA-specific indicators")

class LFACollaborator(BaseModel):
    """Embedded in LFA"""
    user_id: str
    user_name: str
    role: str = Field(..., description="e.g., 'Co-designer', 'Reviewer'")
    added_at: datetime = Field(default_factory=datetime.utcnow)

class LFA(BaseModel):
    """Main LFA document"""
    lfa_id: Optional[str] = Field(default=None, alias="_id")
    
    # Basic Info
    name: str = Field(..., description="LFA/Program name")
    organization_id: str = Field(..., description="FK to organizations")
    created_by: str = Field(..., description="FK to users")
    
    # Program Details
    target_grades: List[str] = Field(default=[], description="e.g., ['6', '7', '8']")
    theme_id: Optional[str] = Field(default=None, description="FK to themes, null if custom")
    challenge_statement: str = Field(..., description="Problem being solved")
    challenge_context: Optional[str] = Field(default=None, description="Additional context")
    
    # Logic Framework
    impacts: List[LFAImpactRef] = Field(default=[], description="Expected impacts (FK refs)")
    outcomes: List[LFAOutcomeRef] = Field(default=[], description="Stakeholder outcomes (FK refs)")
    
    # Status & Workflow
    status: LFAStatus = Field(default=LFAStatus.DRAFT)
    
    # Collaboration
    collaborators: List[LFACollaborator] = Field(default=[])
    
    # Versioning
    version: int = Field(default=1)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    execution_started_at: Optional[datetime] = None

class LFAVersion(BaseModel):
    """Version history for LFA"""
    version_id: Optional[str] = Field(default=None, alias="_id")
    lfa_id: str = Field(..., description="FK to lfas")
    version_number: int
    snapshot: Dict[str, Any] = Field(..., description="Full LFA snapshot as JSON")
    change_summary: str
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LFAReview(BaseModel):
    """Review/feedback on LFA"""
    review_id: Optional[str] = Field(default=None, alias="_id")
    lfa_id: str
    lfa_version: int
    reviewer_id: str
    decision: ReviewDecision
    summary_feedback: str
    detailed_feedback: List[Dict[str, str]] = Field(default=[], description="[{section, comment}]")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ==================== EXECUTION ENGINE ====================

class ExecutionMilestone(BaseModel):
    """Embedded in Execution - gamified levels"""
    milestone_number: int = Field(..., description="1, 2, 3...")
    name: str = Field(..., description="e.g., 'Foundation', 'Launch', 'Early Momentum'")
    description: str
    target_completion_percentage: int = Field(..., description="% of actions needed to complete")
    is_completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None
    xp_reward: int = Field(default=0, description="XP earned on completion")

class Execution(BaseModel):
    """Execution of an LFA - created when LFA status = IN_EXECUTION"""
    execution_id: Optional[str] = Field(default=None, alias="_id")
    lfa_id: str = Field(..., description="FK to lfas - UNIQUE")
    lfa_name: str = Field(..., description="Denormalized for quick access")
    organization_id: str
    
    # Progress Tracking
    current_milestone: int = Field(default=1)
    overall_completion_percentage: int = Field(default=0)
    total_actions: int = Field(default=0)
    completed_actions: int = Field(default=0)
    
    # Gamification
    milestones: List[ExecutionMilestone] = Field(default=[])
    total_xp_earned: int = Field(default=0)
    
    # Status
    status: str = Field(default="active", description="active|paused|completed")
    
    # Timeline
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expected_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionAction(BaseModel):
    """Actions/activities to be performed in execution"""
    action_id: Optional[str] = Field(default=None, alias="_id")
    execution_id: str = Field(..., description="FK to executions")
    lfa_id: str = Field(..., description="FK to lfas")
    
    # Action Details
    sequence_number: int = Field(..., description="Order of execution")
    description: str = Field(..., description="What needs to be done")
    detailed_steps: List[str] = Field(default=[])
    
    # Timeline
    deadline: Optional[datetime] = None
    estimated_duration_days: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Success Criteria
    success_indicator: Optional[str] = None
    baseline_value: Optional[str] = None
    target_value: Optional[str] = None
    
    # Status & Dependencies
    status: ActionStatus = Field(default=ActionStatus.LOCKED)
    prerequisite_action_id: Optional[str] = Field(default=None, description="Must complete this first")
    
    # Gamification
    base_xp: int = Field(default=10)
    earned_xp: int = Field(default=0)
    
    # Correction Tracking
    correction_attempts_used: int = Field(default=0)
    max_correction_attempts: int = Field(default=2)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ActionResult(BaseModel):
    """Results/evidence submitted for an action"""
    result_id: Optional[str] = Field(default=None, alias="_id")
    action_id: str = Field(..., description="FK to execution_actions")
    execution_id: str
    lfa_id: str
    
    # Measurement Data
    indicator: str
    baseline_value: Optional[str] = None
    current_value: str = Field(..., description="Actual achievement")
    target_value: Optional[str] = None
    
    # Calculated Metrics
    improvement_percentage: Optional[float] = None
    achievement_percentage: Optional[float] = None
    
    # Evidence
    evidence_urls: List[str] = Field(default=[], description="Photos, documents, etc.")
    measurement_method: Optional[str] = None
    sample_size: Optional[int] = None
    measurement_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Evaluation
    is_successful: Optional[bool] = None
    evaluation_message: Optional[str] = None
    
    # Submission
    submitted_by: str = Field(..., description="FK to users")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Verification
    is_verified: bool = Field(default=False)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

# ==================== SCHOOLS PROGRESS TRACKING ====================

class SchoolAction(BaseModel):
    """Embedded in SchoolProgress - tracks action completion"""
    action_id: str = Field(..., description="FK to execution_actions")
    action_description: str = Field(..., description="Denormalized")
    status: ActionStatus = Field(default=ActionStatus.LOCKED)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_submitted: bool = Field(default=False)
    result_id: Optional[str] = Field(default=None, description="FK to action_results")

class SchoolMilestone(BaseModel):
    """Embedded in SchoolProgress"""
    milestone_number: int
    milestone_name: str
    is_completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None

class SchoolProgress(BaseModel):
    """NEW: Tracks individual school's progress on an LFA execution"""
    progress_id: Optional[str] = Field(default=None, alias="_id")
    
    # School Info
    school_name: str
    school_code: Optional[str] = None
    district: str
    state: str
    
    # Execution Reference
    execution_id: str = Field(..., description="FK to executions")
    lfa_id: str = Field(..., description="FK to lfas")
    organization_id: str = Field(..., description="NGO managing this school")
    
    # Progress Tracking
    actions: List[SchoolAction] = Field(default=[], description="All actions with status")
    milestones: List[SchoolMilestone] = Field(default=[])
    overall_completion_percentage: int = Field(default=0)
    current_milestone: int = Field(default=1)
    
    # Status
    status: SchoolProgressStatus = Field(default=SchoolProgressStatus.NOT_STARTED)
    
    # Gamification (School level)
    total_xp_earned: int = Field(default=0)
    
    # Point of Contact
    primary_contact_name: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    primary_contact_email: Optional[str] = None
    
    # Timeline
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ==================== GAMIFICATION ====================

class Achievement(BaseModel):
    """Achievement definitions"""
    achievement_id: Optional[str] = Field(default=None, alias="_id")
    code: str = Field(..., description="Unique code, e.g., 'FIRST_LFA'")
    name: str
    description: str
    achievement_type: str = Field(..., description="lfa|milestone|quality|streak|special")
    xp_reward: int
    criteria: Dict[str, Any] = Field(..., description="JSON criteria for unlocking")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserAchievement(BaseModel):
    """User's earned achievements"""
    user_achievement_id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    achievement_id: str
    achievement_name: str = Field(..., description="Denormalized")
    xp_reward: int
    lfa_id: Optional[str] = None
    execution_id: Optional[str] = None
    earned_at: datetime = Field(default_factory=datetime.utcnow)

class XPTransaction(BaseModel):
    """XP transaction log"""
    transaction_id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    amount: int = Field(..., description="Can be negative for penalties")
    reason: str
    context: Dict[str, str] = Field(default={}, description="{lfa_id, execution_id, action_id}")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ==================== SYSTEM COLLECTIONS ====================

class Notification(BaseModel):
    """User notifications"""
    notification_id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    notification_type: str = Field(..., description="review|comment|achievement|milestone")
    title: str
    message: str
    link_type: Optional[str] = None
    link_id: Optional[str] = None
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLog(BaseModel):
    """Audit trail"""
    log_id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    action: str = Field(..., description="created|updated|deleted|approved")
    entity_type: str = Field(..., description="lfa|execution|action|result")
    entity_id: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== COLLECTION INDEXES ====================
"""
Recommended MongoDB Indexes:

users:
  - email (unique)
  - google_id (unique, sparse)
  - organizations.organization_id

organizations:
  - name
  - org_type

impacts:
  - theme_id
  - is_template
  - created_by

outcomes:
  - stakeholder_type
  - is_template
  - created_by

lfas:
  - organization_id
  - created_by
  - status
  - theme_id
  - created_at (desc)

executions:
  - lfa_id (unique)
  - organization_id
  - status
  - started_at (desc)

execution_actions:
  - execution_id, sequence_number
  - lfa_id
  - status
  - prerequisite_action_id

action_results:
  - action_id
  - execution_id
  - submitted_by
  - submitted_at (desc)

school_progress:
  - execution_id
  - lfa_id
  - organization_id
  - status
  - school_code
  - district, state

user_achievements:
  - user_id, earned_at (desc)
  - achievement_id

xp_transactions:
  - user_id, created_at (desc)

notifications:
  - user_id, is_read, created_at (desc)

audit_log:
  - entity_type, entity_id
  - user_id, timestamp (desc)
"""