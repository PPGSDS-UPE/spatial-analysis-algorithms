import json
from typing import Optional, Dict, Any, List

from src.domain.processors.case_filters import CaseFilters
from src.domain.use_cases.maps.get_map_prevalence_use_case import GetMapPrevalenceUseCase

# Simplificação das geometrias (graus, ~500 m): reduz bastante o GeoJSON sem perda visível no mapa
SIMPLIFY_TOLERANCE = 0.005
PROPERTY_COLUMNS = ["code_muni", "name_muni", "total_cases", "population", "prevalence_per_100000"]


class GetMapPrevalenceGeoJsonUseCase:
    """
    Mesmos dados do mapa de prevalência em PNG, em GeoJSON (WGS84) para o mapa interativo.
    Cada município traz nome, casos (já com os filtros aplicados), população e taxa por 100 mil hab.
    """

    def execute(
        self,
        state_abbr: str,
        year: int,
        disease_code: str,
        source: str = "sinan",
        filters: Optional[CaseFilters] = None
    ) -> Optional[Dict[str, Any]]:

        merged_gdf = GetMapPrevalenceUseCase().build_dataset(
            state_abbr=state_abbr,
            year=year,
            disease_code=disease_code,
            source=source,
            filters=filters
        )
        if merged_gdf is None:
            return None

        gdf = merged_gdf.to_crs(epsg=4326)
        view_bounds = self._mainland_bounds(gdf)
        gdf["geometry"] = gdf.geometry.simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)

        gdf = gdf[PROPERTY_COLUMNS + ["geometry"]].copy()
        gdf["code_muni"] = gdf["code_muni"].astype(int)
        gdf["prevalence_per_100000"] = gdf["prevalence_per_100000"].round(2)

        total_cases = int(gdf["total_cases"].sum())
        total_population = int(gdf["population"].sum())

        return {
            "metadata": {
                "state": state_abbr.upper(),
                "year": year,
                "disease_code": disease_code,
                "source": source,
                "filters": filters.to_dict() if filters and not filters.is_empty() else {},
                "filters_description": filters.describe() if filters else "",
                "total_cases": total_cases,
                "population": total_population,
                "prevalence_per_100000": round(total_cases / total_population * 100_000, 2) if total_population else 0.0,
                "bounds": view_bounds,
            },
            "geojson": json.loads(gdf.to_json()),
        }

    @staticmethod
    def _mainland_bounds(gdf) -> List[float]:
        """
        Limites para o enquadramento inicial, ignorando municípios isolados (ilhas oceânicas,
        ex.: Fernando de Noronha), que deslocariam o zoom. As ilhas continuam no GeoJSON.
        """
        sindex = gdf.sindex
        touches_neighbor = [
            len(sindex.query(geometry.buffer(0.01), predicate="intersects")) > 1
            for geometry in gdf.geometry
        ]
        mainland = gdf[touches_neighbor] if any(touches_neighbor) else gdf
        return [float(value) for value in mainland.total_bounds]
