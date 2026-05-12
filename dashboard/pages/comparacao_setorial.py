import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.fundamentus_collector import FundamentusCollector  # noqa: E402
from src.collectors.b3_collector import SETORES_B3  # noqa: E402

st.title("Comparação Setorial")

# --- Selecao de setor ---
setor_selecionado = st.selectbox("Selecione o setor:", list(SETORES_B3.keys()))
tickers = SETORES_B3[setor_selecionado]

st.caption(f"Empresas no setor: {', '.join(tickers)}")

# --- Selecao de indicador ---
INDICADORES = {
    "P/L":              "pl",
    "P/VP":             "pvp",
    "EV/EBITDA":        "ev_ebitda",
    "Dividend Yield %": "dividend_yield",
    "ROE %":            "roe",
    "ROIC %":           "roic",
    "Margem Líquida %": "margem_liquida",
    "Margem Bruta %":   "margem_bruta",
    "Margem EBIT %":    "margem_ebit",
    "Liquidez Corrente":"liquidez_corrente",
}

indicador_nome = st.selectbox("Indicador para comparar:", list(INDICADORES.keys()))
campo = INDICADORES[indicador_nome]

if st.button("Comparar", type="primary"):
    fund = FundamentusCollector()
    dados = []

    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"Buscando {ticker}...")
        try:
            d = fund.get_papel(ticker)
            valor = d.get(campo)
            if valor is not None:
                dados.append({
                    "ticker": ticker,
                    "empresa": d.get("empresa", ticker),
                    "valor": round(valor, 2),
                    "cotacao": d.get("cotacao"),
                    "pl": d.get("pl"),
                    "pvp": d.get("pvp"),
                    "roe": d.get("roe"),
                    "dy": d.get("dividend_yield"),
                    "margem_liq": d.get("margem_liquida"),
                    "ev_ebitda": d.get("ev_ebitda"),
                })
            time.sleep(0.3)
        except Exception as e:
            st.warning(f"{ticker}: {e}")
        progress.progress((i + 1) / len(tickers))

    progress.empty()
    status.empty()

    if dados:
        df = pd.DataFrame(dados).sort_values("valor", ascending=False)

        # --- Grafico de barras ---
        eh_pct = "%" in indicador_nome
        fig = px.bar(
            df,
            x="ticker",
            y="valor",
            color="valor",
            color_continuous_scale="RdYlGn",
            title=f"{indicador_nome} - {setor_selecionado}",
            labels={"valor": "%" if eh_pct else "x", "ticker": ""},
            text="valor",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig, width="stretch")

        # --- Estatisticas ---
        st.subheader("Estatisticas do Setor")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mediana", f"{df['valor'].median():.2f}")
        col2.metric("Média", f"{df['valor'].mean():.2f}")

        idx_max = df["valor"].idxmax()
        idx_min = df["valor"].idxmin()
        col3.metric(
            "Máximo",
            f"{df.loc[idx_max, 'valor']:.2f}",
            f"{df.loc[idx_max, 'ticker']}",
        )
        col4.metric(
            "Mínimo",
            f"{df.loc[idx_min, 'valor']:.2f}",
            f"{df.loc[idx_min, 'ticker']}",
        )

        st.divider()

        # --- Tabela completa ---
        st.subheader("Dados Completos")
        df_show = df[["ticker", "empresa", "cotação", "pl", "pvp", "roe", "dy", "margem_liq", "ev_ebitda"]].copy()
        df_show.columns = ["Ticker", "Empresa", "Cotação", "P/L", "P/VP", "ROE %", "DY %", "Margem Líq. %", "EV/EBITDA"]
        st.dataframe(df_show, width="stretch", hide_index=True)

    else:
        st.warning("Nenhum dado retornado. Verifique os tickers do setor.")

st.caption("Fonte: fundamentus.com.br")
