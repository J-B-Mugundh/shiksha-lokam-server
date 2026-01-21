# LFA Builder - Complete API Specification for FastAPI Implementation

## Overview
- **Framework**: FastAPI (Python 3.11+)
- **Base URL**: `https://api.lfabuilder.org/v1`
- **Authentication**: JWT Bearer Token (access + refresh tokens)
- **Database**: MongoDB
- **Format**: JSON (application/json)
- **Total Endpoints**: ~170

---

## Project Structure (FastAPI)

```
app/
├── main.py                    # FastAPI app initialization
├── config.py                  # Settings & environment variables
├── database.py                # MongoDB connection
│
├── models/                    # Pydantic models (request/response schemas)
│   ├── __init__.py
│   ├── auth.py
│   ├── user.py
│   ├── organization.py
│   ├── lfa.py
│   ├── master_data.py
│   ├── execution.py           # 🎮 Gamification
│   ├── gamification.py        # 🎮 Gamification
│   ├── review.py
│   ├── template.py
│   ├── notification.py
│   └── common.py              # Shared models (pagination, errors)
│
├── routers/                   # API route handlers
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   ├── organizations.py
│   ├── lfas.py
│   ├── master_data.py
│   ├── executions.py          # 🎮 Gamification
│   ├── actions.py             # 🎮 Gamification
│   ├── corrective_actions.py  # 🎮 Gamification
│   ├── xp.py                  # 🎮 Gamification
│   ├── achievements.py        # 🎮 Gamification
│   ├── streaks.py             # 🎮 Gamification
│   ├── reviews.py
│   ├── templates.py
│   ├── exports.py
│   ├── ai.py
│   ├── notifications.py
│   └── admin.py
│
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── auth_service.py
│   ├── lfa_service.py
│   ├── execution_service.py   # 🎮 Gamification
│   ├── xp_service.py          # 🎮 Gamification
│   ├── achievement_service.py # 🎮 Gamification
│   ├── corrective_service.py  # 🎮 Gamification
│   ├── ai_service.py
│   └── export_service.py
│
├── repositories/              # Database operations
│   ├── __init__.py
│   ├── base.py
│   ├── user_repo.py
│   ├── lfa_repo.py
│   ├── execution_repo.py      # 🎮 Gamification
│   └── ...
│
├── core/                      # Core utilities
│   ├── __init__.py
│   ├── security.py            # JWT, password hashing
│   ├── dependencies.py        # FastAPI dependencies
│   ├── exceptions.py          # Custom exceptions
│   └── middleware.py          # CORS, logging, etc.
│
└── utils/                     # Helper functions
    ├── __init__.py
    ├── validators.py
    └── helpers.py
```

---

## Common Models (Pydantic)

### Pagination
```python
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Literal["asc", "desc"] = "desc"

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
```

### Error Responses
```python
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

# Standard HTTP Status Codes:
# 200 - Success
# 201 - Created
# 204 - No Content (for DELETE)
# 400 - Bad Request (validation error)
# 401 - Unauthorized (no/invalid token)
# 403 - Forbidden (insufficient permissions)
# 404 - Not Found
# 409 - Conflict (duplicate, state conflict)
# 422 - Unprocessable Entity (business logic error)
# 500 - Internal Server Error
```

### Authentication Dependency
```python
# core/dependencies.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Validates JWT and returns current user"""
    
async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Ensures user is active"""

async def require_roles(allowed_roles: List[str]):
    """Role-based access control dependency"""
    
async def require_lfa_access(lfa_id: str, min_role: str = "viewer"):
    """Check user has access to specific LFA"""

async def require_org_membership(org_id: str, min_role: str = "member"):
    """Check user is member of organization"""
```

---

## 1. AUTHENTICATION & USERS

### Router: `/auth`

#### POST `/auth/register`
```python
# Request
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: Optional[str] = Field(max_length=100)
    
# Response (201)
class AuthResponse(BaseModel):
    success: bool = True
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse

# Collections: users, user_sessions
# Business Logic:
# - Check email uniqueness
# - Hash password with bcrypt
# - Create user with platform_role="user"
# - Generate JWT tokens
# - Send verification email (async)
```

#### POST `/auth/login`
```python
# Request
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Response (200): AuthResponse
# Errors: 401 (invalid credentials), 403 (account disabled)
# Business Logic:
# - Verify credentials
# - Update last_login_at
# - Create session in user_sessions
# - Return tokens
```

#### POST `/auth/google`
```python
# Request
class GoogleAuthRequest(BaseModel):
    id_token: str  # Google OAuth ID token

# Response (200): AuthResponse
# Business Logic:
# - Verify Google token
# - Find or create user by google_id
# - Link accounts if email exists
```

#### GET `/auth/me`
```python
# Auth: Required
# Response (200): UserResponse
class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    platform_role: str
    organizations: List[UserOrgMembership]
    gamification: GamificationSummary
    preferences: UserPreferences
    onboarding_completed: bool
    created_at: datetime
```

