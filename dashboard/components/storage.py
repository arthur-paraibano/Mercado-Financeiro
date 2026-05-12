"""
Storage abstrato compatível com Streamlit Cloud (efêmero) e local (persistente).

Em produção (Streamlit Cloud), filesystem é efêmero — usa `st.session_state`.
Localmente, persiste em arquivos JSON em `dashboard/data/`.

Detecção: variável de ambiente STREAMLIT_RUNTIME (presente no Cloud) ou flag manual.
"""
import json
import os
from pathlib import Path
from typing import Any

import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _is_cloud() -> bool:
    """Detecta se está rodando no Streamlit Cloud."""
    # No Cloud, HOME costuma ser /home/appuser e essas variáveis estão definidas
    return os.getenv("STREAMLIT_SHARING_MODE") == "true" or "/mount/src" in str(Path.cwd())


def carregar(nome: str, padrao: Any) -> Any:
    """
    Carrega dados pelo nome (sem .json). Tenta session_state primeiro,
    depois arquivo local. Retorna `padrao` se nada encontrado.
    """
    key = f"_store_{nome}"

    # 1. Já em session_state?
    if key in st.session_state:
        return st.session_state[key]

    # 2. Tentar carregar de arquivo local (modo local)
    if not _is_cloud():
        path = DATA_DIR / f"{nome}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                st.session_state[key] = data
                return data
            except Exception:
                pass

    # 3. Fallback: padrão
    st.session_state[key] = padrao
    return padrao


def salvar(nome: str, dados: Any):
    """
    Salva dados. Sempre escreve em session_state.
    Se rodando local, também persiste em arquivo JSON.
    """
    key = f"_store_{nome}"
    st.session_state[key] = dados

    if not _is_cloud():
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            (DATA_DIR / f"{nome}.json").write_text(
                json.dumps(dados, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception:
            # Falha de escrita não deve quebrar o app
            pass
