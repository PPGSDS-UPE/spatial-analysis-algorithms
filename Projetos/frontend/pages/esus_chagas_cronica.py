# pages/esus_chagas_cronica.py

import streamlit as st
from src.ui.components.esus_section import display_esus_query_section

# Configuração da página
st.set_page_config(layout="wide")

# Chama o componente para renderizar toda a lógica
display_esus_query_section()