#### PUT `/auth/me`
```python
# Auth: Required
# Request
class UpdateProfileRequest(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    phone: Optional[str]
    job_title: Optional[str]
    avatar_url: Optional[str]
    preferences: Optional[UserPreferences]

# Response (200): UserResponse
```

---

## 2. ORGANIZATIONS

### Router: `/organizations`

#### POST `/organizations`
```python
# Auth: Required
# Request
class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: Literal["ngo", "cso", "foundation", "government", "social_enterprise", "other"] = "ngo"
    description: Optional[str]
    website: Optional[HttpUrl]
    geography: Optional[GeographyModel]
    focus_areas: Optional[List[str]]

# Response (201)
class OrganizationResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str]
    members: List[OrgMemberResponse]
    stats: OrgStats
    created_at: datetime

# Business Logic:
# - Create org with creator as "owner"
# - Add to user's organizations array
# - Initialize stats
```

#### GET `/organizations`
```python
# Auth: Required
# Query: PaginationParams
# Response (200): PaginatedResponse[OrganizationResponse]
# Returns only orgs where user is a member
```

#### POST `/organizations/{org_id}/members`
```python
# Auth: Required (org admin/owner)
# Request
class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: Literal["admin", "member"] = "member"

# Response (201)
class OrgMemberResponse(BaseModel):
    user_id: Optional[str]  # null if not yet registered
    email: str
    display_name: Optional[str]
    role: str
    invited_at: datetime
    accepted_at: Optional[datetime]
    is_active: bool

# Business Logic:
# - Check inviter has permission
# - If user exists, add to org and notify
# - If user doesn't exist, create pending invitation
# - Send invitation email
```

---

## 3. MASTER DATA

### Router: `/master-data`

#### GET `/themes`
```python
# Auth: Required
# Query: active_only: bool = True
# Response (200)
class ThemeListResponse(BaseModel):
    themes: List[ThemeResponse]

class ThemeResponse(BaseModel):
    id: str
    name: str
    short_name: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    impact_ids: List[str]
    challenge_statements: List[ChallengeStatementResponse]
    display_order: int
```

#### GET `/themes/{theme_id}/impacts`
```python
# Auth: Required
# Response (200)
class ImpactListResponse(BaseModel):
    impacts: List[ImpactResponse]

class ImpactResponse(BaseModel):
    id: str
    text: str
    description: Optional[str]
    category: Optional[str]
    indicators: List[IndicatorResponse]
    display_order: int

class IndicatorResponse(BaseModel):
    id: str
    text: str
    indicator_type: Literal["percentage", "count", "ratio", "score", "boolean"]
    measurement_guidance: Optional[str]
    suggested_frequency: Optional[str]
    suggested_tool: Optional[str]
```

#### GET `/stakeholders`
```python
# Auth: Required
# Query: level: Optional[Literal["school", "cluster", "block", "district"]]
# Response (200)
class StakeholderListResponse(BaseModel):
    stakeholders: List[StakeholderResponse]

class StakeholderResponse(BaseModel):
    id: str
    name: str
    short_name: Optional[str]
    display_name: Optional[str]
    level: str
    category: str
    outcomes: List[OutcomeResponse]
    display_order: int
```

---

## 4. LFA MANAGEMENT

### Router: `/lfas`

#### POST `/lfas`
```python
# Auth: Required
# Request
class CreateLFARequest(BaseModel):
    organization_id: str
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str]
    # Optional: start from template
    template_id: Optional[str]

# Response (201)
class LFAResponse(BaseModel):
    id: str
    organization_id: str
    organization_name: str
    created_by: str
    created_by_name: str
    name: str
    description: Optional[str]
    status: LFAStatus
    theme: Optional[LFATheme]
    challenge: Optional[LFAChallenge]
    impacts: List[LFAImpact]
    stakeholders: List[LFAStakeholder]
    level_progress: List[LevelProgress]
    collaborators: List[CollaboratorResponse]
    xp_earned: int
    version: int
    created_at: datetime
    updated_at: datetime

# Business Logic:
# - Verify user is member of organization
# - If template_id provided, copy template content
# - Initialize level_progress for 5 levels
# - Add creator as owner collaborator
# - Award XP for starting LFA
```

#### GET `/lfas`
```python
# Auth: Required
# Query
class LFAFilterParams(BaseModel):
    organization_id: Optional[str]
    status: Optional[List[LFAStatus]]
    theme_id: Optional[str]
    search: Optional[str]  # searches name, description
    # + PaginationParams

# Response (200): PaginatedResponse[LFASummaryResponse]
class LFASummaryResponse(BaseModel):
    id: str
    name: str
    organization_name: str
    status: LFAStatus
    theme_name: Optional[str]
    completion_percentage: int  # calculated from level_progress
    xp_earned: int
    updated_at: datetime
```

