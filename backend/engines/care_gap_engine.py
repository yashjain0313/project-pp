"""
CareSync Care Gap Detection Engine
Identifies missing preventive care based on clinical guidelines
"""
from sqlalchemy.orm import Session
from models import (
    Patient, Condition, CareGap, Encounter, Medication,
    GapType, GapStatus, GapPriority, ConditionStatus, Gender
)
from datetime import date, datetime, timedelta


# ─── Clinical Rules ─────────────────────────────────────
# Based on HEDIS/USPSTF preventive care guidelines

def _has_recent_gap(db: Session, patient_id: int, title: str) -> bool:
    """Check if patient already has an open/recent gap with this title."""
    existing = db.query(CareGap).filter(
        CareGap.patient_id == patient_id,
        CareGap.title == title,
        CareGap.status.in_([GapStatus.OPEN, GapStatus.OVERDUE])
    ).first()
    return existing is not None


def _has_recent_encounter(db: Session, patient_id: int, encounter_type: str, months: int) -> bool:
    """Check if patient has a recent encounter of given type."""
    cutoff = datetime.utcnow() - timedelta(days=months * 30)
    existing = db.query(Encounter).filter(
        Encounter.patient_id == patient_id,
        Encounter.encounter_type.ilike(f"%{encounter_type}%"),
        Encounter.encounter_date >= cutoff
    ).first()
    return existing is not None


def _has_condition(db: Session, patient_id: int, condition_name: str) -> bool:
    """Check if patient has an active condition matching the name."""
    existing = db.query(Condition).filter(
        Condition.patient_id == patient_id,
        Condition.name.ilike(f"%{condition_name}%"),
        Condition.status == ConditionStatus.ACTIVE
    ).first()
    return existing is not None


def _has_medication(db: Session, patient_id: int, med_name: str) -> bool:
    """Check if patient is on a medication matching the name."""
    existing = db.query(Medication).filter(
        Medication.patient_id == patient_id,
        Medication.name.ilike(f"%{med_name}%"),
        Medication.is_active == True
    ).first()
    return existing is not None


def _create_gap(db: Session, patient_id: int, gap_type: GapType,
                title: str, description: str, priority: GapPriority,
                due_months: int = 3) -> CareGap:
    """Create a new care gap if one doesn't already exist."""
    if _has_recent_gap(db, patient_id, title):
        return None

    gap = CareGap(
        patient_id=patient_id,
        gap_type=gap_type,
        title=title,
        description=description,
        priority=priority,
        due_date=date.today() + timedelta(days=due_months * 30),
        status=GapStatus.OPEN
    )
    db.add(gap)
    return gap


