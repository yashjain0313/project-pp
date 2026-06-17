"""
CareSync Care Plans Router
CRUD operations for patient care plans
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import date

from database import get_db
from models import Patient, User, CarePlan, CarePlanStatus
from schemas import CarePlanCreate, CarePlanUpdate, CarePlanResponse
from auth import get_current_user

router = APIRouter(prefix="/api/care-plans", tags=["Care Plans"])


@router.get("", response_model=List[CarePlanResponse])
async def list_care_plans(
    status: Optional[str] = None,
    patient_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all care plans with optional filters."""
    query = db.query(CarePlan).options(
        joinedload(CarePlan.patient),
        joinedload(CarePlan.created_by_user)
    )

    if status:
        query = query.filter(CarePlan.status == status)
    if patient_id:
        query = query.filter(CarePlan.patient_id == patient_id)

    plans = query.order_by(CarePlan.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for plan in plans:
        plan_dict = CarePlanResponse.model_validate(plan).model_dump()
        if plan.created_by_user:
            plan_dict["provider_name"] = plan.created_by_user.full_name
        results.append(plan_dict)

    return results


@router.get("/{plan_id}", response_model=CarePlanResponse)
async def get_care_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific care plan."""
    plan = db.query(CarePlan).options(
        joinedload(CarePlan.created_by_user)
    ).filter(CarePlan.id == plan_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Care plan not found")

    plan_dict = CarePlanResponse.model_validate(plan).model_dump()
    if plan.created_by_user:
        plan_dict["provider_name"] = plan.created_by_user.full_name
    return plan_dict


@router.post("", response_model=CarePlanResponse)
async def create_care_plan(
    plan_data: CarePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new care plan for a patient."""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == plan_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    plan = CarePlan(
        **plan_data.model_dump(),
        created_by=current_user.id,
        start_date=plan_data.start_date or date.today()
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    plan_dict = CarePlanResponse.model_validate(plan).model_dump()
    plan_dict["provider_name"] = current_user.full_name
    return plan_dict


@router.put("/{plan_id}", response_model=CarePlanResponse)
async def update_care_plan(
    plan_id: int,
    plan_data: CarePlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a care plan."""
    plan = db.query(CarePlan).filter(CarePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Care plan not found")

    update_data = plan_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    db.commit()
    db.refresh(plan)

    plan_dict = CarePlanResponse.model_validate(plan).model_dump()
    if plan.created_by_user:
        plan_dict["provider_name"] = plan.created_by_user.full_name
    return plan_dict


@router.delete("/{plan_id}")
async def delete_care_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a care plan."""
    plan = db.query(CarePlan).filter(CarePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Care plan not found")

    db.delete(plan)
    db.commit()
    return {"message": "Care plan deleted successfully"}
