import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.bcb_collector import BCBCollector  # noqa: E402
from src.collectors.ibge_collector import IBGECollector  # noqa: E402

st.title("Indicadores Macroeconomicos")

bcb = BCBCollector()
ibge = IBGECollector()


# --- Funcoes com cache e fallback ---

@st.cache_data(ttl=3600, show_spinner=False)
def carregar_ipca_ibge():
    """IPCA via IBGE - mais estável que BCB."""
    return ibge._get(7060, "-48", 69)


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_ipca_mensal_ibge():
    """IPCA mensal via IBGE."""
    return ibge._get(7060, "-48", 63)


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_pib():
    return ibge.get_pib_trimestral(40)


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_producao_industrial():
    return ibge.get_producao_industrial(24)


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_comercio():
    return ibge.get_comercio_varejo(24)


@st.cache_data(ttl=1800, show_spinner=False)
def tentar_bcb_selic():
    """Tenta BCB com timeout curto. Retorna None se falhar."""
    try:
        df = bcb.get_selic("01/01/2020")
        return df if not df.empty else None
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def tentar_bcb_cambio():
    try:
        df = bcb.get_cambio_dolar("01/01/2024")
        return df if not df.empty else None
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def tentar_bcb_focus(indicador):
    try:
        df = bcb.get_expectativas_focus(indicador)
        return df if not df.empty else None
    except Exception:
        return None


# --- Carregar dados ---
with st.spinner("Carregando dados do IBGE..."):
    ipca_acum = carregar_ipca_ibge()
    ipca_mensal = carregar_ipca_mensal_ibge()
    pib = carregar_pib()
    prod_ind = carregar_producao_industrial()
    comercio = carregar_comercio()

# BCB (tentativa rapida, sem travar a pagina)
with st.expander("⚙️ Configurações"):
    tentar_bcb = st.checkbox("Tentar carregar dados do BCB (pode demorar)", value=False,
                              help="Inclui Selic, câmbio e expectativas Focus. Pode levar até 15s.")

selic_df = None
cambio_df = None
focus_ipca = None
focus_selic = None

if tentar_bcb:
    with st.spinner("Tentando BCB (timeout 15s)..."):
        selic_df = tentar_bcb_selic()
        cambio_df = tentar_bcb_cambio()
        focus_ipca = tentar_bcb_focus("IPCA")
        focus_selic = tentar_bcb_focus("Selic")

# --- Metricas atuais ---
st.subheader("Indicadores Atuais")
col1, col2, col3, col4 = st.columns(4)

# SELIC
if selic_df is not None:
    col1.metric("SELIC (meta)", f"{selic_df['valor'].iloc[-1]:.2f}% a.a.")
else:
    col1.metric("SELIC (meta)", "14.25% a.a.", help="Valor de referencia. Ative BCB na sidebar para dados em tempo real.")

# IPCA
if not ipca_acum.empty:
    ultimo_ipca = ipca_acum.dropna(subset=["valor"])
    if not ultimo_ipca.empty:
        col2.metric("IPCA Acum. Ano", f"{ultimo_ipca['valor'].iloc[-1]:.2f}%")
    else:
        col2.metric("IPCA", "Indisponivel")
else:
    col2.metric("IPCA", "Indisponivel")

# Cambio
if cambio_df is not None:
    col3.metric("Dolar (PTAX)", f"R$ {cambio_df['valor'].iloc[-1]:.4f}")
else:
    col3.metric("Dolar (PTAX)", "~R$ 5.70", help="Valor aproximado. Ative BCB na sidebar para dado real.")

# PIB
if not pib.empty:
    col4.metric("PIB (ult. trim.)", f"{pib['valor'].iloc[-1]:.1f}%")
else:
    col4.metric("PIB Trimestral", "Indisponivel")

st.divider()

# --- Graficos IBGE (sempre disponiveis) ---
st.subheader("Dados do IBGE")

col1, col2 = st.columns(2)

with col1:
    if not ipca_mensal.empty:
        ipca_plot = ipca_mensal.dropna(subset=["valor"]).tail(24)
        if not ipca_plot.empty:
            fig = px.bar(
                ipca_plot, x="período", y="valor",
                title="IPCA Mensal (% m/m) - Últimos 24 meses",
                labels={"valor": "%", "período": ""},
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, width="stretch")

with col2:
    if not ipca_acum.empty:
        ipca_a_plot = ipca_acum.dropna(subset=["valor"]).tail(24)
        if not ipca_a_plot.empty:
            fig = px.line(
                ipca_a_plot, x="período", y="valor",
                title="IPCA Acumulado no Ano (%)",
                labels={"valor": "%", "período": ""},
            )
            fig.update_traces(line_color="#d62728")
            fig.update_layout(height=350)
            st.plotly_chart(fig, width="stretch")

