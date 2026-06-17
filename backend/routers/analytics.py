"""
CareSync Analytics Router
Dashboard KPIs, charts, and population health analytics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import (
    Patient, User, CareGap, Condition, CarePlan,
    RiskLevel, GapStatus, GapType, ConditionStatus, CarePlanStatus, UserRole
)
from schemas import (
    DashboardKPIs, RiskDistribution, CareGapTrend,
    TopCondition, ProviderPerformance
)
from auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get high-level dashboard KPI metrics."""
    total_patients = db.query(Patient).count()

    high_risk = db.query(Patient).filter(
        Patient.risk_level == RiskLevel.HIGH
    ).count()

    critical_risk = db.query(Patient).filter(
        Patient.risk_level == RiskLevel.CRITICAL
    ).count()

    total_open = db.query(CareGap).filter(
        CareGap.status.in_([GapStatus.OPEN, GapStatus.OVERDUE])
    ).count()

    total_closed = db.query(CareGap).filter(
        CareGap.status == GapStatus.CLOSED
    ).count()

    total_gaps = total_open + total_closed
    closure_rate = (total_closed / total_gaps * 100) if total_gaps > 0 else 0

    total_care_plans = db.query(CarePlan).count()
    active_care_plans = db.query(CarePlan).filter(
        CarePlan.status == CarePlanStatus.ACTIVE
    ).count()

    return DashboardKPIs(
        total_patients=total_patients,
        high_risk_patients=high_risk,
        critical_risk_patients=critical_risk,
        total_open_gaps=total_open,
        total_closed_gaps=total_closed,
        gap_closure_rate=round(closure_rate, 1),
        total_care_plans=total_care_plans,
        active_care_plans=active_care_plans
    )


@router.get("/risk-distribution", response_model=List[RiskDistribution])
async def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get patient distribution by risk level."""
    total = db.query(Patient).count()
    if total == 0:
        return []

    results = []
    for level in RiskLevel:
        count = db.query(Patient).filter(Patient.risk_level == level).count()
        results.append(RiskDistribution(
            level=level.value,
            count=count,
            percentage=round(count / total * 100, 1)
        ))

    return results


@router.get("/care-gap-trends", response_model=List[CareGapTrend])
async def get_care_gap_trends(
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get care gap opened vs closed trends over recent months."""
    results = []
    now = datetime.utcnow()

    for i in range(months - 1, -1, -1):
        month_start = (now - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0)
        if i > 0:
            month_end = (now - timedelta(days=(i - 1) * 30)).replace(day=1, hour=0, minute=0, second=0)
        else:
            month_end = now

        opened = db.query(CareGap).filter(
            CareGap.created_at >= month_start,
            CareGap.created_at < month_end
        ).count()

        closed = db.query(CareGap).filter(
            CareGap.closed_date >= month_start.date(),
            CareGap.closed_date < month_end.date()
        ).count()

        results.append(CareGapTrend(
            month=month_start.strftime("%b %Y"),
            opened=opened,
            closed=closed
        ))

    return results


@router.get("/top-conditions", response_model=List[TopCondition])
async def get_top_conditions(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get most prevalent active conditions."""
    total_patients = db.query(Patient).count()
    if total_patients == 0:
        return []

    conditions = db.query(
        Condition.name,
        func.count(Condition.id).label("count")
    ).filter(
        Condition.status == ConditionStatus.ACTIVE
    ).group_by(
        Condition.name
    ).order_by(
        func.count(Condition.id).desc()
    ).limit(limit).all()

    return [
        TopCondition(
            name=c.name,
            count=c.count,
            percentage=round(c.count / total_patients * 100, 1)
        )
        for c in conditions
    ]


@router.get("/provider-performance", response_model=List[ProviderPerformance])
async def get_provider_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get care gap closure metrics by provider."""
    providers = db.query(User).filter(User.role == UserRole.PROVIDER).all()
    results = []

    for provider in providers:
        patient_count = db.query(Patient).filter(
            Patient.pcp_id == provider.id
        ).count()

        if patient_count == 0:
            continue

        patient_ids = [p.id for p in db.query(Patient.id).filter(
            Patient.pcp_id == provider.id
        ).all()]

        open_gaps = db.query(CareGap).filter(
            CareGap.patient_id.in_(patient_ids),
            CareGap.status.in_([GapStatus.OPEN, GapStatus.OVERDUE])
        ).count()

        closed_gaps = db.query(CareGap).filter(
            CareGap.patient_id.in_(patient_ids),
            CareGap.status == GapStatus.CLOSED
        ).count()

        total = open_gaps + closed_gaps
        closure_rate = (closed_gaps / total * 100) if total > 0 else 0

        results.append(ProviderPerformance(
            provider_name=provider.full_name,
            patient_count=patient_count,
            open_gaps=open_gaps,
            closed_gaps=closed_gaps,
            closure_rate=round(closure_rate, 1)
        ))

    return sorted(results, key=lambda x: x.closure_rate, reverse=True)


@router.get("/gap-type-breakdown")
async def get_gap_type_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get care gap counts by type and status."""
    results = []
    for gap_type in GapType:
        open_count = db.query(CareGap).filter(
            CareGap.gap_type == gap_type,
            CareGap.status == GapStatus.OPEN
        ).count()

        overdue_count = db.query(CareGap).filter(
            CareGap.gap_type == gap_type,
            CareGap.status == GapStatus.OVERDUE
        ).count()

        closed_count = db.query(CareGap).filter(
            CareGap.gap_type == gap_type,
            CareGap.status == GapStatus.CLOSED
        ).count()

        results.append({
            "type": gap_type.value,
            "open": open_count,
            "overdue": overdue_count,
            "closed": closed_count,
            "total": open_count + overdue_count + closed_count
        })

    return results
