import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.collectors.fundamentus_collector import FundamentusCollector  # noqa: E402
from src.processors.score_calculator import ScoreCalculator  # noqa: E402
from src.processors.technical_calculator import TechnicalCalculator  # noqa: E402
from dashboard.components.ticker_selector import ticker_multiselect  # noqa: E402

st.title("Ranking de Ações por Score Composto")

TICKERS_PADRAO = [
    "WEGE3", "ITUB4", "BBAS3", "VALE3", "PETR4",
    "EGIE3", "TAEE11", "CPFE3", "SUZB3", "KLBN11",
    "RDOR3", "FLRY3", "TOTS3", "SLCE3", "JBSS3",
    "BBDC4", "SANB11", "PRIO3", "VIVT3", "ABEV3",
]

with st.expander("⚙️ Configurações", expanded=True):
    col_uni, col_pesos = st.columns([3, 4])

    with col_uni:
        st.markdown("**Universo**")
        usar_padrao = st.checkbox("Usar lista padrão (20 ações)", value=True)
        if usar_padrao:
            tickers = TICKERS_PADRAO
        else:
            tickers = ticker_multiselect(
                "Selecione ações:",
                default=["WEGE3", "ITUB4", "VALE3"],
                key="ranking_custom",
                sidebar=False,
            )

    with col_pesos:
        st.markdown("**Pesos do Score**")
        c1, c2, c3, c4, c5 = st.columns(5)
        p_saude = c1.slider("Saúde", 0, 50, 30, key="rk_saude")
        p_val = c2.slider("Valuation", 0, 50, 25, key="rk_val")
        p_div = c3.slider("Dividendos", 0, 50, 20, key="rk_div")
        p_cres = c4.slider("Crescimento", 0, 50, 15, key="rk_cres")
        p_tec = c5.slider("Técnico", 0, 50, 10, key="rk_tec")

if st.button("Calcular Ranking", type="primary"):
    fund = FundamentusCollector()
    brapi = BrapiCollector()
    calc = ScoreCalculator()
    calc.PESOS = {
        "saude": p_saude, "valuation": p_val,
        "dividendos": p_div, "crescimento": p_cres, "tecnico": p_tec,
    }

    resultados = []
    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"Analisando {ticker} ({i + 1}/{len(tickers)})...")
        try:
            dados = fund.get_papel(ticker)

            # Indicadores tecnicos
            sinais = {}
            try:
                historico = brapi.get_historico(ticker, "3mo", "1d")
                if historico and len(historico) > 30:
                    df_h = pd.DataFrame(historico)
                    df_h["date"] = pd.to_datetime(df_h["date"], unit="s")
                    df_tech = TechnicalCalculator.calcular_todos(df_h)
                    sinais = TechnicalCalculator.gerar_sinais(df_tech)
            except Exception:
                pass

            # Calcular scores
            s_saude, _ = calc.score_saude(dados)
            s_val, _ = calc.score_valuation(dados)
            s_div, _ = calc.score_dividendos(dados)
            s_cres, _ = calc.score_crescimento(dados)
            s_tec, _ = calc.score_tecnico(sinais)

            scores = {
                "saude": s_saude, "valuation": s_val,
                "dividendos": s_div, "crescimento": s_cres, "tecnico": s_tec,
            }
            s_geral = calc.score_geral(scores)

            resultados.append({
                "Ticker": ticker,
                "Empresa": (dados.get("empresa") or ticker)[:25],
                "Cotação": dados.get("cotacao") or 0,
                "Score": s_geral,
                "Saúde": s_saude,
                "Valuation": s_val,
                "Dividendos": s_div,
                "Crescimento": s_cres,
                "Técnico": s_tec,
                "P/L": dados.get("pl"),
                "DY %": dados.get("dividend_yield"),
                "ROE %": dados.get("roe"),
            })
            time.sleep(0.3)
        except Exception as e:
            st.warning(f"{ticker}: {e}")
        progress.progress((i + 1) / len(tickers))

    progress.empty()
    status.empty()

    if resultados:
        df = pd.DataFrame(resultados).sort_values("Score", ascending=False).reset_index(drop=True)
        df.index += 1

        # --- Tabela principal ---
        st.subheader("Ranking Geral")

        def colorir_score(val):
            if val >= 70:
                return "background-color: #2d6a2e; color: white"
            elif val >= 50:
                return "background-color: #c9a200; color: black"
            elif val >= 30:
                return "background-color: #cc7722; color: white"
            else:
                return "background-color: #a82020; color: white"

        cols_show = ["Ticker", "Empresa", "Score", "Saúde", "Valuation", "Dividendos", "Crescimento", "Técnico", "P/L", "DY %", "ROE %", "Cotação"]
        styled = df[cols_show].style.map(
            colorir_score,
            subset=["Score", "Saúde", "Valuation", "Dividendos", "Crescimento", "Técnico"],
        ).format({"Cotação": "R$ {:.2f}", "P/L": "{:.2f}", "DY %": "{:.1f}%", "ROE %": "{:.1f}%"}, na_rep="N/A")

        st.dataframe(styled, width="stretch", height=500)

        st.divider()

        # --- Grafico Top 10 ---
        st.subheader("Top 10 - Comparação por Dimensão")
        top10 = df.head(10)
        df_melt = top10.melt(
            id_vars=["Ticker"],
            value_vars=["Saúde", "Valuation", "Dividendos", "Crescimento", "Técnico"],
        )
        fig = px.bar(
            df_melt,
            x="variable", y="value", color="Ticker",
            barmode="group",
            title="Top 10 Ações - Scores por Dimensão",
            labels={"variable": "Dimensão", "value": "Score (0-100)"},
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, width="stretch")

        # --- Radar do Top 5 ---
        st.subheader("Top 5 - Gráfico Radar")
        import plotly.graph_objects as go

        top5 = df.head(5)
        categorias = ["Saúde", "Valuation", "Dividendos", "Crescimento", "Técnico"]

        fig = go.Figure()
        for _, row in top5.iterrows():
            valores = [row[c] for c in categorias] + [row[categorias[0]]]
            fig.add_trace(go.Scatterpolar(
                r=valores,
                theta=categorias + [categorias[0]],
                fill="toself",
                name=row["Ticker"],
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=500,
            title="Radar - Top 5 Ações",
        )
        st.plotly_chart(fig, width="stretch")

    else:
        st.warning("Nenhum resultado. Verifique os tickers.")

st.caption("Fontes: fundamentus.com.br (fundamentos) | brapi.dev (técnicos)")