#### PUT `/lfas/{lfa_id}`
```python
# Auth: Required (editor+ role on LFA)
# Request: Partial update, auto-save compatible
class UpdateLFARequest(BaseModel):
    name: Optional[str]
    description: Optional[str]
    target_grades: Optional[List[str]]
    duration: Optional[DurationModel]
    timeline: Optional[TimelineModel]
    budget_range: Optional[str]

# Response (200): LFAResponse
# Business Logic:
# - Check LFA is not locked
# - Update version number
# - Create version snapshot if significant change
```

#### PUT `/lfas/{lfa_id}/theme`
```python
# Auth: Required (editor+)
# Request
class UpdateThemeRequest(BaseModel):
    theme_id: Optional[str]  # null for custom
    is_custom: bool = False
    custom_theme_name: Optional[str]  # required if is_custom=True

# Response (200): LFAResponse
# Business Logic:
# - Validate theme exists (if theme_id provided)
# - Clear impacts if theme changes (confirm with user)
# - Update level_progress for level 2
```

#### PUT `/lfas/{lfa_id}/impacts`
```python
# Auth: Required (editor+)
# Request
class UpdateImpactsRequest(BaseModel):
    impacts: List[LFAImpactInput]

class LFAImpactInput(BaseModel):
    source_impact_id: Optional[str]  # null for custom
    is_custom: bool = False
    text: str
    category_name: Optional[str]
    display_order: int
    indicators: List[LFAIndicatorInput]

class LFAIndicatorInput(BaseModel):
    source_indicator_id: Optional[str]
    is_custom: bool = False
    text: str
    indicator_type: str
    baseline: Optional[BaselineTarget]
    target: Optional[BaselineTarget]
    measurement_frequency: Optional[str]
    measurement_tool: Optional[str]

class BaselineTarget(BaseModel):
    value: Optional[float]
    date: Optional[date]

# Response (200): LFAResponse
# Business Logic:
# - Validate source_impact_id exists in master data
# - Check baseline/target validity
# - Update level_progress for level 3
# - Award XP for adding impacts
```

#### PUT `/lfas/{lfa_id}/stakeholders`
```python
# Auth: Required (editor+)
# Request
class UpdateStakeholdersRequest(BaseModel):
    stakeholders: List[LFAStakeholderInput]

class LFAStakeholderInput(BaseModel):
    source_stakeholder_id: str
    target_count: Optional[int]
    notes: Optional[str]
    display_order: int
    outcomes: List[LFAOutcomeInput]

# Response (200): LFAResponse
# Business Logic:
# - Validate stakeholder exists
# - Ensure outcomes belong to selected stakeholder
# - Update level_progress for level 4
```

#### POST `/lfas/{lfa_id}/submit-for-review`
```python
# Auth: Required (owner/editor)
# Request
class SubmitForReviewRequest(BaseModel):
    reviewer_notes: Optional[str]

# Response (200)
class SubmitResponse(BaseModel):
    success: bool
    lfa_id: str
    new_status: str
    submitted_at: datetime

# Business Logic:
# - Validate LFA is complete (all levels at 100%)
# - Validate quality score >= minimum threshold
# - Change status to "submitted_for_review"
# - Create version snapshot
# - Notify reviewers
# - Award XP for submission
```

#### POST `/lfas/{lfa_id}/lock`
```python
# Auth: Required (system/reviewer after approval)
# Response (200)
# Business Logic:
# - Verify status is "approved"
# - Change status to "locked"
# - Set locked_at timestamp
# - LFA becomes immutable
# - Enable execution creation
```

---

## 🎮 5. EXECUTION ENGINE (Gamification)

### Router: `/executions`
### Collections: `executions`, `execution_levels`, `execution_actions`

#### POST `/executions`
```python
# Auth: Required
# Request
class CreateExecutionRequest(BaseModel):
    lfa_id: str

# Response (201)
class ExecutionResponse(BaseModel):
    id: str
    lfa_id: str
    lfa_name: str
    organization_id: str
    organization_name: str
    status: Literal["active", "paused", "completed", "abandoned"]
    current_level_number: int
    overall_completion_percentage: int
    total_xp_earned: int
    stats: ExecutionStats
    started_at: datetime
    created_at: datetime

class ExecutionStats(BaseModel):
    total_levels: int
    completed_levels: int
    total_actions: int
    completed_actions: int
    actions_with_corrections: int
    escalated_actions: int
    average_achievement_percentage: float
    on_time_completion_rate: float

# Business Logic:
# 1. Verify LFA status is "locked"
# 2. Check no existing execution for this LFA
# 3. Call AI service to generate levels from LFA
# 4. Create execution_levels (typically 4-6 levels)
# 5. Create execution_actions for each level
# 6. Set first level to "in_progress", others "locked"
# 7. Update LFA status to "in_execution"
# 8. Award XP for starting execution
```

#### GET `/executions`
```python
# Auth: Required
# Query
class ExecutionFilterParams(BaseModel):
    organization_id: Optional[str]
    status: Optional[List[str]]
    # + PaginationParams

# Response (200): PaginatedResponse[ExecutionSummaryResponse]
```

#### GET `/executions/{execution_id}`
```python
# Auth: Required (must have access to LFA)
# Response (200): ExecutionResponse (full details)
```

