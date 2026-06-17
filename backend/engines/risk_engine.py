"""
CareSync Risk Scoring Engine
Calculates patient risk scores based on clinical factors
"""
from sqlalchemy.orm import Session
from models import Patient, Condition, Medication, CareGap, RiskLevel, GapStatus, ConditionStatus
from datetime import date


# ─── Condition Risk Weights ─────────────────────────────
# Based on disease burden and resource utilization patterns

CONDITION_WEIGHTS = {
    # Cardiovascular
    "heart failure": 25,
    "coronary artery disease": 22,
    "atrial fibrillation": 18,
    "hypertension": 10,
    "hyperlipidemia": 8,
    "peripheral vascular disease": 15,

    # Metabolic
    "type 2 diabetes": 18,
    "type 1 diabetes": 20,
    "obesity": 10,
    "metabolic syndrome": 12,

    # Respiratory
    "copd": 20,
    "asthma": 8,
    "pulmonary fibrosis": 22,

    # Renal
    "chronic kidney disease": 20,
    "end stage renal disease": 30,

    # Mental Health
    "major depression": 10,
    "anxiety disorder": 6,
    "bipolar disorder": 12,
    "schizophrenia": 15,

    # Other Chronic
    "rheumatoid arthritis": 8,
    "osteoporosis": 6,
    "cancer": 25,
    "liver cirrhosis": 22,
    "hypothyroidism": 5,
    "epilepsy": 10,
}


def calculate_risk_score(patient: Patient, db: Session) -> tuple[float, RiskLevel]:
    """
    Calculate a patient's risk score (0-100) based on multiple clinical factors.

    Factors considered:
    1. Age (elderly patients at higher risk)
    2. Chronic condition burden (weighted by severity)
    3. Medication count (polypharmacy risk)
    4. Open care gap count (unresolved preventive needs)
    5. Number of active conditions
    """
    score = 0.0

    # ─── Age Factor (0-20 points) ────────────────────────
    age = patient.age
    if age >= 80:
        score += 20
    elif age >= 70:
        score += 16
    elif age >= 65:
        score += 12
    elif age >= 55:
        score += 8
    elif age >= 45:
        score += 4
    elif age >= 35:
        score += 2

    # ─── Chronic Condition Burden (0-50 points) ──────────
    active_conditions = db.query(Condition).filter(
        Condition.patient_id == patient.id,
        Condition.status == ConditionStatus.ACTIVE
    ).all()

    condition_score = 0
    chronic_count = 0

    for condition in active_conditions:
        cond_name = condition.name.lower()
        # Check for matching condition weights
        for key, weight in CONDITION_WEIGHTS.items():
            if key in cond_name:
                condition_score += weight
                break
        else:
            # Default weight for unknown conditions
            condition_score += 5

        if condition.is_chronic:
            chronic_count += 1

    # Cap condition score at 50
    score += min(condition_score, 50)

    # ─── Comorbidity Multiplier ──────────────────────────
    # Multiple chronic conditions compound risk
    if chronic_count >= 4:
        score += 10
    elif chronic_count >= 3:
        score += 6
    elif chronic_count >= 2:
        score += 3

    # ─── Polypharmacy Factor (0-10 points) ───────────────
    active_meds = db.query(Medication).filter(
        Medication.patient_id == patient.id,
        Medication.is_active == True
    ).count()

    if active_meds >= 10:
        score += 10
    elif active_meds >= 7:
        score += 7
    elif active_meds >= 5:
        score += 5
    elif active_meds >= 3:
        score += 2

    # ─── Open Care Gaps Factor (0-10 points) ─────────────
    open_gaps = db.query(CareGap).filter(
        CareGap.patient_id == patient.id,
        CareGap.status.in_([GapStatus.OPEN, GapStatus.OVERDUE])
    ).count()

    overdue_gaps = db.query(CareGap).filter(
        CareGap.patient_id == patient.id,
        CareGap.status == GapStatus.OVERDUE
    ).count()

    if open_gaps >= 5:
        score += 8
    elif open_gaps >= 3:
        score += 5
    elif open_gaps >= 1:
        score += 2

    # Overdue gaps are extra concerning
    score += min(overdue_gaps * 2, 5)

    # ─── Normalize and Classify ──────────────────────────
    final_score = min(round(score, 1), 100.0)

    if final_score >= 81:
        risk_level = RiskLevel.CRITICAL
    elif final_score >= 61:
        risk_level = RiskLevel.HIGH
    elif final_score >= 31:
        risk_level = RiskLevel.MODERATE
    else:
        risk_level = RiskLevel.LOW

    return final_score, risk_level


def update_patient_risk(patient: Patient, db: Session) -> tuple[float, RiskLevel]:
    """Calculate and persist a patient's risk score."""
    score, level = calculate_risk_score(patient, db)
    patient.risk_score = score
    patient.risk_level = level
    db.commit()
    db.refresh(patient)
    return score, level


def update_all_patient_risks(db: Session) -> int:
    """Recalculate risk scores for all patients."""
    patients = db.query(Patient).all()
    for patient in patients:
        score, level = calculate_risk_score(patient, db)
        patient.risk_score = score
        patient.risk_level = level
    db.commit()
    return len(patients)
