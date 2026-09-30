from fastapi import APIRouter, Query
from typing import List, Optional

from .get_variables_esus_controller import get_variables_esus_controller
from .fetch_data_esus_controller import fetch_esus_data_controller

esus_router = APIRouter()

@esus_router.get(
    "/variables",
    tags=["PySUS - e-SUS Notifica"],
    summary="Lista as variáveis (doenças/agravos) disponíveis para o e-SUS Notifica"
)
def get_esus_variables_route():
    """Endpoint para obter as variáveis (doenças) disponíveis do e-SUS Notifica."""
    return get_variables_esus_controller()


@esus_router.get(
    "/fetch-data",
    tags=["PySUS - e-SUS Notifica"],
    summary="Busca dados do e-SUS Notifica e retorna um sumário de casos por município de residência"
)
async def get_esus_data_route(
    disease_code: str = Query("DCCR", description="Código do agravo. Ex: 'DCCR' para Doença de Chagas Crônica."),
    years: List[int] = Query(..., description="Lista de anos para a consulta. Ex: 2023,2024"),
    states: Optional[List[str]] = Query(None, description="Lista opcional de siglas de estados (UFs) para filtrar. Ex: PE,SP")
):
    """
    Endpoint para buscar um resumo de dados do e-SUS Notifica de forma não-bloqueante.
    """
    return await fetch_esus_data_controller(
        disease_code=disease_code,
        years=years,
        states=states
    )
