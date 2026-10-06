# src/infrastructure/controllers/case_filters_query.py
"""
Parâmetros de query dos filtros de casos, compartilhados pelas rotas do SINAN, e-SUS e mapas.
Uso: filters: CaseFilters = Depends(case_filters_query)
"""
from enum import Enum
from typing import List, Optional

from fastapi import Query

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


class AgeGroupOption(str, Enum):
    de_0_a_14 = "0_14"
    de_15_a_29 = "15_29"
    de_30_a_39 = "30_39"
    de_40_a_49 = "40_49"
    de_50_a_59 = "50_59"
    de_60_a_69 = "60_69"
    de_70_a_79 = "70_79"
    de_80_mais = "80_mais"


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
    age_groups: Optional[List[AgeGroupOption]] = Query(
        None,
        description="Faixas etárias (NU_IDADE_N). Aceita vários valores; filtra pela união das faixas."
    ),
    education_levels: Optional[List[EducationOption]] = Query(
        None,
        description="Nível de escolaridade (CS_ESCOL_N). Os códigos do SINAN são agrupados nas categorias do e-SUS."
    ),
) -> CaseFilters:
    return CaseFilters(
        races=[race.value for race in races] if races else None,
        sexes=[sex.value for sex in sexes] if sexes else None,
        age_groups=[group.value for group in age_groups] if age_groups else None,
        education_levels=[level.value for level in education_levels] if education_levels else None,
    )
