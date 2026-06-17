"""
CareSync Seed Data Generator
Creates realistic synthetic patient data for demonstration
"""
import random
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from models import (
    User, Patient, Condition, Medication, CareGap, CarePlan, Encounter,
    UserRole, Gender, ConditionStatus, GapType, GapStatus, GapPriority,
    CarePlanStatus, RiskLevel
)
from auth import get_password_hash
from engines.risk_engine import update_all_patient_risks
from engines.care_gap_engine import analyze_all_patients


# ─── Sample Data ────────────────────────────────────────

FIRST_NAMES_M = [
    "James", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony",
    "Mark", "Donald", "Steven", "Paul", "Andrew", "Kenneth", "George",
    "Edward", "Brian", "Ronald", "Timothy", "Jason", "Jeffrey", "Frank"
]

FIRST_NAMES_F = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Margaret",
    "Betty", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily", "Donna",
    "Michelle", "Carol", "Amanda", "Melissa", "Deborah", "Stephanie", "Rebecca"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"
]

STREETS = [
    "Oak Street", "Maple Avenue", "Cedar Lane", "Pine Drive", "Elm Street",
    "Washington Boulevard", "Park Avenue", "Main Street", "Broadway",
    "Lake Drive", "Highland Road", "Sunset Boulevard", "River Road",
    "Forest Lane", "Meadow Drive", "Valley Road"
]

CITIES = [
    "Minneapolis, MN", "Saint Paul, MN", "Eden Prairie, MN", "Bloomington, MN",
    "Plymouth, MN", "Minnetonka, MN", "Edina, MN", "Maple Grove, MN",
    "Brooklyn Park, MN", "Burnsville, MN"
]

CONDITIONS_DATA = [
    # (name, icd_code, is_chronic, weight)
    ("Type 2 Diabetes Mellitus", "E11.9", True, 20),
    ("Essential Hypertension", "I10", True, 18),
    ("Hyperlipidemia", "E78.5", True, 10),
    ("Coronary Artery Disease", "I25.10", True, 8),
    ("Heart Failure", "I50.9", True, 6),
    ("COPD", "J44.1", True, 8),
    ("Asthma", "J45.20", True, 12),
    ("Chronic Kidney Disease Stage 3", "N18.3", True, 6),
    ("Major Depressive Disorder", "F33.0", True, 10),
    ("Anxiety Disorder", "F41.1", True, 12),
    ("Atrial Fibrillation", "I48.91", True, 5),
    ("Hypothyroidism", "E03.9", True, 10),
    ("Obesity", "E66.01", True, 15),
    ("Osteoarthritis", "M19.90", True, 10),
    ("Osteoporosis", "M81.0", True, 5),
    ("Rheumatoid Arthritis", "M06.9", True, 4),
    ("GERD", "K21.0", True, 8),
    ("Peripheral Vascular Disease", "I73.9", True, 3),
]

MEDICATIONS_DATA = [
    # (name, dosage, frequency, for_conditions)
    ("Metformin", "500mg", "Twice daily", ["diabetes"]),
    ("Lisinopril", "10mg", "Once daily", ["hypertension", "heart"]),
    ("Atorvastatin", "20mg", "Once daily at bedtime", ["hyperlipidemia", "coronary"]),
    ("Amlodipine", "5mg", "Once daily", ["hypertension"]),
    ("Metoprolol", "25mg", "Twice daily", ["hypertension", "heart", "atrial"]),
    ("Omeprazole", "20mg", "Once daily before breakfast", ["gerd"]),
    ("Levothyroxine", "50mcg", "Once daily on empty stomach", ["hypothyroidism"]),
    ("Albuterol Inhaler", "90mcg", "As needed", ["asthma", "copd"]),
    ("Sertraline", "50mg", "Once daily", ["depression", "anxiety"]),
    ("Gabapentin", "300mg", "Three times daily", ["pain"]),
    ("Losartan", "50mg", "Once daily", ["hypertension"]),
    ("Furosemide", "40mg", "Once daily", ["heart failure"]),
    ("Warfarin", "5mg", "Once daily", ["atrial fibrillation"]),
    ("Insulin Glargine", "20 units", "Once daily at bedtime", ["diabetes"]),
    ("Clopidogrel", "75mg", "Once daily", ["coronary"]),
    ("Montelukast", "10mg", "Once daily at bedtime", ["asthma"]),
    ("Prednisone", "5mg", "As directed", ["rheumatoid", "copd"]),
    ("Hydrochlorothiazide", "25mg", "Once daily", ["hypertension"]),
    ("Aspirin", "81mg", "Once daily", ["coronary", "heart"]),
    ("Calcium + Vitamin D", "600mg/400IU", "Twice daily", ["osteoporosis"]),
]

