

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import WeeklyReport, Territory
from app.schemas.reports import WeeklyReportPublic, StateAggregation

router = APIRouter()

@router.get("/", response_model=List[WeeklyReportPublic], summary="Lista relatórios semanais (detalhado)")
async def read_reports(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    geocode: Optional[str] = Query(None, description="Filtra por código IBGE do município"),
    state_code: Optional[int] = Query(None, description="Filtra por código do estado"),
    se: Optional[int] = Query(None, description="Filtra por Semana Epidemiológica exata"),
    se_start: Optional[int] = Query(None, description="Semana Epidemiológica inicial"),
    se_end: Optional[int] = Query(None, description="Semana Epidemiológica final"),
):
    
    stmt = select(WeeklyReport).options(selectinload(WeeklyReport.territory))

    
    if geocode:
        stmt = stmt.where(WeeklyReport.geocode == geocode)
    
    if state_code:
        
        stmt = stmt.join(WeeklyReport.territory).where(Territory.state_code == state_code)
    
    if se:
        stmt = stmt.where(WeeklyReport.se == se)
    
    if se_start:
        stmt = stmt.where(WeeklyReport.se >= se_start)
    if se_end:
        stmt = stmt.where(WeeklyReport.se <= se_end)

    
    stmt = stmt.order_by(desc(WeeklyReport.se), WeeklyReport.geocode).offset(skip).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/by_state", response_model=List[StateAggregation], summary="Dados agregados por Estado (Para o Mapa)")
async def read_reports_by_state(
    db: AsyncSession = Depends(get_db),
    se: int = Query(..., description="Semana Epidemiológica obrigatória para o mapa (ex: 202544)")
):
    
    stmt = (
        select(
            Territory.state_code,
            func.sum(WeeklyReport.reported_cases).label("total_cases"),
            func.avg(WeeklyReport.alert_level).label("avg_alert_level"),
            func.sum(WeeklyReport.population).label("total_population"),
            func.count(WeeklyReport.id).label("report_count")
        )
        .join(Territory, WeeklyReport.geocode == Territory.geocode)
        .where(WeeklyReport.se == se)
        .group_by(Territory.state_code)
        .order_by(Territory.state_code)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    
    return [
        StateAggregation(
            state_code=row.state_code,
            total_cases=row.total_cases or 0,
            avg_alert_level=row.avg_alert_level or 0.0,
            total_population=row.total_population or 0.0,
            report_count=row.report_count
        )
        for row in rows
    ]