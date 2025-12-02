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
    """
    Retorna o HTML puro do mapa Folium.
    """
    if scope == 'pe':
        map_html = await generate_city_map(db, se)
    else:
        map_html = await generate_choropleth_map(db, se)
        
    return map_html


@router.get("/dashboard", response_class=HTMLResponse, summary="Página principal do Dashboard")
async def get_dashboard_page(db: AsyncSession = Depends(get_db)):
    """
    Retorna a página HTML completa do Dashboard com seletores.
    """
    stmt = select(WeeklyReport.se).distinct().order_by(desc(WeeklyReport.se))
    result = await db.execute(stmt)
    available_ses = result.scalars().all()

    if not available_ses:
        return HTMLResponse("<h1>Nenhum dado disponível. Execute o script de backfill.</h1>")

    latest_se = available_ses[0]
    
    # Gera opções do select
    options_html = ""
    for se in available_ses:
        year = str(se)[:4]
        week = str(se)[4:]
        selected = "selected" if se == latest_se else ""
        options_html += f'<option value="{se}" {selected}>Ano {year} - Semana {week} (SE {se})</option>'

    # 2. HTML do Dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Painel de Monitoramento da Dengue</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body, html {{ height: 100%; }}
            .map-container {{ height: calc(100vh - 80px); }}
        </style>
    </head>
    <body class="bg-gray-100 font-sans overflow-hidden">
        
        <nav class="bg-blue-900 p-4 shadow-md text-white flex justify-between items-center h-20">
            <div class="flex items-center space-x-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0121 18.382V7.618a1 1 0 01-1.447-.894L15 7m0 13V7" />
                </svg>
                <h1 class="text-xl font-bold hidden md:block">Monitoramento Dengue <span class="font-light opacity-75">| InfoDengue</span></h1>
                <h1 class="text-xl font-bold md:hidden">Dengue API</h1>
            </div>
            
            <div class="flex items-center space-x-2 md:space-x-4">
                <div class="bg-blue-800 rounded-lg p-1 flex">
                    <button id="btn-br" class="px-3 py-1 rounded bg-blue-600 text-white font-medium text-sm shadow transition duration-200">Brasil</button>
                    <button id="btn-pe" class="px-3 py-1 rounded hover:bg-blue-700 text-blue-200 font-medium text-sm ml-1 transition duration-200">Pernambuco</button>
                </div>

                <div class="flex items-center bg-blue-800 rounded-lg p-1">
                    <label for="se-selector" class="hidden md:inline mr-2 text-sm font-medium pl-2">Período:</label>
                    <select id="se-selector" class="bg-blue-700 text-white text-sm rounded-md border-none focus:ring-2 focus:ring-blue-500 py-2 pl-3 pr-2 cursor-pointer">
                        {options_html}
                    </select>
                </div>
            </div>
        </nav>

        <main class="map-container w-full relative bg-white">
            <div id="loading" class="hidden absolute inset-0 bg-white bg-opacity-75 z-20 flex items-center justify-center">
                <div class="flex flex-col items-center">
                    <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-900 mb-4"></div>
                    <span class="text-blue-900 font-semibold">Carregando dados...</span>
                </div>
            </div>
            
            <iframe id="map-frame" src="/api/v1/map/render?se={latest_se}&scope=br" class="w-full h-full border-none"></iframe>
        </main>

        <script>
            const selector = document.getElementById('se-selector');
            const mapFrame = document.getElementById('map-frame');
            const loading = document.getElementById('loading');
            const btnBr = document.getElementById('btn-br');
            const btnPe = document.getElementById('btn-pe');
            
            let currentScope = 'br';

            function updateMap() {{
                const selectedSe = selector.value;
                loading.classList.remove('hidden');
                // Adiciona timestamp para evitar cache do navegador
                mapFrame.src = `/api/v1/map/render?se=${{selectedSe}}&scope=${{currentScope}}&t=${{new Date().getTime()}}`;
            }}

            function setScope(scope) {{
                currentScope = scope;
                if (scope === 'br') {{
                    btnBr.className = "px-3 py-1 rounded bg-blue-600 text-white font-medium text-sm shadow transition duration-200";
                    btnPe.className = "px-3 py-1 rounded hover:bg-blue-700 text-blue-200 font-medium text-sm ml-1 transition duration-200";
                }} else {{
                    btnPe.className = "px-3 py-1 rounded bg-blue-600 text-white font-medium text-sm shadow transition duration-200 ml-1";
                    btnBr.className = "px-3 py-1 rounded hover:bg-blue-700 text-blue-200 font-medium text-sm transition duration-200";
                }}
                updateMap();
            }}

            selector.addEventListener('change', updateMap);
            btnBr.addEventListener('click', () => setScope('br'));
            btnPe.addEventListener('click', () => setScope('pe'));

            mapFrame.addEventListener('load', () => {{
                loading.classList.add('hidden');
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)