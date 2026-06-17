"""
CareSync Care Gaps Router
Endpoints for care gap management and analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import date

from database import get_db
from models import Patient, User, CareGap, GapStatus, GapType, GapPriority
from schemas import CareGapResponse, CareGapClose, CareGapSummary
from auth import get_current_user
from engines.care_gap_engine import analyze_patient_care_gaps, analyze_all_patients
from engines.risk_engine import update_patient_risk

router = APIRouter(prefix="/api/care-gaps", tags=["Care Gaps"])


@router.get("", response_model=List[CareGapResponse])
async def list_care_gaps(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    gap_type: Optional[str] = None,
    patient_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all care gaps with optional filters."""
    query = db.query(CareGap).options(joinedload(CareGap.patient))

    if status:
        query = query.filter(CareGap.status == status)
    if priority:
        query = query.filter(CareGap.priority == priority)
    if gap_type:
        query = query.filter(CareGap.gap_type == gap_type)
    if patient_id:
        query = query.filter(CareGap.patient_id == patient_id)

    # Order: overdue first, then open, then closed; high priority first
    gaps = query.order_by(
        CareGap.status.asc(),
        CareGap.priority.desc(),
        CareGap.due_date.asc()
    ).offset(skip).limit(limit).all()

    results = []
    for gap in gaps:
        gap_dict = CareGapResponse.model_validate(gap).model_dump()
        if gap.patient:
            gap_dict["patient_name"] = f"{gap.patient.first_name} {gap.patient.last_name}"
        results.append(gap_dict)

    return results


@router.get("/summary", response_model=CareGapSummary)
async def get_care_gap_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregate care gap statistics."""
    total = db.query(CareGap).count()
    open_count = db.query(CareGap).filter(CareGap.status == GapStatus.OPEN).count()
    closed_count = db.query(CareGap).filter(CareGap.status == GapStatus.CLOSED).count()
    overdue_count = db.query(CareGap).filter(CareGap.status == GapStatus.OVERDUE).count()

    by_type = {}
    for gap_type in GapType:
        by_type[gap_type.value] = db.query(CareGap).filter(
            CareGap.gap_type == gap_type,
            CareGap.status.in_([GapStatus.OPEN, GapStatus.OVERDUE])
        ).count()

    by_priority = {}
    for priority in GapPriority:
        by_priority[priority.value] = db.query(CareGap).filter(
            CareGap.priority == priority,
            CareGap.status.in_([GapStatus.OPEN, GapStatus.OVERDUE])
        ).count()

    return CareGapSummary(
        total=total,
        open=open_count,
        closed=closed_count,
        overdue=overdue_count,
        by_type=by_type,
        by_priority=by_priority
    )


@router.post("/analyze/{patient_id}")
async def analyze_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run care gap analysis for a specific patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    new_gaps = analyze_patient_care_gaps(patient, db)
    # Update risk score after gap analysis
    update_patient_risk(patient, db)

    return {
        "patient_id": patient_id,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "new_gaps_found": len(new_gaps),
        "gaps": [
            {
                "title": g.title,
                "type": g.gap_type.value,
                "priority": g.priority.value
            } for g in new_gaps
        ]
    }


@router.post("/analyze-all")
async def analyze_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run care gap analysis for all patients."""
    result = analyze_all_patients(db)
    return result


@router.put("/{gap_id}/close")
async def close_care_gap(
    gap_id: int,
    close_data: CareGapClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Close a care gap with optional resolution notes."""
    gap = db.query(CareGap).filter(CareGap.id == gap_id).first()
    if not gap:
        raise HTTPException(status_code=404, detail="Care gap not found")

    if gap.status == GapStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Care gap is already closed")

    gap.status = GapStatus.CLOSED
    gap.closed_date = date.today()
    gap.resolution_notes = close_data.resolution_notes

    db.commit()
    db.refresh(gap)

    # Update patient risk score
    patient = db.query(Patient).filter(Patient.id == gap.patient_id).first()
    if patient:
        update_patient_risk(patient, db)

    return {"message": "Care gap closed successfully", "gap_id": gap_id}


@router.put("/{gap_id}/reopen")
async def reopen_care_gap(
    gap_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reopen a previously closed care gap."""
    gap = db.query(CareGap).filter(CareGap.id == gap_id).first()
    if not gap:
        raise HTTPException(status_code=404, detail="Care gap not found")

    if gap.status != GapStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Care gap is not closed")

    gap.status = GapStatus.OPEN
    gap.closed_date = None
    gap.resolution_notes = None

    db.commit()

    # Update patient risk score
    patient = db.query(Patient).filter(Patient.id == gap.patient_id).first()
    if patient:
        update_patient_risk(patient, db)

    return {"message": "Care gap reopened", "gap_id": gap_id}
