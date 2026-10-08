import math
from io import BytesIO
from typing import Dict, Any, List, Tuple

import pydeck as pdk
import streamlit as st

from src.services.api_services import fetch_prevalence_map, fetch_prevalence_geojson
from src.ui.constants import METRIC_OPTIONS_SINAN

MAP_TYPE_INTERACTIVE = "🖱️ Interativo (com tooltip)"
MAP_TYPE_PNG = "🖼️ Imagem (PNG)"

# Escala azul (mesma família de cores do mapa PNG). A 1ª cor é reservada para municípios sem casos.
ZERO_COLOR = [247, 251, 255]
CLASS_COLORS = [[198, 219, 239], [107, 174, 214], [33, 113, 181], [8, 48, 107]]
LINE_COLOR = [90, 90, 90]
NO_DATA_LABEL = "Sem casos"

MAP_HEIGHT_PX = 560
MAP_WIDTH_PX = 900


def _format_number(value: float, decimals: int = 0) -> str:
    """Formato pt-BR: 1.234.567,89"""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def _class_breaks(values: List[float]) -> List[float]:
    """Quantis dos valores positivos (até 4 classes), sem limites repetidos."""
    positive = sorted(v for v in values if v > 0)
    if not positive:
        return []
    breaks = []
    for i in range(1, len(CLASS_COLORS) + 1):
        index = min(len(positive) - 1, math.ceil(i * len(positive) / len(CLASS_COLORS)) - 1)
        value = positive[index]
        if not breaks or value > breaks[-1]:
            breaks.append(value)
    return breaks


def _color_for(value: float, breaks: List[float]) -> List[int]:
    if value <= 0 or not breaks:
        return ZERO_COLOR
    for color, upper in zip(CLASS_COLORS, breaks):
        if value <= upper:
            return color
    return CLASS_COLORS[len(breaks) - 1]


def _prepare_geojson(geojson: Dict[str, Any], metric_column: str) -> Tuple[Dict[str, Any], List[Tuple[List[int], str]]]:
    """Adiciona cor e textos formatados a cada município; retorna também os itens da legenda."""
    decimals = 0 if metric_column == "total_cases" else 2
    values = [float(f["properties"].get(metric_column) or 0) for f in geojson["features"]]
    breaks = _class_breaks(values)

    for feature, value in zip(geojson["features"], values):
        props = feature["properties"]
        props["fill_color"] = _color_for(value, breaks)
        props["cases_fmt"] = _format_number(props.get("total_cases") or 0)
        props["population_fmt"] = _format_number(props.get("population") or 0)
        props["rate_fmt"] = _format_number(props.get("prevalence_per_100000") or 0, 2)

    legend = [(ZERO_COLOR, NO_DATA_LABEL)]
    lower = 0.0
    for color, upper in zip(CLASS_COLORS, breaks):
        if decimals == 0:
            label = f"{_format_number(math.floor(lower) + 1)} – {_format_number(upper)}"
        else:
            lower_label = "> 0" if lower == 0 else _format_number(lower, decimals)
            label = f"{lower_label} – {_format_number(upper, decimals)}"
        legend.append((color, label))
        lower = upper
    return geojson, legend


def _view_state(bounds: List[float]) -> pdk.ViewState:
    min_lon, min_lat, max_lon, max_lat = bounds
    lon_span = max(max_lon - min_lon, 0.01)
    lat_span = max(max_lat - min_lat, 0.01)
    # Zoom que faz os limites caberem no quadro (mundo = 512 px * 2^zoom)
    zoom = math.log2(min(MAP_WIDTH_PX * 360 / (512 * lon_span), MAP_HEIGHT_PX * 360 / (512 * lat_span))) - 0.3
    return pdk.ViewState(
        longitude=(min_lon + max_lon) / 2,
        latitude=(min_lat + max_lat) / 2,
        zoom=zoom,
        pitch=0,
    )


def _render_legend(legend: List[Tuple[List[int], str]], metric_label: str) -> None:
    items = "".join(
        f'<span style="display:inline-flex;align-items:center;margin-right:14px;">'
        f'<span style="width:16px;height:16px;border:1px solid #888;margin-right:6px;'
        f'background:rgb({c[0]},{c[1]},{c[2]});"></span>{label}</span>'
        for c, label in legend
    )
    st.markdown(f"<div style='font-size:0.9em;'><b>{metric_label}:</b> {items}</div>", unsafe_allow_html=True)