#### GET `/executions/{execution_id}/levels`
```python
# Auth: Required
# Response (200)
class LevelListResponse(BaseModel):
    levels: List[ExecutionLevelResponse]

class ExecutionLevelResponse(BaseModel):
    id: str
    execution_id: str
    level_number: int
    name: str  # e.g., "Foundation", "Launch"
    description: str
    status: Literal["locked", "in_progress", "completed"]
    timeline: LevelTimeline
    progress: LevelProgress
    gamification: LevelGamification
    mapped_impact_ids: List[str]
    mapped_outcome_ids: List[str]

class LevelTimeline(BaseModel):
    expected_start_date: date
    expected_end_date: date
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]

class LevelProgress(BaseModel):
    total_actions: int
    completed_actions: int
    completion_percentage: int

class LevelGamification(BaseModel):
    base_xp: int
    completion_bonus_xp: int
    xp_earned: int
```

#### GET `/executions/{execution_id}/current-action`
```python
# Auth: Required
# Response (200)
class CurrentActionResponse(BaseModel):
    level: ExecutionLevelSummary
    action: ExecutionActionResponse
    previous_action_summary: Optional[ActionSummary]  # for context

class ExecutionActionResponse(BaseModel):
    id: str
    execution_id: str
    execution_level_id: str
    level_number: int
    sequence_number: int
    description: str
    detailed_steps: List[ActionStep]
    timeline: ActionTimeline
    success_criteria: SuccessCriteria
    status: ActionStatus
    gamification: ActionGamification
    corrective: CorrectiveTracking
    predecessor_action_id: Optional[str]
    created_at: datetime

class ActionStep(BaseModel):
    step_number: int
    description: str

class ActionTimeline(BaseModel):
    deadline: date
    estimated_duration_days: int
    actual_start_date: Optional[date]
    actual_completion_date: Optional[date]
    days_remaining: int  # calculated
    is_overdue: bool  # calculated

class SuccessCriteria(BaseModel):
    indicator: str
    indicator_id: Optional[str]
    indicator_type: Literal["impact", "outcome"]
    measurement_method: str
    baseline: float
    target: float
    minimum_acceptable: float  # 80% of improvement
    data_source: Optional[str]
    sample_size: Optional[int]

class ActionGamification(BaseModel):
    base_xp: int = 1000
    xp_earned: Optional[int]
    potential_xp: int  # calculated based on current status

class CorrectiveTracking(BaseModel):
    attempts_used: int
    max_attempts: int = 2
    can_have_more_corrective: bool  # calculated

# Business Logic:
# - Find first action where status is not "completed"
# - If all completed, return level completion status
# - Calculate days_remaining, is_overdue
# - Include context about previous action if exists
```

#### POST `/executions/{execution_id}/actions/{action_id}/start`
```python
# Auth: Required
# Response (200): ExecutionActionResponse
# Business Logic:
# - Verify action status is "locked" or can be started
# - Verify predecessor action is completed (if exists)
# - Update status to "in_progress"
# - Set actual_start_date
```

---

## 🎮 6. ACTION RESULTS & VALIDATION (Gamification)

### Router: `/executions/{execution_id}/actions/{action_id}`

#### POST `/executions/{execution_id}/actions/{action_id}/results`
```python
# Auth: Required
# Request
class SubmitResultsRequest(BaseModel):
    indicator: str
    values: ResultValues
    measurement: MeasurementDetails
    evidence_urls: Optional[List[str]]
    notes: Optional[str]

class ResultValues(BaseModel):
    baseline: float
    current: float
    target: float

class MeasurementDetails(BaseModel):
    method: str
    sample_size: Optional[int]
    data_source: Optional[str]
    collection_date: date

# Response (201)
class ResultResponse(BaseModel):
    id: str
    execution_action_id: str
    indicator: str
    values: ResultValues
    calculated: CalculatedResults
    evaluation: EvaluationResult
    submitted_by: str
    submitted_at: datetime

class CalculatedResults(BaseModel):
    improvement: float           # current - baseline
    target_improvement: float    # target - baseline
    achievement_percentage: float  # (improvement / target_improvement) * 100

class EvaluationResult(BaseModel):
    result: Literal["excellent", "satisfactory", "below_target", "unsatisfactory"]
    message: str
    next_action: Literal["UNLOCK", "CORRECTIVE_REQUIRED", "CORRECTIVE_MANDATORY"]

# Business Logic (CRITICAL - from Srinath's architecture):
# 1. Validate indicator matches action's success_criteria
# 2. Validate baseline matches original
# 3. Calculate achievement_percentage:
#    improvement = current - baseline
#    target_improvement = target - baseline
#    achievement_percentage = (improvement / target_improvement) * 100
#
# 4. Evaluate outcome:
#    IF achievement_percentage >= 100:
#        result = "EXCELLENT", next_action = "UNLOCK"
#    ELSE IF achievement_percentage >= 80:
#        result = "SATISFACTORY", next_action = "UNLOCK"
#    ELSE IF achievement_percentage >= 50:
#        result = "BELOW_TARGET", next_action = "CORRECTIVE_REQUIRED"
#    ELSE:
#        result = "UNSATISFACTORY", next_action = "CORRECTIVE_MANDATORY"
#
# 5. Store result in action_results collection
# 6. Update action status based on evaluation
# 7. If corrective required, trigger corrective action generation
```

