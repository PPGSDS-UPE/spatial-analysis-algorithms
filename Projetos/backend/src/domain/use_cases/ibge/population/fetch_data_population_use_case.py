import pandas as pd
import sidrapy
from typing import List, Dict, Any, Optional

CENSUS_YEAR = 2022
CENSUS_TABLE_CODE = "4709"
CENSUS_VARIABLE_CODE = "93"
ESTIMATE_TABLE_CODE = "6579"
ESTIMATE_VARIABLE_CODE = "9324"

STATE_ABBR_TO_IBGE_CODE: Dict[str, str] = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27",
    "SE": "28", "BA": "29", "MG": "31", "ES": "32", "RJ": "33", "SP": "35",
    "PR": "41", "SC": "42", "RS": "43", "MS": "50", "MT": "51", "GO": "52", "DF": "53"
}

class FetchDataPopulationUseCase:
    def execute(self, year: int, state_abbr: str) -> Optional[List[Dict[str, Any]]]:
        
        state_code = STATE_ABBR_TO_IBGE_CODE.get(state_abbr.upper())
        if not state_code:
            print(f"Erro: sigla de estado '{state_abbr}' inválida.")
            return None

        # O IBGE não publica estimativas para todos os anos (ex.: 2023, logo após o Censo 2022).
        # Se o ano pedido não tiver dados, usa o ano disponível mais próximo, priorizando o Censo.
        candidate_years = [year] + sorted(
            {CENSUS_YEAR, *range(year - 3, year + 4)} - {year},
            key=lambda y: (y != CENSUS_YEAR, abs(y - year), -y)
        )

        raw_data_table = None
        for candidate_year in candidate_years:
            raw_data_table = self._query_sidra(candidate_year, state_code)
            if raw_data_table is not None:
                if candidate_year != year:
                    print(f"Aviso: sem dados de população para {year}; usando {candidate_year}.")
                break

        if raw_data_table is None:
            print("Nenhum dado retornado pela API SIDRA.")
            return None

        dataframe = pd.DataFrame(raw_data_table)
        dataframe.columns = dataframe.iloc[0]
        dataframe = dataframe.drop(0).reset_index(drop=True)

        dataframe.rename(columns={
            'Município (Código)': 'municipality_code_7digit',
            'Município': 'municipality_name',
            'Valor': 'population'
        }, inplace=True)

        required_cols = ['municipality_code_7digit', 'municipality_name', 'population']
        if not all(col in dataframe.columns for col in required_cols):
            print("Erro: Colunas esperadas não encontradas no DataFrame.")
            print("Colunas disponíveis:", list(dataframe.columns))
            return None

        final_dataframe = dataframe[required_cols].copy()

        # Converte para numérico e remove linhas inválidas
        final_dataframe[['municipality_code_7digit', 'population']] = (
            final_dataframe[['municipality_code_7digit', 'population']]
            .apply(pd.to_numeric, errors='coerce')
        )
        final_dataframe.dropna(inplace=True)
        final_dataframe = final_dataframe.astype({
            'municipality_code_7digit': int,
            'population': int
        })

        # Calcula código de 6 dígitos (sem o dígito verificador)
        final_dataframe['code_muni_6digit'] = final_dataframe['municipality_code_7digit'] // 10

        final_dataframe = final_dataframe[
            ['code_muni_6digit', 'municipality_code_7digit', 'municipality_name', 'population']
        ]

        return final_dataframe.to_dict(orient='records')

    @staticmethod
    def _query_sidra(year: int, state_code: str) -> Optional[Any]:
        table_to_query = CENSUS_TABLE_CODE if year == CENSUS_YEAR else ESTIMATE_TABLE_CODE
        variable_to_query = CENSUS_VARIABLE_CODE if year == CENSUS_YEAR else ESTIMATE_VARIABLE_CODE

        # A API espera o formato "in n3 XX" (municípios dentro do estado XX)
        territorial_scope = f"in n3 {state_code}"

        try:
            raw_data_table = sidrapy.get_table(
                table_code=table_to_query,
                territorial_level="6",
                ibge_territorial_code=territorial_scope,
                variable=variable_to_query,
                period=str(year),
                header="y"
            )
        except Exception as e:
            print(f"Erro ao buscar dados do SIDRA para {year} (tabela {table_to_query}): {e}")
            return None

        if raw_data_table is None or len(raw_data_table) <= 1:
            return None
        return raw_data_table