def _display_interactive_map(data: Dict[str, Any], metric_column: str, metric_label: str) -> None:
    metadata = data["metadata"]
    geojson, legend = _prepare_geojson(data["geojson"], metric_column)

    col_cases, col_rate, col_pop = st.columns(3)
    col_cases.metric("Casos no estado", _format_number(metadata["total_cases"]))
    col_rate.metric("Taxa no estado (por 100 mil hab.)", _format_number(metadata["prevalence_per_100000"], 2))
    col_pop.metric("População", _format_number(metadata["population"]))

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson,
        pickable=True,
        stroked=True,
        filled=True,
        auto_highlight=True,
        highlight_color=[255, 200, 0, 180],
        get_fill_color="properties.fill_color",
        get_line_color=LINE_COLOR,
        line_width_min_pixels=0.5,
    )

    tooltip = {
        "html": (
            "<b>{name_muni}</b><br/>"
            "Casos: <b>{cases_fmt}</b><br/>"
            "Taxa: <b>{rate_fmt}</b> por 100 mil hab.<br/>"
            "População: {population_fmt}"
        ),
        "style": {"backgroundColor": "white", "color": "#222", "fontSize": "13px",
                  "border": "1px solid #999", "padding": "6px"},
    }

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=_view_state(metadata["bounds"]),
        map_provider="carto",
        map_style="light",
        tooltip=tooltip,
    )
    st.pydeck_chart(deck, use_container_width=True, height=MAP_HEIGHT_PX)
    _render_legend(legend, metric_label)


def display_prevalence_map_tab(
    key_prefix: str,
    source: str,
    disease_code: str,
    disease_label: str,
    state: str,
    year: int,
    case_filters: Dict[str, Any],
    filters_description: str,
) -> None:
    """Aba de mapa de prevalência compartilhada pelas páginas do SINAN e do e-SUS."""
    st.subheader("Visualização Espacial")

    col_metric, col_type, col_btn = st.columns([2, 2, 1])

    with col_metric:
        metric_label_map = st.selectbox(
            "Metric to Map",
            options=list(METRIC_OPTIONS_SINAN.keys()),
            key=f"{key_prefix}_map_metric"
        )

    with col_type:
        map_type = st.radio(
            "Tipo de mapa",
            options=[MAP_TYPE_INTERACTIVE, MAP_TYPE_PNG],
            key=f"{key_prefix}_map_type",
            horizontal=True,
        )

    with col_btn:
        st.write("")  # Espaçamento
        st.write("")
        generate_map = st.button("Gerar Mapa", key=f"btn_{key_prefix}_map")

    if not generate_map:
        return

    if not state or len(state) != 2:
        st.warning("⚠️ Para gerar o mapa, preencha o campo 'State (UF)' nos filtros acima.")
        return

    metric_column_name = METRIC_OPTIONS_SINAN[metric_label_map]
    caption = (f"Map: {disease_label} ({metric_label_map}) in {state}/{year}"
               + (f" — Filtros: {filters_description}" if filters_description else ""))

    with st.spinner(f"Generating map for {disease_label} ({metric_label_map}) in {state}..."):

        if map_type == MAP_TYPE_INTERACTIVE:
            data = fetch_prevalence_geojson(
                state_abbr=state,
                year=year,
                disease_code=disease_code,
                source=source,
                filters=case_filters
            )
            if data:
                st.success("✅ Map generated successfully! Passe o mouse sobre um município para ver os detalhes.")
                _display_interactive_map(data, metric_column_name, metric_label_map)
                st.caption(caption + ". Com filtros, a taxa usa a população total do município.")
            else:
                st.error(f"Failed to generate map for {disease_label}.")

        else:
            map_content = fetch_prevalence_map(
                state_abbr=state,
                year=year,
                metric=metric_column_name,
                disease_code=disease_code,
                source=source,
                filters=case_filters
            )
            if map_content:
                st.success("✅ Map generated successfully!")
                st.image(BytesIO(map_content), caption=caption, use_container_width=True)
            else:
                st.error(f"Failed to generate map for {disease_label}.")
