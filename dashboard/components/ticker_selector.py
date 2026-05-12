import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402


@st.cache_data(ttl=86400, show_spinner=False)
def _carregar_acoes() -> dict[str, str]:
    """Carrega lista completa de ações da brapi (cache 24h)."""
    try:
        brapi = BrapiCollector()
        lista = brapi.get_lista_acoes()
        acoes = {}
        for item in lista:
            ticker = item.get("stock", "")
            nome = item.get("name", "")
            if ticker and nome:
                # Limpar nome (brapi retorna tudo maiusculo)
                nome_limpo = nome.strip().title()
                acoes[ticker] = nome_limpo
        # Ordenar por ticker
        return dict(sorted(acoes.items()))
    except Exception:
        return {}


def _get_acoes() -> dict[str, str]:
    """Retorna dict ticker -> nome. Usa cache do Streamlit."""
    acoes = _carregar_acoes()
    if not acoes:
        # Fallback minimo se API falhar
        return {
            "PETR4": "Petrobras PN", "VALE3": "Vale S/A",
            "ITUB4": "Itau Unibanco PN", "BBAS3": "Banco Do Brasil",
            "WEGE3": "Weg S/A", "ABEV3": "Ambev S/A",
        }
    return acoes


def _get_options() -> tuple[list[str], list[str]]:
    acoes = _get_acoes()
    options = [f"{t} - {n}" for t, n in acoes.items()]
    tickers = list(acoes.keys())
    return options, tickers


# Exports para uso externo
TICKERS_DISPONIVEIS = _get_acoes()


def ticker_selectbox(
    label: str = "Selecione a ação:",
    default: str = "PETR4",
    key: str | None = None,
    sidebar: bool = False,
) -> str:
    """
    Selectbox pesquisavel de tickers com nome da empresa.
    Retorna o ticker selecionado (ex: 'PETR4').
    """
    widget = st.sidebar.selectbox if sidebar else st.selectbox
    options, tickers = _get_options()

    default_idx = 0
    if default in tickers:
        default_idx = tickers.index(default)

    selecionado = widget(label, options, index=default_idx, key=key)
    return selecionado.split(" - ")[0].strip()


def ticker_multiselect(
    label: str = "Selecione ações:",
    default: list[str] | None = None,
    key: str | None = None,
    sidebar: bool = False,
) -> list[str]:
    """
    Multiselect pesquisavel de tickers.
    Retorna lista de tickers selecionados.
    """
    widget = st.sidebar.multiselect if sidebar else st.multiselect
    options, tickers = _get_options()
    acoes = _get_acoes()

    default_opts = []
    if default:
        for t in default:
            if t in acoes:
                default_opts.append(f"{t} - {ações[t]}")

    selecionados = widget(label, options, default=default_opts, key=key)
    return [s.split(" - ")[0].strip() for s in selecionados]
