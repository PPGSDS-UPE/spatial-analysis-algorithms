import altair as alt
import pandas as pd
import streamlit as st
from typing import Any, Dict, Optional, Tuple

from src.ui.constants import METRIC_OPTIONS_SINAN, RACE_OPTIONS, SEX_OPTIONS, AGE_GROUP_OPTIONS, EDUCATION_OPTIONS

# Filtros comparáveis no gráfico: chave em 'series' na resposta da API -> (título, rótulos das categorias)
CHART_VARIABLES = {
    "race": ("Cor/Raça", {code: label for label, code in RACE_OPTIONS.items()}),
    "sex": ("Sexo", {code: label for label, code in SEX_OPTIONS.items()}),
    "age_group": ("Faixa etária", {code: label for label, code in AGE_GROUP_OPTIONS.items()}),
    "education": ("Escolaridade", {code: label for label, code in EDUCATION_OPTIONS.items()}),
}


def display_chart_options(key_prefix: str) -> Tuple[str, str, bool]:
    """Seletores de métrica (as mesmas do mapa) e tipo de gráfico + botão. Retorna (métrica, tipo, botão clicado)."""
    col_metric, col_type, col_btn = st.columns([2, 1, 1])
    with col_metric:
        metric_label = st.selectbox("Metric to Chart", options=list(METRIC_OPTIONS_SINAN.keys()),
                                    key=f"{key_prefix}_chart_metric")
    with col_type:
        chart_type = st.radio("Tipo de gráfico", options=["Barras", "Pizza"], horizontal=True,
                              key=f"{key_prefix}_chart_type")
    with col_btn:
        st.write("")  # Espaçamento
        st.write("")
        generate = st.button("Gerar Gráfico", key=f"btn_{key_prefix}_chart")
    return metric_label, chart_type, generate


def _bar_chart(df: pd.DataFrame, title: str, metric_label: str, value_format: str) -> alt.Chart:
    base = alt.Chart(df, title=title).encode(
        x=alt.X("Categoria:N", sort=list(df["Categoria"]), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Valor:Q", title=metric_label),
        tooltip=["Categoria", alt.Tooltip("Valor:Q", title=metric_label, format=value_format),
                 alt.Tooltip("Percentual:Q", format=".1%")],
    )
    bars = base.mark_bar()
    labels = base.mark_text(dy=-8).encode(text=alt.Text("Valor:Q", format=value_format))
    return bars + labels


def _pie_chart(df: pd.DataFrame, title: str, metric_label: str, value_format: str) -> alt.Chart:
    base = alt.Chart(df, title=title).encode(
        theta=alt.Theta("Valor:Q", stack=True),
        order=alt.Order("Valor:Q", sort="descending"),
        tooltip=["Categoria", alt.Tooltip("Valor:Q", title=metric_label, format=value_format),
                 alt.Tooltip("Percentual:Q", format=".1%")],
    )
    slices = base.mark_arc(outerRadius=140).encode(
        color=alt.Color("Categoria:N", sort=list(df["Categoria"]), legend=alt.Legend(title=None))
    )
    # Rótulos sem a cor da fatia, para ficarem legíveis também nas cores claras
    labels = base.mark_text(radius=165, size=12).encode(text=alt.Text("Valor:Q", format=value_format))
    return slices + labels


def display_prevalence_charts(chart_data: Optional[Dict[str, Any]], metric_label: str,
                              chart_type: str, caption: str = "") -> None:
    """Um gráfico por filtro com valores marcados, comparando a métrica escolhida entre esses valores."""
    metric_column = METRIC_OPTIONS_SINAN[metric_label]
    value_format = ",.0f" if metric_column == "total_cases" else ",.2f"

    st.metric(f"{metric_label} — todos os filtros", format(chart_data.get(metric_column, 0), value_format))

    series = chart_data.get("series") or {}
    if not series:
        st.warning("⚠️ Marque ao menos um valor em Cor/Raça, Sexo, Faixa etária ou Escolaridade nos filtros de casos "
                   "para comparar os grupos no gráfico.")
        return

    st.success("✅ Chart generated successfully!")
    chart_fn = _bar_chart if chart_type == "Barras" else _pie_chart

    for variable, items in series.items():
        variable_name, labels = CHART_VARIABLES[variable]
        df = pd.DataFrame([
            {"Categoria": labels.get(item["category"], item["category"]), "Valor": item[metric_column]}
            for item in items
        ])
        total = df["Valor"].sum()
        df["Percentual"] = df["Valor"] / total if total else 0.0

        st.altair_chart(chart_fn(df, f"{metric_label} por {variable_name.lower()}", metric_label, value_format),
                        use_container_width=True)

    if caption:
        st.caption(caption)
    if metric_column != "total_cases":
        st.caption(f"Denominador: população total do estado ({chart_data.get('population', 0):,} hab.), "
                   "como no mapa. Os demais filtros marcados restringem os casos de cada grupo.")
