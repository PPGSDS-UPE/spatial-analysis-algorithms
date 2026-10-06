import pandas as pd
from pysus.ftp.databases import SINAN
from typing import List, Dict, Optional, Any
from collections import Counter
import pyarrow.parquet as pq
from pathlib import Path 
from src.infrastructure.shared import data_utils
from src.domain.processors.case_filters import CaseFilters, apply_case_filters, count_distributions

class FetchDataSinanUseCase:
   
    def execute(self, disease_code: str, years: List[int], states: Optional[List[str]] = None, filters: Optional[CaseFilters] = None) -> Optional[Dict[str, Any]]:
        try:
            print(f"Buscando arquivos no SINAN para o agravo '{disease_code}'...")
            sinan_db = SINAN().load()
            total_counts = Counter()
            distribution_counts: Dict[str, Counter] = {}
            column_names: Optional[List[str]] = None 
            
            for year in years:
                print(f"Processando lote para o ano: {year}...")
                
                files_to_download = sinan_db.get_files(dis_code=disease_code, year=year)
                if not files_to_download: continue

                downloaded_obj = sinan_db.download(files_to_download, local_dir='/tmp')
                if not downloaded_obj: continue

                dir_path = Path(downloaded_obj.path)
                print(f" -> Dados baixados na pasta: {dir_path}")

                parquet_files_paths = list(dir_path.glob('*.parquet'))
                
                if not parquet_files_paths:
                    print(f" -> Nenhum arquivo .parquet encontrado dentro da pasta {dir_path}")
                    continue

                for filepath in parquet_files_paths:
                    print(f" -> Lendo arquivo de dados: {filepath.name}")
                    parquet_file = pq.ParquetFile(filepath)

                    for i in range(parquet_file.num_row_groups):
                        chunk_df = parquet_file.read_row_group(i).to_pandas()
                        
                        if chunk_df.empty: continue

                        if column_names is None:
                            column_names = chunk_df.columns.tolist() 
                            print(f"-> Cabeçalho capturado: {column_names[:5]}...")

                        municipality_col = next((col for col in ["ID_MN_RESI", "ID_MUNICIP", "ID_MN_NOT"] if col in chunk_df.columns), None)
                        if not municipality_col: continue
                        
                        
                        filtered_chunk_df = data_utils.filter_dataframe_by_states(chunk_df, states, municipality_col)
                        filtered_chunk_df = apply_case_filters(filtered_chunk_df, filters)
                        filtered_chunk_df = filtered_chunk_df.dropna(subset=[municipality_col])

                        partial_counts = filtered_chunk_df[municipality_col].value_counts()
                        for variable, counts in count_distributions(filtered_chunk_df).items():
                            distribution_counts.setdefault(variable, Counter()).update(counts)
                        total_counts.update(partial_counts.to_dict())
            
            if not total_counts:
                 print("Nenhum registro encontrado após o processamento.")
                 
                 return {
                     "summary": [], 
                     "columns": column_names if column_names else []
                 }

            summary_list = [{"municipality_code": code, "total_cases": count} for code, count in total_counts.items()]
            print(f"Resumo final do SINAN gerado para {len(summary_list)} municípios.")
            
            return {
                "summary": summary_list,
                "columns": column_names if column_names else [],
                "distributions": {variable: dict(counts) for variable, counts in distribution_counts.items()}
            }
            
        except Exception as e:
            print(f"Ocorreu um erro durante a busca de dados do SINAN: {e}")
            return None