"""
CareSync Pydantic Schemas
Request/Response models for API validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# ─── Enums ──────────────────────────────────────────────

class UserRoleEnum(str, Enum):
    PROVIDER = "provider"
    ADMIN = "admin"

class RiskLevelEnum(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class GapTypeEnum(str, Enum):
    SCREENING = "screening"
    VACCINATION = "vaccination"
    CHECKUP = "checkup"
    LAB = "lab"

class GapStatusEnum(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    OVERDUE = "overdue"

class GapPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ConditionStatusEnum(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"

class CarePlanStatusEnum(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# ─── Auth Schemas ───────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: UserRoleEnum
    specialty: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Patient Schemas ────────────────────────────────────

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: GenderEnum
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    insurance_id: Optional[str] = None
    pcp_id: Optional[int] = None

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    insurance_id: Optional[str] = None
    pcp_id: Optional[int] = None

class ConditionResponse(BaseModel):
    id: int
    patient_id: int
    icd_code: str
    name: str
    diagnosed_date: Optional[date] = None
    status: ConditionStatusEnum
    is_chronic: bool

    class Config:
        from_attributes = True

class MedicationResponse(BaseModel):
    id: int
    patient_id: int
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool

    class Config:
        from_attributes = True

class CareGapResponse(BaseModel):
    id: int
    patient_id: int
    gap_type: GapTypeEnum
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: GapStatusEnum
    priority: GapPriorityEnum
    closed_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True

class CarePlanResponse(BaseModel):
    id: int
    patient_id: int
    created_by: Optional[int] = None
    title: str
    description: Optional[str] = None
    goals: Optional[str] = None
    status: CarePlanStatusEnum
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: Optional[datetime] = None
    provider_name: Optional[str] = None

    class Config:
        from_attributes = True

class EncounterResponse(BaseModel):
    id: int
    patient_id: int
    provider_id: Optional[int] = None
    encounter_type: str
    encounter_date: datetime
    notes: Optional[str] = None
    vitals_bp_systolic: Optional[int] = None
    vitals_bp_diastolic: Optional[int] = None
    vitals_heart_rate: Optional[int] = None
    vitals_temperature: Optional[float] = None
    vitals_weight: Optional[float] = None
    vitals_height: Optional[float] = None
    vitals_bmi: Optional[float] = None
    provider_name: Optional[str] = None

    class Config:
        from_attributes = True

class PatientResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: date
    gender: GenderEnum
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    insurance_id: Optional[str] = None
    pcp_id: Optional[int] = None
    risk_score: float
    risk_level: RiskLevelEnum
    age: Optional[int] = None
    provider_name: Optional[str] = None
    open_gaps_count: Optional[int] = 0
    conditions_count: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatientDetailResponse(PatientResponse):
    conditions: List[ConditionResponse] = []
    medications: List[MedicationResponse] = []
    care_gaps: List[CareGapResponse] = []
    care_plans: List[CarePlanResponse] = []
    encounters: List[EncounterResponse] = []

    class Config:
        from_attributes = True


# ─── Care Gap Schemas ───────────────────────────────────

class CareGapClose(BaseModel):
    resolution_notes: Optional[str] = None

class CareGapSummary(BaseModel):
    total: int
    open: int
    closed: int
    overdue: int
    by_type: dict
    by_priority: dict


# ─── Care Plan Schemas ──────────────────────────────────

class CarePlanCreate(BaseModel):
    patient_id: int
    title: str
    description: Optional[str] = None
    goals: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class CarePlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[str] = None
    status: Optional[CarePlanStatusEnum] = None
    end_date: Optional[date] = None


# ─── Analytics Schemas ──────────────────────────────────

class DashboardKPIs(BaseModel):
    total_patients: int
    high_risk_patients: int
    critical_risk_patients: int
    total_open_gaps: int
    total_closed_gaps: int
    gap_closure_rate: float
    total_care_plans: int
    active_care_plans: int

class RiskDistribution(BaseModel):
    level: str
    count: int
    percentage: float

class CareGapTrend(BaseModel):
    month: str
    opened: int
    closed: int

class TopCondition(BaseModel):
    name: str
    count: int
    percentage: float

class ProviderPerformance(BaseModel):
    provider_name: str
    patient_count: int
    open_gaps: int
    closed_gaps: int
    closure_rate: float


# Forward reference update
TokenResponse.model_rebuild()
