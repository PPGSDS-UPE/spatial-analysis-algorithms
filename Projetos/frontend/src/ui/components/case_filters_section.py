import streamlit as st
from typing import Dict, Any, List, Tuple

from src.ui.constants import RACE_OPTIONS, SEX_OPTIONS, AGE_GROUP_OPTIONS, EDUCATION_OPTIONS


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

        selected_age_groups = st.multiselect(
            "Faixa etária",
            options=list(AGE_GROUP_OPTIONS.keys()),
            key=f"{key_prefix}_filter_age_groups",
            help="Vazio = todas. Marcando várias, a tabela e o mapa usam a união das faixas "
                 "e o gráfico compara cada faixa. Menores de 1 ano entram em <15."
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

    if selected_age_groups:
        # Ordem crescente, independentemente da ordem em que as faixas foram marcadas
        ordered_age_groups = [label for label in AGE_GROUP_OPTIONS if label in selected_age_groups]
        params["age_groups"] = [AGE_GROUP_OPTIONS[label] for label in ordered_age_groups]
        description_parts.append(", ".join(ordered_age_groups))

    if selected_education:
        params["education_levels"] = [EDUCATION_OPTIONS[label] for label in selected_education]
        description_parts.append("Escolaridade: " + ", ".join(selected_education))

    return params, " | ".join(description_parts)
