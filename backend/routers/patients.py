"""
CareSync Patient Router
CRUD operations for patient management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from database import get_db
from models import Patient, User, CareGap, Condition, GapStatus, ConditionStatus, RiskLevel
from schemas import (
    PatientCreate, PatientUpdate, PatientResponse, PatientDetailResponse,
    ConditionResponse, MedicationResponse, CareGapResponse, CarePlanResponse,
    EncounterResponse
)
from auth import get_current_user
from engines.risk_engine import update_patient_risk

router = APIRouter(prefix="/api/patients", tags=["Patients"])


def _build_patient_response(patient: Patient, db: Session) -> dict:
    """Build a patient response with computed fields."""
    open_gaps = db.query(CareGap).filter(
        CareGap.patient_id == patient.id,
        CareGap.status.in_([GapStatus.OPEN, GapStatus.OVERDUE])
    ).count()

    active_conditions = db.query(Condition).filter(
        Condition.patient_id == patient.id,
        Condition.status == ConditionStatus.ACTIVE
    ).count()

    provider_name = None
    if patient.primary_provider:
        provider_name = patient.primary_provider.full_name

    return {
        "id": patient.id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "phone": patient.phone,
        "email": patient.email,
        "address": patient.address,
        "insurance_id": patient.insurance_id,
        "pcp_id": patient.pcp_id,
        "risk_score": patient.risk_score,
        "risk_level": patient.risk_level,
        "age": patient.age,
        "provider_name": provider_name,
        "open_gaps_count": open_gaps,
        "conditions_count": active_conditions,
        "created_at": patient.created_at,
    }


@router.get("", response_model=List[PatientResponse])
async def list_patients(
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    has_open_gaps: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all patients with optional filters."""
    query = db.query(Patient).options(joinedload(Patient.primary_provider))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Patient.first_name.ilike(search_term)) |
            (Patient.last_name.ilike(search_term)) |
            (Patient.insurance_id.ilike(search_term))
        )

    if risk_level:
        query = query.filter(Patient.risk_level == risk_level)

    patients = query.offset(skip).limit(limit).all()

    results = []
    for patient in patients:
        resp = _build_patient_response(patient, db)
        if has_open_gaps is not None:
            if has_open_gaps and resp["open_gaps_count"] == 0:
                continue
            if not has_open_gaps and resp["open_gaps_count"] > 0:
                continue
        results.append(resp)

    return results


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full patient details including conditions, meds, care gaps, etc."""
    patient = db.query(Patient).options(
        joinedload(Patient.primary_provider),
        joinedload(Patient.conditions),
        joinedload(Patient.medications),
        joinedload(Patient.care_gaps),
        joinedload(Patient.care_plans),
        joinedload(Patient.encounters),
    ).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    base = _build_patient_response(patient, db)

    # Build nested responses
    base["conditions"] = [
        ConditionResponse.model_validate(c) for c in patient.conditions
    ]
    base["medications"] = [
        MedicationResponse.model_validate(m) for m in patient.medications
    ]
    base["care_gaps"] = [
        CareGapResponse.model_validate(g) for g in
        sorted(patient.care_gaps, key=lambda x: (x.status != GapStatus.OVERDUE, x.status != GapStatus.OPEN, x.priority != "high"))
    ]
    base["care_plans"] = []
    for cp in patient.care_plans:
        cp_dict = CarePlanResponse.model_validate(cp).model_dump()
        if cp.created_by_user:
            cp_dict["provider_name"] = cp.created_by_user.full_name
        base["care_plans"].append(cp_dict)

    base["encounters"] = []
    for enc in sorted(patient.encounters, key=lambda x: x.encounter_date, reverse=True):
        enc_dict = EncounterResponse.model_validate(enc).model_dump()
        if enc.provider:
            enc_dict["provider_name"] = enc.provider.full_name
        base["encounters"].append(enc_dict)

    return base


@router.post("", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new patient."""
    patient = Patient(**patient_data.model_dump())
    if not patient.pcp_id:
        patient.pcp_id = current_user.id

    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Calculate initial risk
    update_patient_risk(patient, db)

    return _build_patient_response(patient, db)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a patient's information."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = patient_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)

    db.commit()
    db.refresh(patient)
    return _build_patient_response(patient, db)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a patient and all associated records."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted successfully"}


@router.post("/{patient_id}/recalculate-risk")
async def recalculate_risk(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate a patient's risk score."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    score, level = update_patient_risk(patient, db)
    return {"risk_score": score, "risk_level": level.value}
