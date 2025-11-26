from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.models.models import WeeklyReport
from app.services.map_service import generate_choropleth_map, generate_city_map

router = APIRouter()

@router.get("/render", response_class=HTMLResponse, summary="Renderiza o HTML do mapa")
async def render_map_html(
    se: int = Query(..., description="Semana Epidemiológica (ex: 202545)"),
    scope: str = Query("br", description="Escopo: 'br' (Brasil) ou 'pe' (Pernambuco)"),
    db: AsyncSession = Depends(get_db)
):
    
    if scope == 'pe':
        map_html = await generate_city_map(db, se)
    else:
        map_html = await generate_choropleth_map(db, se)
        
    return map_html


@router.get("/dashboard", response_class=HTMLResponse, summary="Página principal do Dashboard")
async def get_dashboard_page(db: AsyncSession = Depends(get_db)):
    
    
    stmt = select(WeeklyReport.se).distinct().order_by(desc(WeeklyReport.se))
    result = await db.execute(stmt)
    available_ses = result.scalars().all()

    if not available_ses:
        return HTMLResponse("<h1>Nenhum dado disponível. Execute o script de backfill.</h1>")

    latest_se = available_ses[0]
    
    
    options_html = ""
    for se in available_ses:
        year = str(se)[:4]
        week = str(se)[4:]
        selected = "selected" if se == latest_se else ""
        options_html += f'<option value="{se}" {selected}>Ano {year} - Semana {week} (SE {se})</option>'

    
    html_content = f
    return HTMLResponse(content=html_content, status_code=200)