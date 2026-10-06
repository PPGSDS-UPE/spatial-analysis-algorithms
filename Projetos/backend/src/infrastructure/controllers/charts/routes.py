from fastapi import APIRouter, Query, Depends

from .get_chart_prevalence_controller import generate_prevalence_chart
from src.infrastructure.controllers.maps.routes import CaseSource
from src.infrastructure.controllers.case_filters_query import case_filters_query
from src.domain.processors.case_filters import CaseFilters

charts_router = APIRouter()

@charts_router.get(
    "/{state_abbr}/{year}/prevalence",
    tags=["Gráficos"],
    summary="Casos e prevalência no estado para cada valor marcado nos filtros (cor/raça, sexo, escolaridade)"
)
async def get_chart_prevalence_route(
    state_abbr: str,
    year: int,
    disease_code: str = Query(..., description="Código do agravo (ex: 'CHAG' no SINAN, 'DCCR' no e-SUS).", example="CHAG"),
    source: CaseSource = Query(
        default=CaseSource.sinan,
        description="Fonte dos casos: 'sinan' ou 'esus'."
    ),
    filters: CaseFilters = Depends(case_filters_query)
):

    return await generate_prevalence_chart(
        state_abbr=state_abbr,
        year=year,
        disease_code=disease_code,
        source=source.value,
        filters=filters
    )
