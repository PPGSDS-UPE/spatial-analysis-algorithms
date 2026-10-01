# Salve este código como (por exemplo): src/ui/sidra_component.py

import streamlit as st
import pandas as pd
import re
from typing import Optional, Dict, Any, List

# Certifique-se que o 'src' está no path do Python
from src.services.api_services import (
     fetch_table_list, 
     fetch_table_metadata, 
     fetch_sidra_data
)

def display_sidra_query_component():
    """
    Exibe todo o componente de consulta SIDRA (Seção 1 e 2)
    e gerencia o estado da aplicação.
    """

    # --- INICIALIZAÇÃO DO ESTADO ---
    # Garante que 'metadata' exista no session_state
    if 'metadata' not in st.session_state:
        st.session_state.metadata = None

    # --- FUNÇÕES INTERNAS (HELPERS) ---
    # Estas funções são "escondidas" dentro do componente principal
    
    def _fetch_and_store_metadata():
        """
        Função de callback. Chamada QUANDO o selectbox muda.
        Ela busca os metadados e os armazena no session_state.
        """
        selected_table_str = st.session_state.get("sidra_table_select") 
        
        if selected_table_str:
            selected_id = selected_table_str.split(" - ")[0]
            with st.spinner(f"Fetching metadata for table {selected_id}..."):
                st.session_state.metadata = fetch_table_metadata(int(selected_id))
        else:
            st.session_state.metadata = None

    def _display_table_selection_section():
        """ SECTION 1: Table Selection """
        st.header("1. Select the Table")
        
        # fetch_table_list já é cacheada (apenas em caso de sucesso)
        formatted_table_list = fetch_table_list()

        if formatted_table_list:
            table_options = [f"{t['id']} - {t['name']}" for t in formatted_table_list]

            st.selectbox(
                label="Choose a table to inspect and query",
                options=table_options,
                index=None,
                placeholder="Type the code or name of the table to search...",
                key="sidra_table_select",
                on_change=_fetch_and_store_metadata
            )
        else:
            st.warning("Could not load the table list from the API.")
            st.session_state.metadata = None 

    def _display_sidra_query_section(metadata: Optional[Dict[str, Any]]):
        """ SECTION 2: Data Query """
        st.divider()
        st.header("2. Query General SIDRA Data")

        if metadata is None:
            st.info("Select a table in section 1 to enable the data query form.")
            return

        st.info(f"Query parameters for the table: **{metadata.get('tabela_nome')}**") 

        level_options = {item['nome']: item['id'].replace('N', '') for item in metadata.get('niveis_territoriais', [])}
        variable_options = {item['nome']: item['id'] for item in metadata.get('variaveis', [])}

        period_options = ["last", "all"]
        available_period = metadata.get('periodo', {}).get('disponibilidade')
        if isinstance(available_period, list):
            period_options.extend(sorted(available_period, reverse=True))
        elif isinstance(available_period, str):
            found_years = re.findall(r'\b\d{4}\b', available_period)
            if found_years:
                period_options.extend(sorted(list(set(found_years)), reverse=True))

        with st.form("query_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.text_input("Table Code", value=metadata.get('tabela_id'), disabled=True)
                selected_level_label = st.selectbox("Territorial Level*", options=list(level_options.keys()), key="general_level") 
                ibge_code_input = st.text_input("Territorial Code", value="all", help="Use 'all' or a UF code (ex: 26 for PE)", key="general_ibge_code") 

            with col2:
                selected_variable_labels = st.multiselect("Variable(s) (optional)", options=list(variable_options.keys()), key="general_var") 
                period_input = st.selectbox("Period*", options=period_options, key="general_period") 

            submitted = st.form_submit_button("Fetch Data")

        if submitted:
            territorial_level_code = level_options[selected_level_label]
            variable_codes = [variable_options[label] for label in selected_variable_labels]
            variable_param = ",".join(variable_codes) if variable_codes else None

            params = {
                "table_code": metadata.get('tabela_id'),
                "territorial_level": territorial_level_code,
                "ibge_territorial_code": ibge_code_input,
                "variable": variable_param,
                "period": period_input,
            }
            
            params = {k: v for k, v in params.items() if v}

            with st.spinner("Querying the Sidra API..."):
                data = fetch_sidra_data(params) 
                if data:
                    st.success(f"{len(data)} records found!")
                    st.dataframe(pd.DataFrame(data))
                else:
                    st.warning("No data found for this query.")

    # --- LÓGICA DE EXECUÇÃO ---
    # Chama as funções internas na ordem correta
    
    _display_table_selection_section()
    _display_sidra_query_section(st.session_state.metadata)