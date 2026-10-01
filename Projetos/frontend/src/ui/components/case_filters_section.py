import streamlit as st
from typing import Dict, Any, List, Tuple

from src.ui.constants import RACE_OPTIONS, SEX_OPTIONS, EDUCATION_OPTIONS

AGE_LIMIT = 120


def display_case_filters(key_prefix: str) -> Tuple[Dict[str, Any], str]:
    """
    Renderiza os filtros de casos (cor/raça, sexo, faixa etária e escolaridade).

    Retorna (params, descricao): 'params' contém apenas os filtros ativos, no formato
    esperado pela API; 'descricao' é um resumo legível para legendas.
    """
    with st.expander("🔎 Filtros de casos (cor/raça, sexo, idade, escolaridade)"):
        col_race, col_sex = st.columns(2)

        with col_race:
            selected_races = st.multiselect(
                "Cor/Raça",
                options=list(RACE_OPTIONS.keys()),
                key=f"{key_prefix}_filter_races",
                help="Vazio = todas."
            )

        with col_sex:
            selected_sexes = st.multiselect(
                "Sexo",
                options=list(SEX_OPTIONS.keys()),
                key=f"{key_prefix}_filter_sexes",
                help="Vazio = todos."
            )

        age_min, age_max = st.slider(
            "Faixa etária (anos)",
            min_value=0, max_value=AGE_LIMIT, value=(0, AGE_LIMIT),
            key=f"{key_prefix}_filter_age",
            help="Menores de 1 ano contam como 0. Mantenha 0-120 para não filtrar."
        )

        selected_education = st.multiselect(
            "Escolaridade",
            options=list(EDUCATION_OPTIONS.keys()),
            key=f"{key_prefix}_filter_education",
            help="Vazio = todas. No SINAN, as séries do fundamental e o superior incompleto/completo "
                 "são agrupados nestas categorias. Registros sem escolaridade informada são excluídos ao filtrar."
        )

        st.caption(
            "Com filtros, a taxa de prevalência usa a população total do município como denominador "
            "(não há população por cor/raça, sexo, idade e escolaridade por município em todos os anos)."
        )

    params: Dict[str, Any] = {}
    description_parts: List[str] = []

    if selected_races:
        params["races"] = [RACE_OPTIONS[label] for label in selected_races]
        description_parts.append(", ".join(selected_races))

    if selected_sexes:
        params["sexes"] = [SEX_OPTIONS[label] for label in selected_sexes]
        description_parts.append(", ".join(selected_sexes))

    if age_min > 0:
        params["age_min"] = age_min
    if age_max < AGE_LIMIT:
        params["age_max"] = age_max
    if age_min > 0 or age_max < AGE_LIMIT:
        description_parts.append(f"{age_min}-{age_max} anos" if age_max < AGE_LIMIT else f"{age_min}+ anos")

    if selected_education:
        params["education_levels"] = [EDUCATION_OPTIONS[label] for label in selected_education]
        description_parts.append("Escolaridade: " + ", ".join(selected_education))

    return params, " | ".join(description_parts)
