import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.fundamentus_collector import FundamentusCollector  # noqa: E402

st.title("Screening - Filtro Avancado de Ações")

# --- Configurações ---
with st.expander("⚙️ Configurações de Filtro", expanded=True):
    st.markdown("**Filtros Fundamentalistas**")
    c1, c2, c3, c4 = st.columns(4)
    pl_min = c1.number_input("P/L mínimo", value=0.0, step=0.5)
    pl_max = c2.number_input("P/L máximo", value=15.0, step=0.5)
    pvp_max = c3.slider("P/VP máximo", 0.0, 10.0, 2.5, 0.1)
    roe_min = c4.slider("ROE mínimo (%)", 0.0, 50.0, 10.0, 0.5)

    c5, c6, c7, c8 = st.columns(4)
    dy_min = c5.slider("DY mínimo (%)", 0.0, 20.0, 0.0, 0.5)
    margem_min = c6.slider("Margem Líq. min (%)", -20.0, 40.0, 0.0, 0.5)
    ev_ebitda_max = c7.slider("EV/EBITDA máximo", 0.0, 30.0, 12.0, 0.5)
    liq_corrente_min = c8.slider("Liquidez Corrente min", 0.0, 5.0, 0.0, 0.1)

    st.markdown("**Filtros Adicionais**")
    c9, c10 = st.columns(2)
    excluir_prejuizo = c9.checkbox("Excluir empresas com prejuízo", value=True)
    apenas_lucro_crescente = c10.checkbox("Apenas com crescimento receita 5a > 0", value=False)

# Universo de acoes
TICKERS = [
    "ABEV3", "AZUL4", "B3SA3", "BBAS3", "BBDC4", "BBSE3", "BEEF3",
    "BPAC11", "BRFS3", "CCRO3", "CMIG4", "COGN3", "CPFE3", "CSAN3",
    "CSNA3", "CYRE3", "EGIE3", "EMBR3", "ENEV3", "ENGI11", "EQTL3",
    "FLRY3", "GGBR4", "GOAU4", "HAPV3", "HYPE3", "ITSA4", "ITUB4",
    "JBSS3", "KLBN11", "LREN3", "LWSA3", "MGLU3", "MRFG3", "MRVE3",
    "MULT3", "NTCO3", "PETR4", "PRIO3", "RADL3", "RDOR3", "RENT3",
    "SANB11", "SLCE3", "SMTO3", "SUZB3", "TAEE11", "TIMS3", "TOTS3",
    "UGPA3", "USIM5", "VALE3", "VBBR3", "VIVT3", "WEGE3",
]

st.info(f"Universo: {len(TICKERS)} ações. Os filtros são aplicados sobre dados do Fundamentus.")

if st.button("Executar Screening", type="primary"):
    fund = FundamentusCollector()
    resultados = []

    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(TICKERS):
        status.text(f"Analisando {ticker} ({i + 1}/{len(TICKERS)})...")
        try:
            d = fund.get_papel(ticker)

            pl = d.get("pl")
            pvp = d.get("pvp")
            roe = d.get("roe") or 0
            dy = d.get("dividend_yield") or 0
            margem = d.get("margem_liquida") or 0
            ev = d.get("ev_ebitda")
            liq = d.get("liquidez_corrente") or 0
            lucro = d.get("lucro_liquido_12m") or 0
            cres = d.get("cres_rec_5a") or 0

            # Aplicar filtros
            passa = True
            if pl is not None and (pl < pl_min or pl > pl_max):
                passa = False
            if pl is not None and pl <= 0:
                passa = False
            if pvp is not None and pvp > pvp_max:
                passa = False
            if roe < roe_min:
                passa = False
            if dy < dy_min:
                passa = False
            if margem < margem_min:
                passa = False
            if ev is not None and ev > ev_ebitda_max:
                passa = False
            if liq_corrente_min > 0 and liq < liq_corrente_min:
                passa = False
            if excluir_prejuizo and lucro < 0:
                passa = False
            if apenas_lucro_crescente and cres <= 0:
                passa = False

            if passa:
                resultados.append({
                    "Ticker": ticker,
                    "Empresa": (d.get("empresa") or ticker)[:25],
                    "Cotação": d.get("cotacao"),
                    "P/L": pl,
                    "P/VP": pvp,
                    "EV/EBITDA": ev,
                    "ROE %": roe,
                    "ROIC %": d.get("roic"),
                    "DY %": dy,
                    "Margem Líq. %": margem,
                    "Margem EBIT %": d.get("margem_ebit"),
                    "Liq. Corrente": liq,
                    "Cresc. 5a %": cres,
                    "Lucro 12m": lucro,
                })
            time.sleep(0.2)
        except Exception:
            pass
        progress.progress((i + 1) / len(TICKERS))

    progress.empty()
    status.empty()

    if resultados:
        df = pd.DataFrame(resultados)

        st.success(f"**{len(df)}** empresas passaram nos filtros (de {len(TICKERS)}).")

        # Opcao de ordenacao
        col_ordem = st.selectbox(
            "Ordenar por:",
            ["ROE %", "DY %", "P/L", "P/VP", "EV/EBITDA", "Margem Líq. %", "Cresc. 5a %"],
        )
        asc = col_ordem in ["P/L", "P/VP", "EV/EBITDA"]
        df = df.sort_values(col_ordem, ascending=asc, na_position="last").reset_index(drop=True)
        df.index += 1

        st.dataframe(
            df.style.format({
                "Cotação": "R$ {:.2f}",
                "P/L": "{:.2f}",
                "P/VP": "{:.2f}",
                "EV/EBITDA": "{:.2f}",
                "ROE %": "{:.1f}%",
                "ROIC %": "{:.1f}%",
                "DY %": "{:.1f}%",
                "Margem Líq. %": "{:.1f}%",
                "Margem EBIT %": "{:.1f}%",
                "Liq. Corrente": "{:.2f}",
                "Cresc. 5a %": "{:.1f}%",
                "Lucro 12m": "R$ {:,.0f}",
            }, na_rep="N/A"),
            width="stretch",
            height=500,
        )

        st.divider()

        # Graficos
        col1, col2 = st.columns(2)

        with col1:
            fig = px.scatter(
                df, x="P/L", y="ROE %",
                size="DY %", color="DY %",
                hover_name="Ticker",
                title="P/L vs ROE (tamanho = DY)",
                color_continuous_scale="YlGn",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width="stretch")

        with col2:
            fig = px.scatter(
                df, x="EV/EBITDA", y="Margem Líq. %",
                size="ROE %", color="ROE %",
                hover_name="Ticker",
                title="EV/EBITDA vs Margem Líquida (tamanho = ROE)",
                color_continuous_scale="YlGn",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width="stretch")

    else:
        st.warning("Nenhuma empresa passou em todos os filtros. Tente relaxar os critérios.")

st.caption("Fonte: fundamentus.com.br")