#### POST `/executions/{execution_id}/actions/{action_id}/complete`
```python
# Auth: Required
# Response (200)
class ActionCompletionResponse(BaseModel):
    action_id: str
    status: str
    evaluation: EvaluationResult
    xp_earned: int
    xp_breakdown: XPBreakdown
    next_action: Optional[NextActionInfo]
    level_completed: bool
    level_completion_bonus: Optional[int]
    achievements_unlocked: List[AchievementResponse]

class XPBreakdown(BaseModel):
    base_amount: int
    quality_multiplier: float
    time_bonus: int
    time_penalty: int
    corrective_penalty: int
    final_xp: int

class NextActionInfo(BaseModel):
    action_id: str
    description: str
    deadline: date

# Business Logic (XP Calculation from Srinath's architecture):
# 1. Get latest result for action
# 2. Calculate XP:
#    base_xp = action.gamification.base_xp (default 1000)
#    
#    # Quality multiplier based on achievement
#    IF achievement >= 100%: quality_multiplier = 1.2
#    ELSE IF achievement >= 90%: quality_multiplier = 1.1
#    ELSE IF achievement >= 80%: quality_multiplier = 1.0
#    ELSE IF achievement >= 50%: quality_multiplier = 0.8
#    ELSE: quality_multiplier = 0.5
#    
#    # Time bonus/penalty
#    days_early = deadline - completion_date
#    IF days_early > 0: time_bonus = MIN(days_early * 20, 500)
#    ELSE IF days_early < 0: time_penalty = ABS(days_early) * 30
#    
#    # Corrective penalty
#    corrective_penalty = corrective_attempts_used * 200
#    
#    # Final calculation
#    final_xp = MAX(
#        (base_xp * quality_multiplier) + time_bonus - time_penalty - corrective_penalty,
#        base_xp * 0.3  # Minimum 30%
#    )
#
# 3. Update action status to "completed"
# 4. Create xp_transaction
# 5. Update user's total XP
# 6. Check for level completion
# 7. Check for achievements
# 8. Unlock next action (if exists)
# 9. Return comprehensive response
```

---

## 🎮 7. CORRECTIVE ACTIONS (Gamification)

### Router: `/executions/{execution_id}/actions/{action_id}/corrective`
### Collection: `corrective_actions`

#### GET `/executions/{execution_id}/actions/{action_id}/corrective`
```python
# Auth: Required
# Response (200)
class CorrectiveActionResponse(BaseModel):
    id: str
    parent_action_id: str
    triggering_result_id: str
    attempt_number: int
    description: str
    rationale: str  # AI-generated root cause
    specific_steps: List[ActionStep]
    timeline: CorrectiveTimeline
    success_criteria: SuccessCriteria  # Same as parent
    status: Literal["pending", "accepted", "in_progress", "completed", "failed"]
    gamification: CorrectiveGamification
    ai_diagnosis: AIDiagnosis
    user_customized: bool
    created_at: datetime

class CorrectiveTimeline(BaseModel):
    deadline: date
    estimated_duration_days: int
    actual_completion_date: Optional[date]

class CorrectiveGamification(BaseModel):
    base_xp: int  # 50% of parent action
    xp_earned: Optional[int]

class AIDiagnosis(BaseModel):
    root_cause: str
    contributing_factors: List[str]
    confidence: float

# Business Logic:
# - Called after result submission with achievement < 80%
# - AI analyzes gap and generates corrective action
# - Corrective has same target as parent action
# - Max 2 corrective attempts per action
```

#### POST `/executions/{execution_id}/actions/{action_id}/corrective/accept`
```python
# Auth: Required
# Response (200): CorrectiveActionResponse (status changed to "accepted")
# Business Logic:
# - Update corrective status to "accepted"
# - Update parent action status to "corrective_required"
# - Set accepted_at timestamp
```

#### PUT `/executions/{execution_id}/actions/{action_id}/corrective/customize`
```python
# Auth: Required
# Request
class CustomizeCorrectiveRequest(BaseModel):
    description: Optional[str]
    specific_steps: Optional[List[ActionStep]]
    # Cannot change: deadline, success_criteria, target

# Response (200): CorrectiveActionResponse
# Business Logic:
# - Store original_description before change
# - Set user_customized = true
# - Must keep same target and success criteria
```

#### POST `/executions/{execution_id}/actions/{action_id}/corrective/results`
```python
# Auth: Required
# Request: SubmitResultsRequest (same as action results)
# Response (201): ResultResponse
# Business Logic:
# - Same evaluation logic as action results
# - Sets is_corrective_result = true
# - Links to corrective_action_id
```

