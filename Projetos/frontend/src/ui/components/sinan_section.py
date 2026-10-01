import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from io import BytesIO

# Imports dos serviços
from src.services.api_services import (
    fetch_sinan_variables,
    fetch_sinan_data,
    fetch_prevalence_map
)

from src.ui.constants import METRIC_OPTIONS_SINAN
from src.ui.components.case_filters_section import display_case_filters

def display_sinan_query_section():
    
    # ==============================================================================
    # 1. CARREGAMENTO INICIAL E VARIÁVEIS
    # ==============================================================================
    variables_data = fetch_sinan_variables()

    if not variables_data:
        st.error("Could not load SINAN variables from the API. Check the systems list.")
        return

    st.header("System SINAN")
    st.subheader(variables_data.get('description', 'Data Query'))

    # Processamento das variáveis
    variables_df = pd.DataFrame(variables_data['variables'])
    variables_df.columns = ["Code", "Disease/Condition Name"]
    disease_codes = dict(zip(variables_df['Disease/Condition Name'], variables_df['Code']))

    with st.expander("Available Variables (Diseases)"):
        st.dataframe(variables_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ==============================================================================
    # 2. FILTROS UNIFICADOS (Contexto Global)
    # ==============================================================================
    st.header("Parâmetros de Análise (Global)")
    st.markdown("Selecione a Doença, Ano e Estado abaixo para visualizar a Tabela ou o Mapa.")

    with st.container():
        col_global_1, col_global_2, col_global_3 = st.columns(3)
        
        with col_global_1:
            selected_disease_label = st.selectbox(
                "Select Disease/Condition",
                options=list(disease_codes.keys()),
                key="sinan_global_disease"
            )
            disease_code = disease_codes[selected_disease_label]
            #st.text_input("Disease Code", value=disease_code, disabled=True)
            
        with col_global_2:
            global_year = st.number_input(
                "Year",
                min_value=2000, max_value=2024, value=2022, 
                step=1, key="sinan_global_year"
            )
            
        with col_global_3:
            global_state = st.text_input(
                "State (UF)",
                value="PE", max_chars=2,
                help="Enter one UF (Ex: PE).",
                key="sinan_global_state"
            ).upper()

        case_filters, filters_description = display_case_filters("sinan")

    st.markdown("---")

    # ==============================================================================
    # 3. SISTEMA DE ABAS (DIVISÃO DA JANELA)
    # ==============================================================================
    # Aqui está a divisão exata que você pediu, ajustada para o contexto do SINAN
    tab_data, tab_map = st.tabs(["📊 Dados Detalhados (Tabela)", "🗺️ Mapa de Prevalência"])

    # --------------------------------------------------------------------------
    # ABA 1: TABELA DE DADOS
    # --------------------------------------------------------------------------
    with tab_data:
        st.subheader(f"Tabela: {selected_disease_label}")
        
        if st.button("Carregar Dados SINAN", key="btn_sinan_table"):
            
            year_list = [global_year] 
            state_list = [global_state] if global_state else None
            
            params: Dict[str, Any] = {
                "disease_code": disease_code,
                "years": year_list,
                "states": state_list,
                **case_filters
            }
            
            st.info(f"Buscando dados: {disease_code}, Ano: {global_year}, Estado: {global_state}"
                    + (f" | Filtros: {filters_description}" if filters_description else ""))

            with st.spinner("Fetching SINAN data..."):
                data = fetch_sinan_data(params) 
                
                # Lógica de extração de dados
                data_to_display = data.get('summary_by_municipality') if isinstance(data, dict) else None
                metadata = data.get('metadata', {}) if isinstance(data, dict) else {}
                
                total_records = metadata.get('total_records_found', 0)
                columns_list = metadata.get('columns', metadata.get('available_columns', [])) 

                if data_to_display and isinstance(data_to_display, list) and data_to_display:
                    
                    st.success(f"✅ {total_records} records found for {selected_disease_label}!")
                    st.dataframe(pd.DataFrame(data_to_display), use_container_width=True)
                    
                    if columns_list: 
                        with st.expander(f"Show {len(columns_list)} available data columns"):
                            columns_df = pd.DataFrame(columns_list, columns=["Column Name"])
                            st.dataframe(columns_df, use_container_width=True, hide_index=True)
                    
                elif total_records == 0:
                    st.info(f"ℹ️ No records found for {selected_disease_label} in {global_state} ({global_year}).")
                else:
                    st.error("Data fetching failed. Check API response.")

    # --------------------------------------------------------------------------
    # ABA 2: MAPA DE PREVALÊNCIA
    # --------------------------------------------------------------------------
    with tab_map:
        st.subheader("Visualização Espacial")
        
        col_metric, col_btn = st.columns([3, 1])
        
        with col_metric:
            metric_label_map = st.selectbox(
                "Metric to Map",
                options=list(METRIC_OPTIONS_SINAN.keys()),
                key="sinan_map_metric"
            )
        
        with col_btn:
            st.write("") # Espaçamento
            st.write("")
            generate_map = st.button("Gerar Mapa", key="btn_sinan_map")

        if generate_map:
            if not global_state or len(global_state) != 2:
                st.warning("⚠️ Para gerar o mapa, preencha o campo 'State (UF)' nos filtros acima.")
            else:
                metric_column_name = METRIC_OPTIONS_SINAN[metric_label_map]
                
                with st.spinner(f"Generating map for {selected_disease_label} ({metric_label_map}) in {global_state}..."):
                    
                    map_content = fetch_prevalence_map(
                        state_abbr=global_state,  # Reusa variável global
                        year=global_year,         # Reusa variável global
                        metric=metric_column_name,
                        disease_code=disease_code,
                        filters=case_filters
                    )

                    if map_content:
                        st.success("✅ Map generated successfully!")
                        st.image(
                            BytesIO(map_content),
                            caption=f"Map: {selected_disease_label} ({metric_label_map}) in {global_state}/{global_year}"
                                    + (f" — Filtros: {filters_description}" if filters_description else ""),
                            use_container_width=True
                        )
                    else:
                        st.error(f"Failed to generate map for {selected_disease_label}.")