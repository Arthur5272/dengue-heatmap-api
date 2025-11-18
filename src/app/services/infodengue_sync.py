# src/app/services/infodengue_sync.py

import asyncio
import logging
import httpx
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql import select, func

from app.models.models import Territory, WeeklyReport
from app.core.config import settings

logger = logging.getLogger(__name__)

# Limita o número de requisições HTTP simultâneas para não sobrecarregar a API
CONCURRENT_REQUESTS_LIMIT = 100

# URL base da API do InfoDengue
INFODENGUE_API_URL = "https://info.dengue.mat.br/api/alertcity/"

class SyncServiceError(Exception):
    """Exceção base para erros de sincronização do InfoDengue."""
    pass

class InfoDengueSyncService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS_LIMIT)
        # Criamos um cliente HTTP que será reutilizado
        self.client = httpx.AsyncClient(timeout=15.0)

    async def _get_territories_to_sync(self) -> List[str]:
        """Busca todos os geocodes da nossa tabela 'territories'."""
        logger.info("Buscando lista de geocodes (municípios) no banco...")
        stmt = select(Territory.geocode)
        result = await self.db.execute(stmt)
        geocodes = [row[0] for row in result.fetchall()]
        logger.info(f"Encontrados {len(geocodes)} municípios para sincronizar.")
        return geocodes

    def _calculate_sync_window(self) -> Dict[str, int]:
        """
        Calcula a janela de tempo padrão (últimas 8 semanas).
        """
        today = pd.Timestamp.now()
        # Semana epidemiológica atual
        current_ew = today.weekofyear
        current_ey = today.year
        
        # Data de 8 semanas atrás
        start_date = today - pd.DateOffset(weeks=8)
        start_ew = start_date.weekofyear
        start_ey = start_date.year

        # O InfoDengue usa 'ey' (ano) e 'ew' (semana)
        return {
            "ew_start": start_ew,
            "ey_start": start_ey,
            "ew_end": current_ew,
            "ey_end": current_ey,
        }

    async def _fetch_city_data(
        self, geocode: str, params: dict
    ) -> Tuple[str, List[dict]]:
        """
        Worker: Busca dados de UM município na API InfoDengue.
        É limitado pelo semáforo.
        """
        async with self.semaphore:
            try:
                # Adiciona o geocode e formato aos parâmetros
                full_params = params.copy()
                full_params["geocode"] = geocode
                full_params["disease"] = "dengue"
                full_params["format"] = "json"
                
                response = await self.client.get(INFODENGUE_API_URL, params=full_params)
                
                response.raise_for_status() # Lança erro para 4xx ou 5xx
                
                data = response.json()
                if isinstance(data, list):
                    return geocode, data
                return geocode, [] # Retorna lista vazia se a resposta não for uma lista

            except httpx.HTTPStatusError as e:
                # Erro 404 (Not Found) é comum para cidades sem dados, não é um erro fatal
                if e.response.status_code == 404:
                    logger.debug(f"Nenhum dado encontrado para geocode {geocode} (404).")
                else:
                    logger.warning(f"Erro HTTP ao buscar geocode {geocode}: {e}")
                return geocode, [] # Retorna sucesso (vazio)
            
            except httpx.RequestError as e:
                logger.error(f"Erro de rede/timeout ao buscar geocode {geocode}: {e}")
                raise SyncServiceError(f"Falha de rede: {geocode}") # Lança erro para retry
            
            except Exception as e:
                logger.error(f"Erro inesperado ao processar geocode {geocode}: {e}")
                return geocode, []

    def _parse_and_prepare_data(
        self, geocode: str, api_data: List[dict]
    ) -> List[dict]:
        """
        Converte a resposta JSON da API para o formato do nosso DB (WeeklyReport).
        """
        prepared_rows = []
        for week_data in api_data:
            try:
                # Converte o timestamp (em milissegundos) para data
                data_ini_se_ts = week_data.get("data_iniSE")
                if data_ini_se_ts:
                    data_ini_se = datetime.fromtimestamp(data_ini_se_ts / 1000).date()
                else:
                    continue # Pula registro se não tiver data

                row = {
                    "geocode": geocode,
                    "se": int(week_data["SE"]),
                    "data_ini_se": data_ini_se,
                    "reported_cases": week_data.get("casos"),
                    "estimated_cases": week_data.get("casos_est"),
                    "estimated_cases_min": week_data.get("casos_est_min"),
                    "estimated_cases_max": week_data.get("casos_est_max"),
                    "alert_level": week_data.get("nivel"),
                    "population": week_data.get("pop"),
                    "rt_value": week_data.get("Rt"),
                    # last_synced_at é definido pelo DB
                }
                prepared_rows.append(row)
            except Exception as e:
                logger.warning(f"Erro ao parsear dados da semana {week_data.get('SE')} para geocode {geocode}: {e}")
        
        return prepared_rows

    async def _upsert_data(self, data: List[dict]) -> dict:
        """
        Executa o 'UPSERT' (INSERT ... ON CONFLICT ...) no banco.
        """
        if not data:
            logger.info("Nenhum dado novo para inserir/atualizar.")
            return {"inserted": 0, "updated": 0}

        logger.info(f"Iniciando UPSERT para {len(data)} registros semanais...")

        stmt = pg_insert(WeeklyReport).values(data)
        
        # Define o que fazer em conflito na chave (geocode, se)
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=['geocode', 'se'],
            
            # Atualiza os campos
            set_={
                'data_ini_se': stmt.excluded.data_ini_se,
                'reported_cases': stmt.excluded.reported_cases,
                'estimated_cases': stmt.excluded.estimated_cases,
                'estimated_cases_min': stmt.excluded.estimated_cases_min,
                'estimated_cases_max': stmt.excluded.estimated_cases_max,
                'alert_level': stmt.excluded.alert_level,
                'population': stmt.excluded.population,
                'rt_value': stmt.excluded.rt_value,
                'last_synced_at': func.now()
            },
            
            # Otimização: Só atualiza se houver mudança real
            where=(
                (WeeklyReport.reported_cases != stmt.excluded.reported_cases) |
                (WeeklyReport.estimated_cases != stmt.excluded.estimated_cases) |
                (WeeklyReport.alert_level != stmt.excluded.alert_level)
            )
        )
        
        # Adiciona RETURNING para saber o que aconteceu
        final_stmt = on_conflict_stmt.returning(WeeklyReport.id, (WeeklyReport.estimated_cases_max != None).label("updated"))

        try:
            result = await self.db.execute(final_stmt)
            rows = result.fetchall()
            
            inserted_count = sum(1 for row in rows if not row.updated)
            updated_count = len(rows) - inserted_count

            logger.info(f"UPSERT concluído. Inseridos: {inserted_count}, Atualizados: {updated_count}.")
            return {"inserted": inserted_count, "updated": updated_count}
        
        except Exception as e:
            logger.error(f"Erro durante o UPSERT: {e}")
            raise SyncServiceError(f"Falha no UPSERT: {e}")

    async def run_full_sync(
        self,
        ew_start: Optional[int] = None,
        ey_start: Optional[int] = None,
        ew_end: Optional[int] = None,
        ey_end: Optional[int] = None
    ) -> dict:
        """
        Orquestra o processo completo de sincronização.
        Busca todos os municípios em paralelo.
        Processa o UPSERT em lotes.
        """
        logger.info("Iniciando sincronização completa do InfoDengue...")
        
        # --- NOVO: Define o tamanho do lote ---
        BATCH_SIZE = 1000  # Insere 1000 linhas por vez (10k parâmetros, bem seguro)
        
        # 1. Define a janela de tempo
        if not all([ew_start, ey_start, ew_end, ey_end]):
            logger.info("Janela de tempo não fornecida, calculando padrão (últimas 8 semanas)...")
            time_params = self._calculate_sync_window()
        else:
            time_params = {
                "ew_start": ew_start, "ey_start": ey_start,
                "ew_end": ew_end, "ey_end": ey_end
            }
        logger.info(f"Janela de sincronização: {time_params}")

        # 2. Busca os geocodes
        geocodes = await self._get_territories_to_sync()
        if not geocodes:
            logger.error("Nenhum território (geocode) encontrado no banco. Abortando sync.")
            return {}

        # 3. Prepara as tarefas de fetch (paralelas)
        tasks = [self._fetch_city_data(geo, time_params) for geo in geocodes]
        
        # --- LÓGICA DE LOTE ---
        all_data_to_upsert = [] # Buffer do lote
        total_inserted = 0
        total_updated = 0
        failed_geocodes = 0
        
        logger.info(f"Disparando {len(tasks)} requisições HTTP em paralelo (limite de {CONCURRENT_REQUESTS_LIMIT})...")
        
        # 4. Executa as tarefas
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Fetch concluído. Processando e fazendo UPSERT em lotes...")

        # 5. Processa os resultados e faz o UPSERT em lotes
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Uma task de fetch falhou: {result}")
                failed_geocodes += 1
            elif isinstance(result, tuple):
                geocode, api_data = result
                if api_data:
                    prepared_data = self._parse_and_prepare_data(geocode, api_data)
                    all_data_to_upsert.extend(prepared_data)
            
            # --- VERIFICA O LOTE ---
            # Se o buffer do lote atingir o tamanho, envia para o DB
            if len(all_data_to_upsert) >= BATCH_SIZE:
                logger.info(f"Processando lote de {len(all_data_to_upsert)} registros...")
                try:
                    batch_stats = await self._upsert_data(all_data_to_upsert)
                    total_inserted += batch_stats.get("inserted", 0)
                    total_updated += batch_stats.get("updated", 0)
                except Exception as e:
                    logger.error(f"Falha ao processar um lote: {e}")
                finally:
                    all_data_to_upsert = [] # Limpa o buffer do lote

        # 6. Processa o último lote (o que sobrou)
        if all_data_to_upsert:
            logger.info(f"Processando lote final de {len(all_data_to_upsert)} registros...")
            try:
                batch_stats = await self._upsert_data(all_data_to_upsert)
                total_inserted += batch_stats.get("inserted", 0)
                total_updated += batch_stats.get("updated", 0)
            except Exception as e:
                logger.error(f"Falha ao processar o lote final: {e}")

        # 7. Monta as estatísticas finais
        stats = {
            "inserted": total_inserted,
            "updated": total_updated,
            "geocodes_synced": len(geocodes) - failed_geocodes,
            "geocodes_failed": failed_geocodes
        }
        
        logger.info(f"Sincronização completa do InfoDengue finalizada. Stats: {stats}")
        
        # Fecha o cliente HTTP (movido para o final)
        await self.client.aclose()
        logger.info("Cliente HTTP fechado.")

        return stats