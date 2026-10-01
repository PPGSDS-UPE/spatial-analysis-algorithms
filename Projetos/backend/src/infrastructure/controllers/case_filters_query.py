# src/infrastructure/controllers/case_filters_query.py
"""
Parâmetros de query dos filtros de casos, compartilhados pelas rotas do SINAN, e-SUS e mapas.
Uso: filters: CaseFilters = Depends(case_filters_query)
"""
from enum import Enum
from typing import List, Optional

from fastapi import HTTPException, Query

from src.domain.processors.case_filters import CaseFilters


class RaceOption(str, Enum):
    branca = "branca"
    preta = "preta"
    amarela = "amarela"
    parda = "parda"
    indigena = "indigena"
    ignorado = "ignorado"


class SexOption(str, Enum):
    masculino = "masculino"
    feminino = "feminino"
    ignorado = "ignorado"


class EducationOption(str, Enum):
    nenhuma = "nenhuma"
    fundamental_incompleto = "fundamental_incompleto"
    fundamental_completo = "fundamental_completo"
    medio_incompleto = "medio_incompleto"
    medio_completo = "medio_completo"
    superior = "superior"
    ignorado = "ignorado"
    nao_se_aplica = "nao_se_aplica"


def case_filters_query(
    races: Optional[List[RaceOption]] = Query(None, description="Filtro de cor/raça (CS_RACA). Aceita vários valores."),
    sexes: Optional[List[SexOption]] = Query(None, description="Filtro de sexo (CS_SEXO). Aceita vários valores."),
    age_min: Optional[int] = Query(None, ge=0, le=130, description="Idade mínima em anos (NU_IDADE_N)."),
    age_max: Optional[int] = Query(None, ge=0, le=130, description="Idade máxima em anos (NU_IDADE_N)."),
    education_levels: Optional[List[EducationOption]] = Query(
        None,
        description="Nível de escolaridade (CS_ESCOL_N). Os códigos do SINAN são agrupados nas categorias do e-SUS."
    ),
) -> CaseFilters:
    if age_min is not None and age_max is not None and age_min > age_max:
        raise HTTPException(status_code=422, detail="age_min não pode ser maior que age_max.")

    return CaseFilters(
        races=[race.value for race in races] if races else None,
        sexes=[sex.value for sex in sexes] if sexes else None,
        age_min=age_min,
        age_max=age_max,
        education_levels=[level.value for level in education_levels] if education_levels else None,
    )
