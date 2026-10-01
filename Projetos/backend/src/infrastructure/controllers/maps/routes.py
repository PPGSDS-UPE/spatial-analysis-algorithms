from fastapi import APIRouter, Query, Depends
from enum import Enum

from .get_map_birthrate_controller import generate_birth_rate_map
from .get_map_state_controller import generate_state_layers_map
# 1. IMPORTAR O NOVO CONTROLLER
from .get_map_prevalence_controller import generate_prevalence_map
from src.infrastructure.controllers.case_filters_query import case_filters_query
from src.domain.processors.case_filters import CaseFilters

class BirthRateMetric(str, Enum):
    total_births = "total_births"
    birth_rate_per_1000 = "birth_rate_per_1000"
    births_mother_under20 = "births_mother_under20"
    births_mother_20to29 = "births_mother_20to29"
    births_mother_30to39 = "births_mother_30to39"
    births_mother_40plus = "births_mother_40plus"

# 2. ADICIONAR O NOVO ENUM PARA AS MÉTRICAS DE PREVALÊNCIA
class PrevalenceMetric(str, Enum):
    total_cases = "total_cases"
    # O nome da métrica deve bater com o definido no 'GetMapPrevalenceUseCase'
    prevalence_per_100000 = "prevalence_per_100000"

class CaseSource(str, Enum):
    sinan = "sinan"
    esus = "esus"

maps_router = APIRouter()

@maps_router.get(
    "/{state_abbr}/{year}/birth-rate", 
    tags=["Mapas"],
    summary="Gera um mapa coroplético de natalidade para um estado e ano"
)
def get_map_birthrate_route(
    state_abbr: str, 
    year: int,
    group_code: str = Query(
        default="DN", 
        description="Código do grupo de dados do SINASC (ex: 'DN' para Declaração de Nascido Vivo).",
        example="DN"
    ),
    metric: BirthRateMetric = Query(
        default=BirthRateMetric.birth_rate_per_1000,
        description="A métrica de natalidade a ser exibida no mapa."
    )
):
    
    return generate_birth_rate_map(
        state_abbr=state_abbr, 
        year=year, 
        metric=metric.value,
        group_code=group_code 
    )

# 3. ADICIONAR A NOVA ROTA DE PREVALÊNCIA
@maps_router.get(
    "/{state_abbr}/{year}/prevalence", 
    tags=["Mapas"],
    summary="Gera um mapa coroplético de prevalência para um estado, ano e agravo"
)
def get_map_prevalence_route(
    state_abbr: str, 
    year: int,
    disease_code: str = Query(
        ..., # ... torna o parâmetro OBRIGATÓRIO
        description="Código do agravo do SINAN (ex: 'B58' para Toxoplasmose).",
        example="B58"
    ),
    metric: PrevalenceMetric = Query(
        default=PrevalenceMetric.prevalence_per_100000,
        description="A métrica de prevalência a ser exibida no mapa."
    ),
    source: CaseSource = Query(
        default=CaseSource.sinan,
        description="Fonte dos casos: 'sinan' ou 'esus' (e-SUS Notifica, ex.: 'DCCR' para Chagas Crônica)."
    ),
    filters: CaseFilters = Depends(case_filters_query)
):

    return generate_prevalence_map(
        state_abbr=state_abbr,
        year=year,
        metric=metric.value,
        disease_code=disease_code,
        source=source.value,
        filters=filters
    )

@maps_router.get(
    "/{state_abbr}/{year}/regional-layers", 
    tags=["Mapas"], 
    summary="Gera o mapa de divisões regionais de um estado sobre o contexto nacional (Brasil)."
)
def get_map_state_layers_route(
    state_abbr: str, 
    year: int,
    show_municipalities: bool = Query(
        default=False, 
        description="Incluir a camada de municípios.",
        example=False
    ),
    show_immediate: bool = Query(
        default=False,
        description="Incluir a camada de Regiões Geográficas Imediatas.",
        example=False
    ),
    show_intermediate: bool = Query(
        default=False,
        description="Incluir a camada de Regiões Geográficas Intermediárias.",
        example=False
    ),
    use_zoom: bool = Query(
        default=False,
        description="Incluir zoom nos mapas.",
        example=False
    )
):
    
    return generate_state_layers_map(
        state_abbr=state_abbr, 
        year=year, 
        show_municipalities=show_municipalities,
        show_immediate=show_immediate,
        show_intermediate=show_intermediate,
        use_zoom=use_zoom,
    )