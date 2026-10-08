from typing import Optional
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from src.domain.use_cases.maps.get_map_prevalence_geojson_use_case import GetMapPrevalenceGeoJsonUseCase
from src.domain.processors.case_filters import CaseFilters

async def generate_prevalence_geojson(state_abbr: str, year: int, disease_code: str, source: str = "sinan", filters: Optional[CaseFilters] = None):

    try:
        result = await run_in_threadpool(
            GetMapPrevalenceGeoJsonUseCase().execute,
            state_abbr=state_abbr,
            year=year,
            disease_code=disease_code,
            source=source,
            filters=filters
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Não foi possível gerar o mapa interativo. Dados não encontrados para a combinação: {state_abbr}/{year}/{disease_code}"
                       + (f" com os filtros: {filters.describe()}" if filters and not filters.is_empty() else "") + "."
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno no servidor: {e}")
