"""
Configurações do projeto. Suporta:
- Local: variáveis no arquivo .env
- Streamlit Cloud: secrets.toml gerenciado pela plataforma
"""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def _get_secret(key: str, default: str = "") -> str:
    """Tenta ler do st.secrets (Cloud); fallback para .env local."""
    # 1. Streamlit Secrets (produção)
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass

    # 2. .env local
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT_DIR / ".env")
    except ImportError:
        pass

    return os.getenv(key, default)


# --- APIs ---
BRAPI_TOKEN = _get_secret("BRAPI_TOKEN", "")
BRAPI_BASE_URL = "https://brapi.dev/api"

# --- CVM ---
CVM_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
CVM_DFP_URL = f"{CVM_BASE_URL}/DOC/DFP/DADOS"
CVM_ITR_URL = f"{CVM_BASE_URL}/DOC/ITR/DADOS"
CVM_CAD_URL = f"{CVM_BASE_URL}/CAD/DADOS"

# --- Banco de dados (apenas para uso local via scripts/setup.py) ---
DATABASE_URL = _get_secret("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/mercado_financeiro")

# --- Rate limits (segundos entre requisições) ---
BRAPI_DELAY = 0.5
CVM_DELAY = 1.0

# --- Cache TTL (segundos) ---
CACHE_TTL_COTACAO = 300       # 5 minutos
CACHE_TTL_INDICADORES = 3600  # 1 hora
CACHE_TTL_DFP = 86400         # 24 horas
