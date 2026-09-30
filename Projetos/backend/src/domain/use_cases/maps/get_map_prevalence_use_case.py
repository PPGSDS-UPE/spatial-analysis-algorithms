import io
from typing import Optional

from src.domain.processors.prevalence_processor import PrevalenceDataProcessor 
from src.domain.use_cases.ibge.population.fetch_data_population_use_case import FetchDataPopulationUseCase
from src.domain.use_cases.pysus.sinan.fetch_data_sinan_use_case import FetchDataSinanUseCase
from src.domain.use_cases.pysus.esus.fetch_data_esus_use_case import FetchDataEsusUseCase
from src.infrastructure.shared import map_plotter

# Fontes de casos suportadas; todas retornam {"summary": [{municipality_code, total_cases}], ...}
CASE_SOURCES = {
    "sinan": FetchDataSinanUseCase,
    "esus": FetchDataEsusUseCase,
}

class GetMapPrevalenceUseCase:

    def execute(
        self,
        state_abbr: str,
        year: int,
        disease_code: str,
        metric_column: str,
        source: str = "sinan"
    ) -> Optional[io.BytesIO]:
        
        
        print("--- PASSO 1: COLETANDO DADOS ---")
        
        population_use_case = FetchDataPopulationUseCase()
        population_data = population_use_case.execute(year=year, state_abbr=state_abbr)
        if not population_data:
            print("❌ Falha: Dados de população não encontrados.")
            return None

        cases_use_case = CASE_SOURCES[source]()
        sinan_data_raw = cases_use_case.execute(
            disease_code=disease_code,
            years=[year],
            states=[state_abbr]
        )

        sinan_summary = sinan_data_raw.get('summary') if sinan_data_raw else None

        if not sinan_summary:
            print(f"❌ Falha: Dados de casos ({source.upper()}) não encontrados.")
            return None

        
        print("\n--- PASSO 2: PROCESSANDO DADOS ---")

        processor = PrevalenceDataProcessor(year=year) 
        
        merged_gdf = processor.execute(
            state_abbr=state_abbr,
            population_data=population_data,
            sinan_summary=sinan_summary
        )
        
        if merged_gdf is None: 
            print("❌ Falha: Não foi possível processar e unir os dados.")
            return None
        
        
        print("\n--- PASSO 3: GERANDO MAPA ---")
        
        
        
        metric_details = {
            "total_cases": {
                "title": f"Total de Casos ({disease_code}) - {state_abbr.upper()} ({year})", 
                "label": "Nº de Casos"
            },
            "prevalence_per_100000": {
                "title": f"Prevalência ({disease_code}) - {state_abbr.upper()} ({year})", 
                "label": "Casos por 100.000 Hab."
            }
            
        }
        
        details = metric_details.get(metric_column)
        if not details:
            print(f"❌ Métrica '{metric_column}' inválida para este mapa.")
            print(f"   Métricas disponíveis: {list(metric_details.keys())}")
            return None

        image_buffer = map_plotter.plot_map(
            gdf=merged_gdf,
            state_abbr=state_abbr,
            column_to_plot=metric_column,
            title=details["title"],
            legend_label=details["label"]
        )

        return image_buffer