#### POST `/executions/{execution_id}/actions/{action_id}/corrective/complete`
```python
# Auth: Required
# Response (200)
class CorrectiveCompletionResponse(BaseModel):
    corrective_action_id: str
    status: str
    evaluation: EvaluationResult
    xp_earned: int  # Reduced (50% of what would have been earned)
    parent_action_resolved: bool
    next_step: Literal["action_completed", "another_corrective", "escalation"]

# Business Logic:
# 1. Evaluate corrective results
# 2. IF target met:
#    - Mark corrective as "completed"
#    - Mark parent action as "completed"
#    - Award XP (base * 0.8 for needing correction)
#    - Unlock next action
# 3. ELSE IF corrective_attempts < max_attempts:
#    - Generate another corrective action
#    - Return next_step = "another_corrective"
# 4. ELSE:
#    - Mark as "escalation"
#    - Flag for review
#    - Allow progression with reduced XP (50%)
#    - Unlock next action
```

#### POST `/executions/{execution_id}/actions/{action_id}/escalate`
```python
# Auth: Required
# Request
class EscalateRequest(BaseModel):
    reason: str
    notes: Optional[str]

# Response (200)
# Business Logic:
# - Mark action as "escalated"
# - Create notification for reviewers
# - Allow progression with 50% XP penalty
# - Log escalation in audit
```

---

## 🎮 8. XP & POINTS SYSTEM (Gamification)

### Router: `/xp`
### Collections: `xp_transactions`, `users` (gamification field)

#### GET `/users/{user_id}/xp`
```python
# Auth: Required (self or admin)
# Response (200)
class UserXPResponse(BaseModel):
    user_id: str
    total_xp: int
    level: int
    xp_to_next_level: int
    level_progress_percentage: int
    rank: Optional[int]  # global rank

# Level calculation:
# Level 1: 0-999 XP
# Level 2: 1000-2499 XP
# Level 3: 2500-4999 XP
# Level 4: 5000-9999 XP
# Level 5: 10000+ XP (and so on, exponential)
```

#### GET `/users/{user_id}/xp/transactions`
```python
# Auth: Required (self or admin)
# Query
class XPTransactionFilterParams(BaseModel):
    lfa_id: Optional[str]
    execution_id: Optional[str]
    date_from: Optional[date]
    date_to: Optional[date]
    # + PaginationParams

# Response (200): PaginatedResponse[XPTransactionResponse]
class XPTransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: int
    breakdown: XPBreakdown
    reason: str
    context: XPContext
    created_at: datetime

class XPContext(BaseModel):
    lfa_id: Optional[str]
    lfa_name: Optional[str]
    execution_id: Optional[str]
    execution_action_id: Optional[str]
    achievement_id: Optional[str]
```

#### GET `/users/{user_id}/xp/breakdown`
```python
# Auth: Required
# Response (200)
class XPBreakdownResponse(BaseModel):
    total_xp: int
    by_source: Dict[str, int]  # {"lfa_creation": 5000, "execution": 12000, "achievements": 3000}
    by_lfa: List[LFAXPSummary]
    by_month: List[MonthlyXP]
```

#### GET `/leaderboard`
```python
# Auth: Required
# Query
class LeaderboardParams(BaseModel):
    scope: Literal["global", "organization", "weekly", "monthly"] = "global"
    organization_id: Optional[str]  # required if scope=organization
    limit: int = Field(default=10, le=100)

# Response (200)
class LeaderboardResponse(BaseModel):
    scope: str
    period: Optional[str]  # e.g., "2025-01-13 to 2025-01-19" for weekly
    entries: List[LeaderboardEntry]
    current_user_rank: Optional[int]
    current_user_entry: Optional[LeaderboardEntry]

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    display_name: str
    avatar_url: Optional[str]
    organization_name: Optional[str]
    total_xp: int
    level: int
    lfas_completed: int
    actions_completed: int
```

---

## 🎮 9. ACHIEVEMENTS & BADGES (Gamification)

### Router: `/achievements`
### Collections: `achievements`, `user_achievements`

#### GET `/achievements`
```python
# Auth: Required
# Response (200)
class AchievementListResponse(BaseModel):
    achievements: List[AchievementResponse]
    categories: List[str]

class AchievementResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    icon: Optional[str]
    badge_image_url: Optional[str]
    color: Optional[str]
    type: Literal["level_completion", "lfa_completion", "quality_score", "collaboration", "streak", "special"]
    criteria: Dict[str, Any]
    xp_reward: int
    is_active: bool

# Achievement Types & Criteria Examples:
# {
#   "first_steps": {"type": "lfa_completion", "criteria": {"lfas_started": 1}},
#   "impact_explorer": {"type": "lfa_completion", "criteria": {"impacts_selected": 5}},
#   "system_thinker": {"type": "lfa_completion", "criteria": {"stakeholder_levels": 4}},
#   "lfa_architect": {"type": "lfa_completion", "criteria": {"lfas_completed": 1}},
#   "speed_demon": {"type": "execution", "criteria": {"actions_completed_early": 5}},
#   "perfectionist": {"type": "execution", "criteria": {"excellent_results": 10}},
#   "resilient": {"type": "execution", "criteria": {"correctives_resolved": 3}},
#   "streak_7": {"type": "streak", "criteria": {"daily_streak": 7}},
#   "collaborator": {"type": "collaboration", "criteria": {"team_members_invited": 1}},
# }
```

