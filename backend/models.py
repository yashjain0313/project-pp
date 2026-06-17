"""
CareSync Database Models
All SQLAlchemy ORM models for the healthcare platform
"""
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text,
    Boolean, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from database import Base


# ─── Enums ──────────────────────────────────────────────

class UserRole(str, enum.Enum):
    PROVIDER = "provider"
    ADMIN = "admin"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class GapType(str, enum.Enum):
    SCREENING = "screening"
    VACCINATION = "vaccination"
    CHECKUP = "checkup"
    LAB = "lab"


class GapStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    OVERDUE = "overdue"


class GapPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConditionStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"


class CarePlanStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# ─── Models ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.PROVIDER)
    specialty = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patients = relationship("Patient", back_populates="primary_provider", foreign_keys="Patient.pcp_id")
    care_plans_created = relationship("CarePlan", back_populates="created_by_user")
    encounters = relationship("Encounter", back_populates="provider")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    insurance_id = Column(String(50), nullable=True)
    pcp_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    primary_provider = relationship("User", back_populates="patients", foreign_keys=[pcp_id])
    conditions = relationship("Condition", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    care_gaps = relationship("CareGap", back_populates="patient", cascade="all, delete-orphan")
    care_plans = relationship("CarePlan", back_populates="patient", cascade="all, delete-orphan")
    encounters = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    icd_code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    diagnosed_date = Column(Date, nullable=True)
    status = Column(SQLEnum(ConditionStatus), default=ConditionStatus.ACTIVE)
    is_chronic = Column(Boolean, default=False)

    # Relationships
    patient = relationship("Patient", back_populates="conditions")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    prescriber_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    patient = relationship("Patient", back_populates="medications")


class CareGap(Base):
    __tablename__ = "care_gaps"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    gap_type = Column(SQLEnum(GapType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(SQLEnum(GapStatus), default=GapStatus.OPEN)
    priority = Column(SQLEnum(GapPriority), default=GapPriority.MEDIUM)
    closed_date = Column(Date, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="care_gaps")


class CarePlan(Base):
    __tablename__ = "care_plans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    status = Column(SQLEnum(CarePlanStatus), default=CarePlanStatus.ACTIVE)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="care_plans")
    created_by_user = relationship("User", back_populates="care_plans_created")


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    encounter_type = Column(String(100), nullable=False)
    encounter_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    vitals_bp_systolic = Column(Integer, nullable=True)
    vitals_bp_diastolic = Column(Integer, nullable=True)
    vitals_heart_rate = Column(Integer, nullable=True)
    vitals_temperature = Column(Float, nullable=True)
    vitals_weight = Column(Float, nullable=True)
    vitals_height = Column(Float, nullable=True)
    vitals_bmi = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="encounters")
    provider = relationship("User", back_populates="encounters")
