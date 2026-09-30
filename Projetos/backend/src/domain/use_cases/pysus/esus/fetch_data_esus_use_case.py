import ftplib
import tempfile
import pandas as pd
from pathlib import Path
from collections import Counter
from typing import List, Dict, Optional, Any
from dbfread import DBF
from pyreaddbc import dbc2dbf
from src.infrastructure.shared import data_utils

FTP_HOST = "ftp.datasus.gov.br"
FTP_BASE_PATH = "/dissemin/publicos/ESUSNOTIFICA/DADOS"
# Dados consolidados ficam em FINAIS; os mais recentes, ainda em revisão, em PRELIM
FTP_SUBFOLDERS = ["FINAIS", "PRELIM"]
LOCAL_DIR = Path(tempfile.gettempdir()) / "esus_notifica"

class FetchDataEsusUseCase:
    """
    Busca dados do e-SUS Notifica no FTP do DATASUS.
    Ex.: 'DCCR' = Doença de Chagas Crônica (arquivos DCCRBRAA.dbc, nacionais por ano).
    """

    def execute(self, disease_code: str, years: List[int], states: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        try:
            print(f"Buscando arquivos no e-SUS Notifica para o agravo '{disease_code}'...")
            total_counts = Counter()
            column_names: Optional[List[str]] = None

            for year in years:
                print(f"Processando lote para o ano: {year}...")

                dbc_path = self._download_file(disease_code, year)
                if dbc_path is None:
                    continue

                df = self._read_dbc(dbc_path)
                if df.empty:
                    continue

                if column_names is None:
                    column_names = df.columns.tolist()
                    print(f"-> Cabeçalho capturado: {column_names[:5]}...")

                # No e-SUS as colunas ID_* trazem nomes; os códigos IBGE (6 dígitos) ficam nas CD_*
                municipality_col = next((col for col in ["CD_MN_RESI", "CD_MUNICIP"] if col in df.columns), None)
                if not municipality_col:
                    continue

                filtered_df = data_utils.filter_dataframe_by_states(df, states, municipality_col)

                partial_counts = filtered_df.dropna(subset=[municipality_col])[municipality_col].value_counts()
                total_counts.update(partial_counts.to_dict())

            if not total_counts:
                print("Nenhum registro encontrado após o processamento.")
                return {
                    "summary": [],
                    "columns": column_names if column_names else []
                }

            summary_list = [{"municipality_code": code, "total_cases": count} for code, count in total_counts.items()]
            print(f"Resumo final do e-SUS gerado para {len(summary_list)} municípios.")

            return {
                "summary": summary_list,
                "columns": column_names if column_names else []
            }

        except Exception as e:
            print(f"Ocorreu um erro durante a busca de dados do e-SUS Notifica: {e}")
            return None

    def _download_file(self, disease_code: str, year: int) -> Optional[Path]:
        file_name = f"{disease_code.upper()}BR{str(year)[-2:]}.dbc"
        local_path = LOCAL_DIR / file_name
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)

        if local_path.exists():
            print(f" -> Usando arquivo já baixado: {local_path}")
            return local_path

        ftp = ftplib.FTP(FTP_HOST, timeout=120)
        try:
            ftp.login()
            ftp.voidcmd("TYPE I")  # SIZE só é aceito em modo binário
            for subfolder in FTP_SUBFOLDERS:
                remote_path = f"{FTP_BASE_PATH}/{subfolder}/{file_name}"
                try:
                    ftp.size(remote_path)
                except ftplib.error_perm:
                    continue

                with open(local_path, "wb") as local_file:
                    ftp.retrbinary(f"RETR {remote_path}", local_file.write)
                print(f" -> Dados baixados de {subfolder}: {local_path}")
                return local_path
        finally:
            ftp.quit()

        print(f" -> Arquivo {file_name} não encontrado no FTP.")
        return None

    @staticmethod
    def _read_dbc(dbc_path: Path) -> pd.DataFrame:
        dbf_path = dbc_path.with_suffix(".dbf")
        dbc2dbf(str(dbc_path), str(dbf_path))
        try:
            df = pd.DataFrame(iter(DBF(str(dbf_path), encoding="iso-8859-1")))
        finally:
            dbf_path.unlink(missing_ok=True)

        # Campos vazios do DBF vêm como espaços; converte para nulo
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].str.strip().replace("", pd.NA)

        return df
