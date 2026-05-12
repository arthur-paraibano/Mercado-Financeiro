import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env da raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# --- APIs ---
BRAPI_TOKEN = os.getenv("BRAPI_TOKEN", "")
BRAPI_BASE_URL = "https://brapi.dev/api"

# --- CVM ---
CVM_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
CVM_DFP_URL = f"{CVM_BASE_URL}/DOC/DFP/DADOS"
CVM_ITR_URL = f"{CVM_BASE_URL}/DOC/ITR/DADOS"
CVM_CAD_URL = f"{CVM_BASE_URL}/CAD/DADOS"

# --- Banco de dados ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/mercado_financeiro")

# --- Rate limits (segundos entre requisicoes) ---
BRAPI_DELAY = 0.5
CVM_DELAY = 1.0

# --- Cache TTL (segundos) ---
CACHE_TTL_COTACAO = 300       # 5 minutos
CACHE_TTL_INDICADORES = 3600  # 1 hora
CACHE_TTL_DFP = 86400         # 24 horas
