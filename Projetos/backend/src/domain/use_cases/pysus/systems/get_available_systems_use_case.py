# src/domain/use-cases/pysus/get-available-systems.use-case.py
"""
Use case to list all PySUS data systems supported by the application.
"""
from typing import List, Dict

class GetAvailablePysusSystemsUseCase:
   
    def execute(self) -> List[Dict[str, str]]:
       
        supported_systems = [
            {
                "code": "SINAN",
                "name": "Sistema de Informação de Agravos de Notificação"
            },
            {
                "code": "SIM",
                "name": "Sistema de Informações sobre Mortalidade"
            },
            {
                "code": "SIH",
                "name": "Sistema de Informações Hospitalares do SUS"
            },
            {
                "code": "SINASC",
                "name": "Sistema de Informações sobre Nascidos Vivos"
            },
            {
                "code": "CNES",
                "name": "Cadastro Nacional de Estabelecimentos de Saúde"
            },
            {
                "code": "SIA",
                "name": "Sistema de Informações Ambulatoriais"
            },
            {
                "code": "ESUS",
                "name": "e-SUS Notifica"
            }
            # Adicione outros sistemas aqui se sua aplicação passar a suportá-los
        ]
        
        return supported_systems