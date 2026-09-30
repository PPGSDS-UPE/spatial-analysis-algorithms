from typing import List, Dict

# Agravos disponíveis no FTP do e-SUS Notifica (/dissemin/publicos/ESUSNOTIFICA/DADOS)
ESUS_DISEASES: Dict[str, str] = {
    "DCCR": "Doença de Chagas Crônica",
}

class GetVariablesEsusUseCase:

    def execute(self) -> List[Dict[str, str]]:
        return [{"code": code, "name": name} for code, name in ESUS_DISEASES.items()]
