from fastapi.responses import JSONResponse
from fastapi import status, HTTPException
from typing import List, Optional, Dict, Any
from fastapi.concurrency import run_in_threadpool

from src.domain.use_cases.pysus.esus.fetch_data_esus_use_case import FetchDataEsusUseCase
from src.domain.processors.case_filters import CaseFilters

async def fetch_esus_data_controller(disease_code: str, years: List[int], states: Optional[List[str]], filters: Optional[CaseFilters] = None):

    try:
        params = {
            "disease_code": disease_code,
            "years": years,
            "states": states
        }
        if filters and not filters.is_empty():
            params["filters"] = filters.to_dict()

        use_case = FetchDataEsusUseCase()

        result_dict: Optional[Dict[str, Any]] = await run_in_threadpool(
            use_case.execute, disease_code=disease_code, years=years, states=states, filters=filters
        )

        if result_dict and "summary" in result_dict:

            summary_list = result_dict["summary"]
            column_names = result_dict.get("columns", [])

            if summary_list:

                total_records = sum(item['total_cases'] for item in summary_list)

                summary_response = {
                    "metadata": {
                        "system": "ESUS",
                        "parameters": params,
                        "columns": column_names,
                        "total_records_found": total_records
                    },
                    "summary_by_municipality": summary_list
                }
                return JSONResponse(content=summary_response, status_code=status.HTTP_200_OK)

            else:
                return JSONResponse(
                    content={"metadata": {"columns": column_names, "total_records_found": 0}, "summary_by_municipality": []},
                    status_code=status.HTTP_200_OK
                )

        else:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado ou estrutura de retorno inválida.")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro interno ao buscar dados do e-SUS: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno no servidor.")
