import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Garante que prints com acentos/emojis não quebrem no console do Windows (cp1252)
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# Corrige bugs do pysus 1.x (Windows e FTP concorrente); precisa rodar antes dos imports que usam pysus
from src.infrastructure.shared.pysus_compat import apply_pysus_patches
apply_pysus_patches()

# --- 1. IMPORTS DOS ROTEADORES (CORRIGIDOS) ---

# Módulo PySUS
from src.infrastructure.controllers.pysus.systems.routes import systems_router 
from src.infrastructure.controllers.pysus.cnes.routes import cnes_router
from src.infrastructure.controllers.pysus.sia.routes import sia_router
from src.infrastructure.controllers.pysus.sih.routes import sih_router
from src.infrastructure.controllers.pysus.sim.routes import sim_router
from src.infrastructure.controllers.pysus.sinan.routes import sinan_router
from src.infrastructure.controllers.pysus.sinasc.routes import sinasc_router
from src.infrastructure.controllers.pysus.esus.routes import esus_router

# Módulo Sidra
from src.infrastructure.controllers.sidra.routes import sidra_router 

# Módulo de Mapas
from src.infrastructure.controllers.maps.routes import maps_router
from src.infrastructure.controllers.maps.routes import get_map_state_layers_route

# Módulo de Gráficos
from src.infrastructure.controllers.charts.routes import charts_router

# --- 2. INSTÂNCIA PRINCIPAL DA API ---
app = FastAPI(
    title="API de Dados Abertos e Geografia",
    description="Uma API para consultar e processar dados do DATASUS (via PySUS), IBGE (via SidraPy) e Gerar mapas para análises técnicas.",
    version="1.0.0",
    contact={
        "name": "Henrique Dias",
        "url": "https://github.com/HenriqueDiass",
        "projeto": "Bolsa BIA UPE - 2025"
    },
)

# --- 3. MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 4. INCLUSÃO DOS ROTEADORES ---

# Rota Raiz
@app.get("/", tags=["Root"])
def read_root():
    """Endpoint raiz para verificar se a API está online."""
    return {"message": "API de Dados Abertos no ar!"}

# Módulo PySUS
app.include_router(systems_router, prefix="/pysus/systems")
app.include_router(cnes_router, prefix="/pysus/cnes")
app.include_router(sia_router, prefix="/pysus/sia")
app.include_router(sih_router, prefix="/pysus/sih")
app.include_router(sim_router, prefix="/pysus/sim")
app.include_router(sinan_router, prefix="/pysus/sinan")
app.include_router(sinasc_router, prefix="/pysus/sinasc")
app.include_router(esus_router, prefix="/pysus/esus")

# Módulo Sidra
app.include_router(sidra_router, prefix="/sidra")

# Módulo de Mapas # <-- AJUSTE AQUI
app.include_router(
    maps_router,
    prefix="/maps",
    tags=["Maps"] # A tag já está no arquivo de rotas, mas é bom manter aqui.
)

# Módulo de Gráficos
app.include_router(charts_router, prefix="/charts")


# --- 5. COMANDO PARA RODAR (NO TERMINAL) ---
# Lembre-se de estar na pasta 'backend/' e com o ambiente virtual ativado
# uvicorn main:app --reload