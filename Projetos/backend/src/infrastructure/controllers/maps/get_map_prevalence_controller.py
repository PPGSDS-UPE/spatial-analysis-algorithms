from typing import Optional
from fastapi import HTTPException
from fastapi.responses import Response 
from src.domain.use_cases.maps.get_map_prevalence_use_case import GetMapPrevalenceUseCase
from src.domain.processors.case_filters import CaseFilters

def generate_prevalence_map(state_abbr: str, year: int, metric: str, disease_code: str, source: str = "sinan", filters: Optional[CaseFilters] = None):

    try:
        use_case = GetMapPrevalenceUseCase()

        image_buffer = use_case.execute(
            state_abbr=state_abbr,
            year=year,
            metric_column=metric,
            disease_code=disease_code,
            source=source,
            filters=filters
        )

        if image_buffer is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Não foi possível gerar o mapa. Dados não encontrados para a combinação: {state_abbr}/{year}/{disease_code}"
                       + (f" com os filtros: {filters.describe()}" if filters and not filters.is_empty() else "") + "."
            )
        
        return Response(content=image_buffer.read(), media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno no servidor: {e}")