# PIB
if not pib.empty:
    pib_plot = pib.copy()
    pib_plot["cor"] = pib_plot["valor"].apply(lambda v: "Positivo" if v >= 0 else "Negativo")
    fig = px.bar(
        pib_plot, x="período", y="valor",
        color="cor",
        color_discrete_map={"Positivo": "#2ca02c", "Negativo": "#d62728"},
        title="PIB - Variação Trimestral (%)",
        labels={"valor": "%", "período": "Trimestre"},
    )
    fig.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig, width="stretch")

# Producao Industrial e Comercio
col1, col2 = st.columns(2)

with col1:
    if not prod_ind.empty:
        pi_plot = prod_ind.dropna(subset=["valor"]).tail(24)
        if not pi_plot.empty:
            fig = px.line(
                pi_plot, x="período", y="valor",
                title="Producao Industrial (índice)",
                labels={"valor": "Índice", "período": ""},
            )
            fig.update_traces(line_color="#ff7f0e")
            fig.update_layout(height=300)
            st.plotly_chart(fig, width="stretch")

with col2:
    if not comercio.empty:
        com_plot = comercio.dropna(subset=["valor"]).tail(24)
        if not com_plot.empty:
            fig = px.line(
                com_plot, x="período", y="valor",
                title="Comercio Varejista (volume de vendas)",
                labels={"valor": "Índice", "período": ""},
            )
            fig.update_traces(line_color="#9467bd")
            fig.update_layout(height=300)
            st.plotly_chart(fig, width="stretch")

st.divider()

# --- Dados BCB (quando disponiveis) ---
if selic_df is not None or cambio_df is not None:
    st.subheader("Dados do Banco Central")

    col1, col2 = st.columns(2)

    with col1:
        if selic_df is not None:
            fig = px.line(
                selic_df, x="data", y="valor",
                title="SELIC Meta (% a.a.)",
                labels={"valor": "%", "data": ""},
            )
            fig.update_traces(line_color="#1f77b4")
            fig.update_layout(height=350)
            st.plotly_chart(fig, width="stretch")

    with col2:
        if cambio_df is not None:
            fig = px.line(
                cambio_df, x="data", y="valor",
                title="Dolar PTAX (R$)",
                labels={"valor": "R$", "data": ""},
            )
            fig.update_traces(line_color="#2ca02c")
            fig.update_layout(height=350)
            st.plotly_chart(fig, width="stretch")

    # Focus
    if focus_ipca is not None or focus_selic is not None:
        st.subheader("Expectativas de Mercado (Boletim Focus)")
        col1, col2 = st.columns(2)

        with col1:
            if focus_ipca is not None:
                st.write("**Projeções IPCA**")
                focus_show = (
                    focus_ipca.sort_values("Data", ascending=False)
                    .drop_duplicates(subset=["DataReferencia"])
                    .head(5).sort_values("DataReferencia")
                )
                cols = [c for c in ["DataReferencia", "Mediana", "Mínimo", "Máximo"] if c in focus_show.columns]
                st.dataframe(
                    focus_show[cols].rename(columns={
                        "DataReferencia": "Ano", "Mediana": "Mediana %",
                        "Mínimo": "Min %", "Máximo": "Max %",
                    }),
                    width="stretch", hide_index=True,
                )

        with col2:
            if focus_selic is not None:
                st.write("**Projeções SELIC**")
                focus_show = (
                    focus_selic.sort_values("Data", ascending=False)
                    .drop_duplicates(subset=["DataReferencia"])
                    .head(5).sort_values("DataReferencia")
                )
                cols = [c for c in ["DataReferencia", "Mediana", "Mínimo", "Máximo"] if c in focus_show.columns]
                st.dataframe(
                    focus_show[cols].rename(columns={
                        "DataReferencia": "Ano", "Mediana": "Mediana %",
                        "Min %": "Min %", "Máximo": "Max %",
                    }),
                    width="stretch", hide_index=True,
                )

elif not tentar_bcb:
    st.info(
        "Dados de SELIC, Dolar e Focus não carregados. "
        "Ative **'Tentar carregar BCB'** na sidebar para buscar dados do Banco Central. "
        "A API do BCB pode estar temporariamente indisponivel."
    )

st.caption("Fontes: IBGE (IPCA, PIB, Producao, Comercio) | BCB (SELIC, PTAX, Focus)")
