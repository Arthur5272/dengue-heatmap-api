import folium
import json
import os
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.models import WeeklyReport, Territory


GEOJSON_BR_PATH = os.path.join("src", "static", "geo", "br_states.json")
GEOJSON_PE_PATH = os.path.join("src", "static", "geo", "pe_municipalities.json")


STATE_CODE_TO_UF = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE",
    29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP", 41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF"
}

async def generate_choropleth_map(db: AsyncSession, se: int) -> str:
    
    
    stmt = (
        select(
            Territory.state_code,
            func.avg(WeeklyReport.alert_level).label("avg_alert_level"),
            func.sum(WeeklyReport.reported_cases).label("total_cases")
        )
        .join(Territory, WeeklyReport.geocode == Territory.geocode)
        .where(WeeklyReport.se == se)
        .group_by(Territory.state_code)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    if not rows:
        return "<h3 style='text-align:center; margin-top: 50px;'>Sem dados para o Brasil nesta semana.</h3>"

    
    data = []
    for row in rows:
        uf_sigla = STATE_CODE_TO_UF.get(row.state_code)
        if uf_sigla:
            
            raw_avg = float(row.avg_alert_level or 1.0)
            
            data.append({
                "uf": uf_sigla,
                "Nível de Alerta Médio": round(max(1.0, min(4.0, raw_avg)), 1),
                "Total de Casos": row.total_cases
            })
    
    df_state_data = pd.DataFrame(data)

    
    try:
        with open(GEOJSON_BR_PATH, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
    except FileNotFoundError:
        return "<h3>Erro: GeoJSON do Brasil não encontrado em src/static/geo/br_states.json</h3>"

    
    m = folium.Map(
        location=[-15.7801, -47.9292],
        zoom_start=4,
        tiles=None,       
        zoom_control=False,
        attr="InfoDengue / IBGE"
    )

    
    choropleth = folium.Choropleth(
        geo_data=geo_data,
        name="Nível de Alerta (Médio)",
        data=df_state_data,
        columns=["uf", "Nível de Alerta Médio"],
        key_on="feature.properties.sigla",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.2,
        legend_name="Nível de Alerta Médio (1=Verde, 4=Vermelho)",
        bins=[1, 1.75, 2.5, 3.25, 4.01],
        highlight=True,
    ).add_to(m)

    
    df_indexed = df_state_data.set_index("uf")
    for feature in choropleth.geojson.data['features']:
        uf_sigla = feature['properties']['sigla']
        if uf_sigla in df_indexed.index:
            feature['properties']['alert'] = str(df_indexed.loc[uf_sigla, 'Nível de Alerta Médio'])
            feature['properties']['cases'] = str(df_indexed.loc[uf_sigla, 'Total de Casos'])
        else:
            feature['properties']['alert'] = 'N/A'
            feature['properties']['cases'] = 'N/A'

    folium.GeoJsonTooltip(
        fields=["sigla", "name", "alert", "cases"], 
        aliases=["Sigla:", "Estado:", "Nível Médio:", "Total Casos:"],
        localize=True,
        sticky=False,
        labels=True,
        style="background-color: #F0F0F0; border: 1px solid black; border-radius: 3px;"
    ).add_to(choropleth.geojson)

    return m.get_root().render()


async def generate_city_map(db: AsyncSession, se: int, state_code: int = 26) -> str:
    
    
    stmt = (
        select(
            WeeklyReport.geocode,
            Territory.name,
            WeeklyReport.alert_level,
            WeeklyReport.reported_cases
        )
        .join(Territory, WeeklyReport.geocode == Territory.geocode)
        .where(
            WeeklyReport.se == se,
            Territory.state_code == state_code
        )
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    if not rows:
        return "<h3 style='text-align:center; margin-top: 50px;'>Sem dados municipais para este período.</h3>"

    
    data = []
    for row in rows:
        data.append({
            "geocode": row.geocode,
            "Município": row.name,
            "Nível de Alerta": float(row.alert_level or 1.0), 
            "Casos": row.reported_cases
        })
    
    df_city_data = pd.DataFrame(data)

    
    try:
        with open(GEOJSON_PE_PATH, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
    except FileNotFoundError:
        return "<h3>Erro: GeoJSON de Pernambuco não encontrado em src/static/geo/pe_municipalities.json</h3>"

    
    m = folium.Map(
        location=[-8.4, -37.5], 
        zoom_start=7,
        tiles=None,
        zoom_control=False,
        attr="InfoDengue / IBGE"
    )

    
    choropleth = folium.Choropleth(
        geo_data=geo_data,
        name="Nível de Alerta",
        data=df_city_data,
        columns=["geocode", "Nível de Alerta"],
        key_on="feature.properties.id", 
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.2,
        legend_name="Nível de Alerta (1=Verde, 4=Vermelho)",
        bins=[1, 1.75, 2.5, 3.25, 4.01],
        highlight=True,
    ).add_to(m)

    
    df_indexed = df_city_data.set_index("geocode")
    for feature in choropleth.geojson.data['features']:
        geocode_geo = str(feature['properties']['id'])
        if geocode_geo in df_indexed.index:
            feature['properties']['alert'] = str(df_indexed.loc[geocode_geo, 'Nível de Alerta'])
            feature['properties']['cases'] = str(df_indexed.loc[geocode_geo, 'Casos'])
            feature['properties']['name'] = str(df_indexed.loc[geocode_geo, 'Município'])
        else:
            feature['properties']['alert'] = 'N/A'
            feature['properties']['cases'] = 'N/A'
            feature['properties']['name'] = 'Desconhecido'

    folium.GeoJsonTooltip(
        fields=["name", "alert", "cases"],
        aliases=["Cidade:", "Nível:", "Casos:"],
        localize=True,
        sticky=False,
        labels=True,
        style="background-color: #F0F0F0; border: 1px solid black; border-radius: 3px;"
    ).add_to(choropleth.geojson)

    return m.get_root().render()