#### GET `/users/{user_id}/achievements`
```python
# Auth: Required
# Response (200)
class UserAchievementsResponse(BaseModel):
    earned: List[EarnedAchievementResponse]
    in_progress: List[AchievementProgressResponse]
    total_earned: int
    total_available: int

class EarnedAchievementResponse(BaseModel):
    achievement: AchievementResponse
    earned_at: datetime
    lfa_id: Optional[str]
    execution_id: Optional[str]

class AchievementProgressResponse(BaseModel):
    achievement: AchievementResponse
    current_progress: int
    required_progress: int
    percentage: int
```

#### GET `/users/{user_id}/achievements/progress`
```python
# Auth: Required
# Response (200)
class AchievementProgressListResponse(BaseModel):
    achievements: List[AchievementProgressResponse]

# Business Logic:
# - Calculate progress for each unearned achievement
# - Based on user's current stats
```

#### POST `/users/{user_id}/achievements/{achievement_id}/claim`
```python
# Auth: Required (self only)
# Response (200)
class ClaimAchievementResponse(BaseModel):
    success: bool
    achievement: AchievementResponse
    xp_awarded: int
    new_total_xp: int
    new_level: Optional[int]  # if leveled up

# Business Logic:
# - Verify achievement criteria met
# - Create user_achievement record
# - Create xp_transaction for reward
# - Update user.gamification.achievement_count
# - Return results
```

---

## 🎮 10. STREAKS & PROGRESS (Gamification)

### Router: `/streaks`
### Collection: `user_streaks`

#### GET `/users/{user_id}/streaks`
```python
# Auth: Required
# Response (200)
class UserStreaksResponse(BaseModel):
    streaks: List[StreakResponse]

class StreakResponse(BaseModel):
    streak_type: str  # "daily_login", "weekly_progress", "action_completion"
    current_count: int
    longest_count: int
    last_activity_at: Optional[datetime]
    streak_started_at: Optional[datetime]
    is_active: bool  # has activity today/this period
    will_break_at: datetime  # when streak will break if no activity
```

#### POST `/users/{user_id}/streaks/{streak_type}/check-in`
```python
# Auth: Required (self only)
# Response (200)
class StreakCheckInResponse(BaseModel):
    streak_type: str
    previous_count: int
    new_count: int
    streak_maintained: bool
    streak_broken: bool  # if gap was too long
    xp_bonus: Optional[int]  # bonus for milestone streaks (7, 30, etc.)

# Business Logic:
# - Check last_activity_at
# - If within allowed gap, increment count
# - If gap too long, reset to 1
# - Award XP bonuses at milestones
# - Update longest_count if exceeded
```

#### GET `/users/{user_id}/gamification-summary`
```python
# Auth: Required
# Response (200)
class GamificationSummaryResponse(BaseModel):
    xp: UserXPSummary
    level: LevelInfo
    achievements: AchievementSummary
    streaks: StreakSummary
    recent_activity: List[RecentActivityItem]
    next_milestones: List[MilestoneInfo]

class UserXPSummary(BaseModel):
    total: int
    this_week: int
    this_month: int
    rank: Optional[int]

class LevelInfo(BaseModel):
    current: int
    name: str  # "Novice", "Explorer", "Builder", "Architect", "Master"
    xp_in_level: int
    xp_to_next: int
    progress_percentage: int

class AchievementSummary(BaseModel):
    earned_count: int
    total_count: int
    recent: List[EarnedAchievementResponse]

class StreakSummary(BaseModel):
    daily_streak: int
    longest_streak: int
    is_active_today: bool
```

#### GET `/lfas/{lfa_id}/level-progress`
```python
# Auth: Required
# Response (200)
class LFALevelProgressResponse(BaseModel):
    lfa_id: str
    overall_percentage: int
    levels: List[LFALevelStatus]

class LFALevelStatus(BaseModel):
    level: int
    name: str  # "Foundation", "Student Impact", etc.
    is_started: bool
    is_completed: bool
    completion_percentage: int
    xp_earned: int
    xp_potential: int
```

---

## 11. NOTIFICATIONS

### Router: `/notifications`
### Collection: `notifications`

#### GET `/notifications`
```python
# Auth: Required
# Query: is_read: Optional[bool], type: Optional[str], + PaginationParams
# Response (200): PaginatedResponse[NotificationResponse]

class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    link: Optional[NotificationLink]
    is_read: bool
    created_at: datetime
```

---

## 12. AI SERVICES

### Router: `/ai`

