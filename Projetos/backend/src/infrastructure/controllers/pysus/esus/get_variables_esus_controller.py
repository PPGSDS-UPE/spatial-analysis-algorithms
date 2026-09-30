# src/infrastructure/controllers/pysus/esus/get_variables_esus_controller.py

from fastapi.responses import JSONResponse
from fastapi import status
from src.domain.use_cases.pysus.esus.get_variables_esus_use_case import GetVariablesEsusUseCase

def get_variables_esus_controller():
    """
    Controller para lidar com a requisição das variáveis (doenças) do e-SUS Notifica.
    """
    try:
        use_case = GetVariablesEsusUseCase()
        esus_diseases = use_case.execute()

        response_data = {
            "informationSystem": "ESUS",
            "description": "e-SUS Notifica",
            "variables": esus_diseases
        }
        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        print(f"Erro de servidor ao buscar variáveis do e-SUS: {e}")
        return JSONResponse(
            content={"error": "Ocorreu um erro interno no servidor."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
