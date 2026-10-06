from typing import Any, Dict, List, Optional

from src.domain.processors.case_filters import CaseFilters
from src.domain.use_cases.ibge.population.fetch_data_population_use_case import FetchDataPopulationUseCase
from src.domain.use_cases.maps.get_map_prevalence_use_case import CASE_SOURCES

MULTIPLIER = 100_000


class GetChartPrevalenceUseCase:
    """
    Casos e prevalência no estado para cada valor marcado nos filtros (cor/raça, sexo, escolaridade).

    Os casos de cada categoria são contados com todos os filtros aplicados (ex.: marcar Feminino e
    Parda/Preta compara Parda x Preta entre mulheres, e Feminino entre pessoas pardas ou pretas).
    Como no mapa, o denominador é a população total (não há população por categoria em todos os anos).
    """

    def execute(
        self,
        state_abbr: str,
        year: int,
        disease_code: str,
        source: str = "sinan",
        filters: Optional[CaseFilters] = None
    ) -> Optional[Dict[str, Any]]:

        population_data = FetchDataPopulationUseCase().execute(year=year, state_abbr=state_abbr)
        if not population_data:
            print("❌ Falha: Dados de população não encontrados.")
            return None
        population = sum(item["population"] for item in population_data)

        cases_data = CASE_SOURCES[source]().execute(
            disease_code=disease_code,
            years=[year],
            states=[state_abbr],
            filters=filters
        )
        if cases_data is None:
            print(f"❌ Falha: Dados de casos ({source.upper()}) não encontrados.")
            return None

        distributions = cases_data.get("distributions", {})
        filters = filters or CaseFilters()
        selected_by_variable = {
            "race": filters.races,
            "sex": filters.sexes,
            "education": filters.education_levels,
        }

        series: Dict[str, List[Dict[str, Any]]] = {}
        for variable, selected in selected_by_variable.items():
            if not selected:
                continue
            counts = distributions.get(variable, {})
            series[variable] = [
                {
                    "category": category,
                    "total_cases": counts.get(category, 0),
                    f"prevalence_per_{MULTIPLIER}": counts.get(category, 0) / population * MULTIPLIER,
                }
                for category in selected
            ]

        total_cases = sum(item["total_cases"] for item in cases_data.get("summary", []))
        return {
            "population": population,
            "total_cases": total_cases,
            f"prevalence_per_{MULTIPLIER}": total_cases / population * MULTIPLIER,
            "series": series,
        }