ENCOUNTER_TYPES = [
    "Annual Wellness Visit", "Follow-up Visit", "Urgent Care Visit",
    "Specialist Consultation", "Lab Work", "Medication Review",
    "Chronic Care Management", "Preventive Screening"
]


def _random_date(start_year=2020, end_year=2026):
    """Generate a random date between start and end year."""
    start = date(start_year, 1, 1)
    end = date(min(end_year, 2026), 6, 15)
    delta = (end - start).days
    random_days = random.randint(0, max(delta, 1))
    return start + timedelta(days=random_days)


def _random_dob(min_age=25, max_age=85):
    """Generate random date of birth for given age range."""
    today = date.today()
    age = random.randint(min_age, max_age)
    year = today.year - age
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


def seed_database(db: Session):
    """Seed the database with synthetic patient data."""

    # Check if already seeded
    if db.query(User).count() > 0:
        print("Database already seeded. Skipping.")
        return

    print("🌱 Seeding database with synthetic data...")

    # ─── Create Users ───────────────────────────────────
    demo_password = get_password_hash("demo123")

    providers = [
        User(
            email="provider@caresync.com",
            username="dr.chen",
            full_name="Dr. Sarah Chen",
            hashed_password=demo_password,
            role=UserRole.PROVIDER,
            specialty="Internal Medicine"
        ),
        User(
            email="admin@caresync.com",
            username="admin",
            full_name="Dr. Admin User",
            hashed_password=demo_password,
            role=UserRole.ADMIN,
            specialty="Healthcare Administration"
        ),
        User(
            email="dr.patel@caresync.com",
            username="dr.patel",
            full_name="Dr. Rajesh Patel",
            hashed_password=demo_password,
            role=UserRole.PROVIDER,
            specialty="Family Medicine"
        ),
        User(
            email="dr.williams@caresync.com",
            username="dr.williams",
            full_name="Dr. Maria Williams",
            hashed_password=demo_password,
            role=UserRole.PROVIDER,
            specialty="Geriatric Medicine"
        ),
        User(
            email="dr.kim@caresync.com",
            username="dr.kim",
            full_name="Dr. James Kim",
            hashed_password=demo_password,
            role=UserRole.PROVIDER,
            specialty="Cardiology"
        ),
    ]

    for provider in providers:
        db.add(provider)
    db.flush()

    provider_ids = [p.id for p in providers if p.role == UserRole.PROVIDER]

    # ─── Create Patients ────────────────────────────────
    patients = []
    used_names = set()

    for i in range(50):
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        first_name = random.choice(FIRST_NAMES_M if gender == Gender.MALE else FIRST_NAMES_F)
        last_name = random.choice(LAST_NAMES)

        # Avoid duplicate names
        while f"{first_name} {last_name}" in used_names:
            last_name = random.choice(LAST_NAMES)
        used_names.add(f"{first_name} {last_name}")

        # Age distribution weighted toward older adults (healthcare population)
        age_group = random.choices(
            [(25, 40), (40, 55), (55, 65), (65, 75), (75, 85)],
            weights=[10, 20, 25, 30, 15],
            k=1
        )[0]

        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=_random_dob(*age_group),
            gender=gender,
            phone=f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}",
            email=f"{first_name.lower()}.{last_name.lower()}@email.com",
            address=f"{random.randint(100,9999)} {random.choice(STREETS)}, {random.choice(CITIES)}",
            insurance_id=f"OPT{random.randint(100000, 999999)}",
            pcp_id=random.choice(provider_ids),
        )
        db.add(patient)
        patients.append(patient)

    db.flush()

    # ─── Assign Conditions ──────────────────────────────
    for patient in patients:
        age = patient.age

        # Number of conditions based on age
        if age >= 70:
            num_conditions = random.choices([1, 2, 3, 4, 5], weights=[5, 15, 30, 30, 20], k=1)[0]
        elif age >= 55:
            num_conditions = random.choices([0, 1, 2, 3, 4], weights=[10, 20, 30, 25, 15], k=1)[0]
        elif age >= 40:
            num_conditions = random.choices([0, 1, 2, 3], weights=[20, 35, 30, 15], k=1)[0]
        else:
            num_conditions = random.choices([0, 1, 2], weights=[40, 40, 20], k=1)[0]

        if num_conditions > 0:
            # Weight certain conditions by age
            available_conditions = CONDITIONS_DATA.copy()
            weights = [c[3] for c in available_conditions]

            selected = random.choices(
                available_conditions,
                weights=weights,
                k=min(num_conditions, len(available_conditions))
            )
            # Remove duplicates
            seen = set()
            unique_selected = []
            for c in selected:
                if c[0] not in seen:
                    seen.add(c[0])
                    unique_selected.append(c)

            for cond_data in unique_selected:
                condition = Condition(
                    patient_id=patient.id,
                    name=cond_data[0],
                    icd_code=cond_data[1],
                    is_chronic=cond_data[2],
                    diagnosed_date=_random_date(2018, 2025),
                    status=ConditionStatus.ACTIVE
                )
                db.add(condition)

    db.flush()

    # ─── Assign Medications ─────────────────────────────
    for patient in patients:
        patient_conditions = db.query(Condition).filter(
            Condition.patient_id == patient.id,
            Condition.status == ConditionStatus.ACTIVE
        ).all()

        condition_names = [c.name.lower() for c in patient_conditions]

        for med_data in MEDICATIONS_DATA:
            # Check if medication is relevant to patient's conditions
            relevant = False
            for cond_keyword in med_data[3]:
                for cond_name in condition_names:
                    if cond_keyword in cond_name:
                        relevant = True
                        break
                if relevant:
                    break

            if relevant and random.random() < 0.7:
                medication = Medication(
                    patient_id=patient.id,
                    name=med_data[0],
                    dosage=med_data[1],
                    frequency=med_data[2],
                    start_date=_random_date(2020, 2025),
                    is_active=True,
                    prescriber_id=patient.pcp_id
                )
                db.add(medication)

    db.flush()

    # ─── Create Encounters ──────────────────────────────
    for patient in patients:
        # Each patient gets 2-8 encounters
        num_encounters = random.randint(2, 8)

        for _ in range(num_encounters):
            enc_date = _random_date(2023, 2026)
            enc_type = random.choice(ENCOUNTER_TYPES)

            encounter = Encounter(
                patient_id=patient.id,
                provider_id=patient.pcp_id,
                encounter_type=enc_type,
                encounter_date=datetime.combine(enc_date, datetime.min.time()),
                notes=f"Routine {enc_type.lower()} completed. Patient in stable condition.",
                vitals_bp_systolic=random.randint(110, 160),
                vitals_bp_diastolic=random.randint(65, 100),
                vitals_heart_rate=random.randint(60, 100),
                vitals_temperature=round(random.uniform(97.5, 99.0), 1),
                vitals_weight=round(random.uniform(120, 280), 1),
                vitals_height=round(random.uniform(60, 76), 1),
                vitals_bmi=round(random.uniform(20, 38), 1),
            )
            db.add(encounter)

    db.flush()

    # ─── Create Some Pre-existing Care Gaps ─────────────
    # Some gaps already closed (to show history), some open
    gap_templates = [
        (GapType.SCREENING, "Blood Pressure Screening", GapPriority.MEDIUM),
        (GapType.VACCINATION, "Annual Influenza Vaccination", GapPriority.MEDIUM),
        (GapType.CHECKUP, "Annual Wellness Visit", GapPriority.MEDIUM),
        (GapType.LAB, "Lipid Panel Screening", GapPriority.MEDIUM),
    ]

    for patient in patients[:30]:
        # Add 1-3 closed gaps (historical)
        num_closed = random.randint(1, 3)
        for _ in range(num_closed):
            template = random.choice(gap_templates)
            created = _random_date(2024, 2025)
            closed = created + timedelta(days=random.randint(7, 60))

            gap = CareGap(
                patient_id=patient.id,
                gap_type=template[0],
                title=template[1],
                description=f"Previously identified care gap. Resolved through routine care.",
                priority=template[2],
                status=GapStatus.CLOSED,
                due_date=created + timedelta(days=90),
                closed_date=closed,
                resolution_notes="Completed during scheduled appointment.",
                created_at=datetime.combine(created, datetime.min.time())
            )
            db.add(gap)

    db.flush()

    # ─── Create Care Plans for High-Risk Patients ───────
    care_plan_templates = [
        ("Diabetes Management Plan", "Comprehensive diabetes management including medication adherence, diet counseling, and regular monitoring.", "Maintain HbA1c below 7.0%; Regular foot and eye exams; Daily blood sugar monitoring"),
        ("Cardiovascular Risk Reduction", "Multi-faceted approach to reduce cardiovascular risk through lifestyle modifications and medication management.", "Blood pressure below 130/80; LDL cholesterol below 100; Regular exercise 150 min/week"),
        ("Chronic Care Coordination", "Coordinated care plan for managing multiple chronic conditions.", "Quarterly provider visits; Medication reconciliation; Preventive screening compliance"),
        ("Fall Prevention Program", "Evidence-based fall prevention for elderly patients.", "Home safety assessment; Balance exercises 3x/week; Medication review for fall risk"),
        ("Weight Management Program", "Structured weight management with dietary counseling and activity planning.", "5-10% weight reduction over 6 months; Weekly activity tracking; Monthly nutritional counseling"),
    ]

    for patient in random.sample(patients, 20):
        template = random.choice(care_plan_templates)
        plan = CarePlan(
            patient_id=patient.id,
            created_by=patient.pcp_id,
            title=template[0],
            description=template[1],
            goals=template[2],
            status=random.choice([CarePlanStatus.ACTIVE, CarePlanStatus.ACTIVE, CarePlanStatus.COMPLETED]),
            start_date=_random_date(2024, 2025),
            end_date=_random_date(2025, 2026),
        )
        db.add(plan)

    db.commit()

    # ─── Run Care Gap Analysis ──────────────────────────
    print("🔍 Running care gap analysis engine...")
    result = analyze_all_patients(db)
    print(f"   → Analyzed {result['patients_analyzed']} patients, found {result['new_gaps_found']} new care gaps")

    # ─── Calculate Risk Scores ──────────────────────────
    print("📊 Calculating risk scores...")
    count = update_all_patient_risks(db)
    print(f"   → Updated risk scores for {count} patients")

    # Print summary
    from models import RiskLevel
    for level in RiskLevel:
        count = db.query(Patient).filter(Patient.risk_level == level).count()
        print(f"   → {level.value.capitalize()}: {count} patients")

    total_gaps = db.query(CareGap).count()
    open_gaps = db.query(CareGap).filter(CareGap.status.in_([GapStatus.OPEN, GapStatus.OVERDUE])).count()
    print(f"\n✅ Seeding complete!")
    print(f"   → {len(patients)} patients | {total_gaps} care gaps ({open_gaps} open) | {len(providers)} providers")
    print(f"\n🔐 Demo Credentials:")
    print(f"   Provider: provider@caresync.com / demo123")
    print(f"   Admin:    admin@caresync.com / demo123")
