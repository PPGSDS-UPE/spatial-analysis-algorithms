# src/services/api_service.py

import functools
import streamlit as st
import requests
from typing import Optional, Dict, Any, List
from src.ui.constants import API_URL


def cache_success(func):
    """
    Igual ao @st.cache_data, mas não guarda falhas: quando a função retorna None
    (erro de conexão ou da API), a entrada é descartada e a próxima chamada tenta de novo.
    """
    cached_func = st.cache_data(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = cached_func(*args, **kwargs)
        if result is None:
            cached_func.clear(*args, **kwargs)
        return result

    wrapper.clear = cached_func.clear
    return wrapper

@cache_success
def fetch_table_list() -> Optional[List[Dict[str, Any]]]:
    try:
        response = requests.get(f"{API_URL}/sidra/tables")
        response.raise_for_status()

        raw_data = response.json()

        final_table_list = []
        for research in raw_data:
            if "agregados" in research and isinstance(research["agregados"], list):
                for table in research["agregados"]:
                    final_table_list.append({
                        "id": table["id"],
                        "name": table["nome"] 
                    })

        return sorted(final_table_list, key=lambda x: int(x['id']))
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API to fetch tables: {e}")
        return None

@cache_success
def fetch_table_metadata(table_id: int) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{API_URL}/sidra/tables/{table_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None
    
@cache_success
def fetch_sidra_data(params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    try:
        response = requests.get(f"{API_URL}/sidra/tables/fetch-specific", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error("Error fetching data from the API.")
        if e.response is not None:
            try:
                st.json(e.response.json())
            except:
                st.write(f"Error details: {e}")
        return None
    
@cache_success
def fetch_birthrate_map(state_abbr: str, year: int, metric_column: str) -> Optional[bytes]:
    base_url = f"{API_URL}/maps/{state_abbr}/{year}/birth-rate"

    params = {
        "metric": metric_column,
        "group_code": "DN" 
    }

    st.info(f"Calling API: {base_url} with metric: {metric_column}")

    try:
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error generating map in the API.")
        if e.response is not None:
              try:
                  error_detail = e.response.json().get("detail", e.response.text)
                  st.write(f"Server error details: {error_detail}")
              except:
                  st.write(f"Network error details: {e}")
        return None
    
@cache_success
def fetch_pysus_systems() -> Optional[List[Dict[str, Any]]]:
    """Fetches the list of all supported PySUS systems from the API."""
    try:
        response = requests.get(f"{API_URL}/pysus/systems/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API to fetch PySUS systems: {e}")
        return None

@cache_success
def fetch_sinan_variables() -> Optional[Dict[str, Any]]:
    """Fetches the list of variables (diseases/conditions) available for SINAN."""
    try:
        response = requests.get(f"{API_URL}/pysus/sinan/variables")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API to fetch SINAN variables: {e}")
        return None
    
@cache_success
def fetch_sinan_data(params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Requests a summary of SINAN data from the API based on disease, year, and state."""
    
    # A API espera os anos e estados como listas, que já estão no dicionário 'params'
    base_url = f"{API_URL}/pysus/sinan/fetch-data"

    st.info(f"Sending query to API: {base_url} with parameters: {params}")
    
    try:
        # Nota: O 'requests' lida automaticamente com listas nos parâmetros (years=[2022] vira ?years=2022)
        response = requests.get(base_url, params=params, timeout=120) 
        response.raise_for_status()
        
        # O backend retorna uma lista de dicionários (o sumário de casos)
        return response.json() 
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching SINAN data from the API.")
        if e.response is not None:
              try:
                  error_detail = e.response.json().get("detail", e.response.text)
                  st.write(f"Server error details: {error_detail}")
              except:
                  st.write(f"Network error details: {e}")
        return None
    
@cache_success
def fetch_esus_variables() -> Optional[Dict[str, Any]]:
    """Fetches the list of variables (diseases/conditions) available for e-SUS Notifica."""
    try:
        response = requests.get(f"{API_URL}/pysus/esus/variables")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API to fetch e-SUS variables: {e}")
        return None

@cache_success
def fetch_esus_data(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Requests a summary of e-SUS Notifica data from the API based on disease, year, and state."""
    base_url = f"{API_URL}/pysus/esus/fetch-data"

    st.info(f"Sending query to API: {base_url} with parameters: {params}")

    try:
        response = requests.get(base_url, params=params, timeout=300)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching e-SUS data from the API.")
        if e.response is not None:
              try:
                  error_detail = e.response.json().get("detail", e.response.text)
                  st.write(f"Server error details: {error_detail}")
              except:
                  st.write(f"Network error details: {e}")
        return None

@cache_success
def fetch_prevalence_map(state_abbr: str, year: int, disease_code: str, metric: str, source: str = "sinan", filters: Optional[Dict[str, Any]] = None) -> Optional[bytes]:
    """ Requests the prevalence map image from the backend API. """

    # 1. MUDANÇA: Atualiza a URL base para a nova rota
    base_url = f"{API_URL}/maps/{state_abbr}/{year}/prevalence"

    # 2. MUDANÇA: Atualiza os parâmetros da query
    params = {
        "disease_code": disease_code,
        "metric": metric,
        "source": source,
        **(filters or {})
    }

    st.info(f"Calling API: {base_url} with params: {params}")

    try:
        response = requests.get(base_url, params=params, timeout=300)
        response.raise_for_status()  # Lança exceção para status 4xx/5xx
        return response.content
        # response.content contains the raw bytes (PNG image) from the backend
    
    # A lógica de erro é exatamente a mesma
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error generating prevalence map in the API.")
        if e.response is not None:
            try:
                # Tenta pegar o "detalhe" do erro da API (comum em FastAPI)
                error_detail = e.response.json().get("detail", e.response.text)
                st.write(f"Server error details: {error_detail}")
            except:
                # Se falhar ao parsear o JSON, mostra o texto bruto
                st.write(f"Network error details: {e}")
        return None

@cache_success
def fetch_prevalence_geojson(state_abbr: str, year: int, disease_code: str, source: str = "sinan", filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """ Requests the prevalence data as GeoJSON (municipality, cases, population, rate) for the interactive map. """
    base_url = f"{API_URL}/maps/{state_abbr}/{year}/prevalence-geojson"
    params = {
        "disease_code": disease_code,
        "source": source,
        **(filters or {})
    }

    st.info(f"Calling API: {base_url} with params: {params}")

    try:
        response = requests.get(base_url, params=params, timeout=300)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error generating interactive map in the API.")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
                st.write(f"Server error details: {error_detail}")
            except:
                st.write(f"Network error details: {e}")
        return None

@cache_success
def fetch_prevalence_chart(state_abbr: str, year: int, disease_code: str, source: str = "sinan", filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """ Requests cases and prevalence for each selected filter value (race, sex, education) from the backend API. """
    base_url = f"{API_URL}/charts/{state_abbr}/{year}/prevalence"
    params = {
        "disease_code": disease_code,
        "source": source,
        **(filters or {})
    }

    st.info(f"Calling API: {base_url} with params: {params}")

    try:
        response = requests.get(base_url, params=params, timeout=300)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error generating prevalence chart in the API.")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
                st.write(f"Server error details: {error_detail}")
            except:
                st.write(f"Network error details: {e}")
        return None
    
@cache_success
def fetch_regional_layers_map(
    state_abbr: str, 
    year: int, 
    show_municipalities: bool = False, 
    show_immediate: bool = False, 
    show_intermediate: bool = False, 
    use_zoom: bool = False
) -> Optional[bytes]:
    """ Requests the regional layers map image from the backend API. """
    
    # 1. URL base para a nova rota
    base_url = f"{API_URL}/maps/{state_abbr}/{year}/regional-layers"

    # 2. Parâmetros da query
    params = {
        "show_municipalities": show_municipalities,
        "show_immediate": show_immediate,
        "show_intermediate": show_intermediate,
        "use_zoom": use_zoom
    }

    st.info(f"Calling API: {base_url} with params: {params}")

    try:
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()  # Lança exceção para status 4xx/5xx
        return response.content
    
    except requests.exceptions.RequestException as e:
        # Mensagem de erro específica para esta função
        st.error(f"❌ Error generating regional layers map in the API.")
        
        # O restante do tratamento de erro é o mesmo
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
                st.write(f"Server error details: {error_detail}")
            except:
                st.write(f"Network error details: {e}")
        return None
    
@cache_success
def fetch_sim_variables() -> Optional[Dict[str, Any]]:
    
    base_url = f"{API_URL}/pysus/sim/variables"

    st.info(f"Calling API: {base_url}")

    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()  
        
        return response.json() 
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao buscar variáveis do SIM.")
        
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
                st.write(f"Server error details: {error_detail}")
            except:
                st.write(f"Network error details: {e}")
        return None
    
@cache_success
def fetch_sim_data(
    group_code: str, 
    years: List[int], 
    states: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """ 
    Busca dados do SIM (Sistema de Informações sobre Mortalidade) da API. 
    """
    
    # 1. URL base para a nova rota
    base_url = f"{API_URL}/pysus/sim/fetch-data"

    # 2. Parâmetros da query
    # O 'requests' lida automaticamente com a formatação
    # de listas (years, states) para a query string.
    params: Dict[str, Any] = {
        "group_code": group_code,
        "years": years
    }
    
    # Adiciona 'states' apenas se a lista não estiver vazia
    if states:
        params["states"] = states

    st.info(f"Calling API: {base_url} with params: {params}")

    try:
        # Consultas de dados podem demorar mais que mapas, 
        # aumentei o timeout para 180s (3 minutos)
        response = requests.get(base_url, params=params, timeout=180)
        response.raise_for_status()  # Lança exceção para status 4xx/5xx
        
        # Retorna os dados em formato JSON (dicionário)
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao buscar dados do SIM na API.")
        
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
                st.write(f"Server error details: {error_detail}")
            except:
                st.write(f"Network error details: {e}")
        return None
    
@cache_success
def fetch_sinasc_variables() -> Optional[Dict[str, Any]]:
    
    base_url = f"{API_URL}/pysus/sinasc/variables"

    st.info(f"Calling API: {base_url}")

    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()  
        
        return response.json() 
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao buscar variáveis do SINASC.")
        
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
                st.write(f"Server error details: {error_detail}")
            except:
                st.write(f"Network error details: {e}")
        return None
    
@cache_success
def fetch_sinasc_data(
    group_code: str, 
    years: List[int], 
    states: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    
    base_url = f"{API_URL}/pysus/sinasc/get-summary"
    params: Dict[str, Any] = {
        "group_code": group_code,
        "years": years
    }
    if states:
        params["states"] = states

    st.info(f"Calling API: {base_url} with params: {params}")

    try:
        response = requests.get(base_url, params=params, timeout=180)
        response.raise_for_status()  
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao buscar dados do SIM na API.")
        
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
                st.write(f"Server error details: {error_detail}")
            except:
                st.write(f"Network error details: {e}")
        return None