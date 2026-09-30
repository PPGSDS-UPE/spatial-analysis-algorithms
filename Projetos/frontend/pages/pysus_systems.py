# pages/Pysus_Systems.py

import streamlit as st
from src.services.api_services import fetch_pysus_systems

st.set_page_config(layout="wide")
st.title("📚 PySUS Systems Explorer")
st.markdown("---")

systems_list = fetch_pysus_systems()

if systems_list:
    st.header("Available Information Systems")
    st.write("Click on a system to view its available variables and detailed query options.")

    cols = st.columns(3)
    
    for i, system in enumerate(systems_list):
        with cols[i % 3]: 
            with st.expander(f"**{system['code']}** - {system['name']}", expanded=False):
                st.write(f"System Code: **{system['code']}**")

                page_name = f"{system['code']}_Variables"
                
                if system['code'] == 'SINAN':
                    st.page_link(
                        "pages/sinan_disease_variables.py", 
                        label=f"Explore {system['code']} Variables", 
                        icon="➡️"
                        
                    )
                elif system['code'] == 'ESUS':
                    st.page_link(
                        "pages/esus_chagas_cronica.py",
                        label="Explore Doença de Chagas Crônica",
                        icon="➡️"
                    )
                elif system['code'] == 'CNES':
                
                    st.page_link(
                        "pages/cnes_medical_beds.py",  
                        label="Search Establishments", 
                        icon="🏥"
                    )
                    
                    
                    st.page_link(
                        "pages/cnes_professionals.py",  
                        label="Search Professionals", 
                        icon="🧑‍⚕️"
                    )
                    
                    
                    st.page_link(
                        "pages/cnes_equipment.py",      
                        label="Search Equipment", 
                        icon="🔬"
                    )

                else:
                    st.info("Query page not yet implemented for this system.")



else:
    st.warning("Could not load the list of PySUS systems.")