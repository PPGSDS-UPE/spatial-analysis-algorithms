from fastapi import APIRouter, Query, Depends
from typing import List, Optional

# Os imports dos controllers continuam os mesmos
from .get_variables_sinan_controller import get_variables_sinan_controller
from .fetch_data_sinan_controller import fetch_sinan_data_controller
from src.infrastructure.controllers.case_filters_query import case_filters_query
from src.domain.processors.case_filters import CaseFilters

sinan_router = APIRouter()

# --- Rota 1: Listar Variáveis (Nenhuma mudança aqui) ---
@sinan_router.get(
    "/variables",
    tags=["PySUS - SINAN"],
    summary="Lista as variáveis (doenças/agravos) disponíveis para o SINAN"
)
def get_sinan_variables_route():
    """Endpoint para obter as variáveis (doenças) disponíveis do SINAN."""
    return get_variables_sinan_controller()


# --- Rota 2: Buscar Resumo (COM A MUDANÇA) ---
@sinan_router.get(
    "/fetch-data",
    tags=["PySUS - SINAN"],
    summary="Busca dados do SINAN e retorna um sumário de casos por município"
)
# 1. A função da rota agora é 'async def'
async def get_sinan_data_route(
    disease_code: str = Query(..., description="Código do agravo (doença). Ex: 'DENG' para Dengue.", example="DENG"),
    years: List[int] = Query(..., description="Lista de anos para a consulta. Ex: 2022,2023", example=[2023]),
    states: Optional[List[str]] = Query(None, description="Lista opcional de siglas de estados (UFs) para filtrar. Ex: PE,SP", example=["PE"]),
    filters: CaseFilters = Depends(case_filters_query)
):
    """
    Endpoint para buscar um resumo de dados do SINAN de forma não-bloqueante.
    """
    # 2. A chamada ao controller agora usa 'await'
    return await fetch_sinan_data_controller(
        disease_code=disease_code,
        years=years,
        states=states,
        filters=filters
    )