def analyze_patient_care_gaps(patient: Patient, db: Session) -> list[CareGap]:
    """
    Run all clinical rules against a patient and generate care gaps.
    Returns list of newly created care gaps.
    """
    new_gaps = []
    age = patient.age
    gender = patient.gender

    # ─── SCREENINGS ─────────────────────────────────────

    # Mammogram: Women 40+ every 1-2 years (HEDIS BCS)
    if gender == Gender.FEMALE and age >= 40:
        if not _has_recent_encounter(db, patient.id, "mammogram", 24):
            gap = _create_gap(
                db, patient.id, GapType.SCREENING,
                "Breast Cancer Screening (Mammogram)",
                f"Women aged 40+ should receive a mammogram every 1-2 years. "
                f"Patient is {age} years old with no recent mammogram on record.",
                GapPriority.HIGH if age >= 50 else GapPriority.MEDIUM,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

    # Colonoscopy: Adults 45-75 every 10 years (USPSTF)
    if 45 <= age <= 75:
        if not _has_recent_encounter(db, patient.id, "colonoscopy", 120):
            gap = _create_gap(
                db, patient.id, GapType.SCREENING,
                "Colorectal Cancer Screening",
                f"Adults aged 45-75 should be screened for colorectal cancer. "
                f"Colonoscopy recommended every 10 years or FIT test annually.",
                GapPriority.HIGH if age >= 50 else GapPriority.MEDIUM,
                due_months=6
            )
            if gap:
                new_gaps.append(gap)

    # Cervical Cancer Screening: Women 21-65 every 3 years (HEDIS CCS)
    if gender == Gender.FEMALE and 21 <= age <= 65:
        if not _has_recent_encounter(db, patient.id, "pap smear", 36):
            gap = _create_gap(
                db, patient.id, GapType.SCREENING,
                "Cervical Cancer Screening (Pap Smear)",
                f"Women aged 21-65 should receive cervical cancer screening every 3 years.",
                GapPriority.MEDIUM,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

    # Blood Pressure Screening: All adults yearly
    if age >= 18:
        if not _has_recent_encounter(db, patient.id, "blood pressure", 12):
            gap = _create_gap(
                db, patient.id, GapType.SCREENING,
                "Blood Pressure Screening",
                f"All adults should have blood pressure checked at least annually.",
                GapPriority.MEDIUM if age < 50 else GapPriority.HIGH,
                due_months=2
            )
            if gap:
                new_gaps.append(gap)

    # Lipid Panel: Adults 40+ every 5 years, or yearly if on statins
    if age >= 40:
        check_months = 12 if _has_medication(db, patient.id, "statin") else 60
        if not _has_recent_encounter(db, patient.id, "lipid panel", check_months):
            gap = _create_gap(
                db, patient.id, GapType.LAB,
                "Lipid Panel Screening",
                f"Adults 40+ should have lipid levels checked regularly. "
                f"More frequent monitoring recommended for patients on statins.",
                GapPriority.MEDIUM,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

    # ─── DIABETES-SPECIFIC (HEDIS CDC measures) ─────────

    if _has_condition(db, patient.id, "diabetes"):
        # HbA1c Test: Every 6 months
        if not _has_recent_encounter(db, patient.id, "a1c", 6):
            gap = _create_gap(
                db, patient.id, GapType.LAB,
                "HbA1c Test (Diabetes Management)",
                f"Patients with diabetes should have HbA1c tested at least every 6 months "
                f"to monitor blood sugar control.",
                GapPriority.HIGH,
                due_months=1
            )
            if gap:
                new_gaps.append(gap)

        # Diabetic Eye Exam: Annually (HEDIS EED)
        if not _has_recent_encounter(db, patient.id, "eye exam", 12):
            gap = _create_gap(
                db, patient.id, GapType.CHECKUP,
                "Diabetic Retinopathy Eye Exam",
                f"Patients with diabetes should have a dilated eye exam annually "
                f"to screen for diabetic retinopathy.",
                GapPriority.HIGH,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

        # Diabetic Foot Exam: Annually
        if not _has_recent_encounter(db, patient.id, "foot exam", 12):
            gap = _create_gap(
                db, patient.id, GapType.CHECKUP,
                "Diabetic Foot Exam",
                f"Patients with diabetes should have a comprehensive foot exam annually "
                f"to prevent complications.",
                GapPriority.MEDIUM,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

        # Kidney Function Test: Annually for diabetics (HEDIS KED)
        if not _has_recent_encounter(db, patient.id, "kidney function", 12):
            gap = _create_gap(
                db, patient.id, GapType.LAB,
                "Kidney Function Test (eGFR/Creatinine)",
                f"Patients with diabetes should have kidney function monitored annually. "
                f"Diabetes is a leading cause of chronic kidney disease.",
                GapPriority.HIGH,
                due_months=2
            )
            if gap:
                new_gaps.append(gap)

    # ─── CARDIOVASCULAR ─────────────────────────────────

    if _has_condition(db, patient.id, "heart") or _has_condition(db, patient.id, "hypertension"):
        # EKG monitoring
        if not _has_recent_encounter(db, patient.id, "ekg", 12):
            gap = _create_gap(
                db, patient.id, GapType.CHECKUP,
                "Cardiac Assessment (EKG)",
                f"Patients with cardiovascular conditions should have regular cardiac monitoring.",
                GapPriority.HIGH,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

    # ─── VACCINATIONS ───────────────────────────────────

    # Flu Vaccine: Annually for all adults
    if not _has_recent_encounter(db, patient.id, "flu vaccine", 12):
        gap = _create_gap(
            db, patient.id, GapType.VACCINATION,
            "Annual Influenza Vaccination",
            f"All adults should receive an annual flu vaccine, especially those with "
            f"chronic conditions or age 65+.",
            GapPriority.HIGH if age >= 65 else GapPriority.MEDIUM,
            due_months=2
        )
        if gap:
            new_gaps.append(gap)

    # Pneumonia Vaccine: Adults 65+
    if age >= 65:
        if not _has_recent_encounter(db, patient.id, "pneumonia vaccine", 60):
            gap = _create_gap(
                db, patient.id, GapType.VACCINATION,
                "Pneumococcal Vaccination",
                f"Adults 65+ should receive pneumococcal vaccination (PCV20 or PCV15+PPSV23).",
                GapPriority.HIGH,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

    # Shingles Vaccine: Adults 50+
    if age >= 50:
        if not _has_recent_encounter(db, patient.id, "shingles vaccine", 120):
            gap = _create_gap(
                db, patient.id, GapType.VACCINATION,
                "Shingles (Zoster) Vaccination",
                f"Adults 50+ should receive the recombinant zoster vaccine (Shingrix) "
                f"to prevent shingles.",
                GapPriority.MEDIUM,
                due_months=6
            )
            if gap:
                new_gaps.append(gap)

    # Tdap Booster: Every 10 years
    if age >= 19:
        if not _has_recent_encounter(db, patient.id, "tdap", 120):
            gap = _create_gap(
                db, patient.id, GapType.VACCINATION,
                "Tdap Booster Vaccination",
                f"Adults should receive a Tdap booster every 10 years.",
                GapPriority.LOW,
                due_months=6
            )
            if gap:
                new_gaps.append(gap)

    # ─── CHECKUPS ───────────────────────────────────────

    # Annual Wellness Visit
    if not _has_recent_encounter(db, patient.id, "wellness visit", 12):
        gap = _create_gap(
            db, patient.id, GapType.CHECKUP,
            "Annual Wellness Visit",
            f"All patients should have an annual wellness visit for preventive care "
            f"assessment and care planning.",
            GapPriority.MEDIUM,
            due_months=3
        )
        if gap:
            new_gaps.append(gap)

    # ─── COPD-SPECIFIC ──────────────────────────────────

    if _has_condition(db, patient.id, "copd"):
        if not _has_recent_encounter(db, patient.id, "spirometry", 12):
            gap = _create_gap(
                db, patient.id, GapType.CHECKUP,
                "Pulmonary Function Test (Spirometry)",
                f"Patients with COPD should have pulmonary function tested annually.",
                GapPriority.HIGH,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

    # ─── THYROID MONITORING ─────────────────────────────

    if _has_condition(db, patient.id, "hypothyroid") or _has_medication(db, patient.id, "levothyroxine"):
        if not _has_recent_encounter(db, patient.id, "thyroid", 12):
            gap = _create_gap(
                db, patient.id, GapType.LAB,
                "Thyroid Function Test (TSH)",
                f"Patients on thyroid medication should have TSH levels monitored annually.",
                GapPriority.MEDIUM,
                due_months=3
            )
            if gap:
                new_gaps.append(gap)

    # Mark overdue gaps
    _update_overdue_status(db, patient.id)

    db.commit()
    return new_gaps


def _update_overdue_status(db: Session, patient_id: int):
    """Mark open gaps past their due date as overdue."""
    overdue_gaps = db.query(CareGap).filter(
        CareGap.patient_id == patient_id,
        CareGap.status == GapStatus.OPEN,
        CareGap.due_date < date.today()
    ).all()

    for gap in overdue_gaps:
        gap.status = GapStatus.OVERDUE


def analyze_all_patients(db: Session) -> dict:
    """Run care gap analysis for all patients."""
    patients = db.query(Patient).all()
    total_new_gaps = 0
    for patient in patients:
        new_gaps = analyze_patient_care_gaps(patient, db)
        total_new_gaps += len(new_gaps)
    return {"patients_analyzed": len(patients), "new_gaps_found": total_new_gaps}