#### POST `/ai/quick-start`
```python
# Auth: Required
# Request
class QuickStartRequest(BaseModel):
    description: str  # Natural language program description
    organization_id: str

# Response (201)
class QuickStartResponse(BaseModel):
    lfa_id: str
    generated_content: GeneratedLFAContent
    confidence_score: float
    suggestions: List[str]

# Business Logic:
# - Send description to Claude API
# - Parse response into LFA structure
# - Create draft LFA with generated content
# - Return for user review/edit
```

#### POST `/ai/generate-execution-levels`
```python
# Auth: System (internal)
# Request
class GenerateLevelsRequest(BaseModel):
    lfa_id: str
    lfa_content: LFAResponse

# Response (200)
class GeneratedLevelsResponse(BaseModel):
    levels: List[GeneratedLevel]

class GeneratedLevel(BaseModel):
    level_number: int
    name: str
    description: str
    timeline_months: int
    actions: List[GeneratedAction]
    mapped_impact_ids: List[str]
    mapped_outcome_ids: List[str]

# Business Logic (from Srinath's architecture):
# - Analyze LFA structure
# - Identify all activities, outputs, outcomes
# - Generate 4-6 sequential levels
# - Each level = logical milestone
# - Create specific action items per level
# - Define success criteria linking to LFA indicators
```

#### POST `/ai/generate-corrective-action`
```python
# Auth: System (internal)
# Request
class GenerateCorrectiveRequest(BaseModel):
    parent_action: ExecutionActionResponse
    result: ResultResponse
    gap_percentage: float

# Response (200)
class GeneratedCorrectiveResponse(BaseModel):
    description: str
    rationale: str
    specific_steps: List[ActionStep]
    estimated_duration_days: int
    ai_diagnosis: AIDiagnosis
    confidence: float

# Business Logic:
# - Analyze gap between current and target
# - Identify root cause
# - Generate targeted intervention
# - Must be tactical (not strategic LFA change)
# - Same target as parent action
```

---

## 13. EXPORTS

### Router: `/exports`

#### GET `/lfas/{lfa_id}/export/{format}`
```python
# Auth: Required (viewer+ on LFA)
# Path: format: Literal["pdf", "docx", "xlsx", "pptx"]
# Response: File download (application/pdf, etc.)

# Business Logic:
# - Generate document from LFA data
# - Use templates (Handlebars/Jinja2)
# - For PDF: Puppeteer/WeasyPrint
# - For DOCX: python-docx
# - For XLSX: openpyxl
# - For PPTX: python-pptx
```

---

## 14. ADMIN & ANALYTICS

### Router: `/admin`
### Auth: Required (admin/super_admin role)

#### GET `/admin/analytics/completion`
```python
# Response (200)
class CompletionAnalyticsResponse(BaseModel):
    total_lfas: int
    completed_lfas: int
    completion_rate: float
    avg_time_to_complete_days: float
    by_status: Dict[str, int]
    by_theme: Dict[str, int]
    completion_trend: List[TrendDataPoint]
```

---

## WebSocket Events (Real-time)

### Connection: `/ws`

```python
# Events for real-time collaboration and notifications

# Client -> Server
class WSMessage(BaseModel):
    type: str
    payload: Dict[str, Any]

# Types:
# - "join_lfa": {"lfa_id": str}
# - "leave_lfa": {"lfa_id": str}
# - "cursor_move": {"lfa_id": str, "section": str, "position": dict}
# - "edit_start": {"lfa_id": str, "section": str}
# - "edit_end": {"lfa_id": str, "section": str}

# Server -> Client
# - "user_joined": {"user_id": str, "display_name": str}
# - "user_left": {"user_id": str}
# - "lfa_updated": {"lfa_id": str, "section": str, "by": str}
# - "notification": NotificationResponse
# - "achievement_unlocked": AchievementResponse
# - "xp_earned": {"amount": int, "reason": str}
```

---

## Environment Variables

```python
# .env
DATABASE_URL=mongodb://localhost:27017/lfa_builder
REDIS_URL=redis://localhost:6379

JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

ANTHROPIC_API_KEY=your-claude-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=lfa-builder-files

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password
```

---

## Summary

| Category | Endpoints | Router File |
|----------|-----------|-------------|
| Auth & Users | 12 | `auth.py`, `users.py` |
| Organizations | 9 | `organizations.py` |
| Master Data | 12 | `master_data.py` |
| LFA Core | 27 | `lfas.py` |
| Collaboration | 11 | `lfas.py` (nested) |
| Reviews | 9 | `reviews.py` |
| Templates | 8 | `templates.py` |
| Exports | 8 | `exports.py` |
| AI Services | 8 | `ai.py` |
| **Execution** | **14** | **`executions.py`** 🎮 |
| **Actions & Results** | **8** | **`actions.py`** 🎮 |
| **Corrective Actions** | **7** | **`corrective_actions.py`** 🎮 |
| **XP & Points** | **9** | **`xp.py`** 🎮 |
| **Achievements** | **8** | **`achievements.py`** 🎮 |
| **Streaks** | **7** | **`streaks.py`** 🎮 |
| Notifications | 6 | `notifications.py` |
| Admin | 12 | `admin.py` |
| **TOTAL** | **~170** | |
