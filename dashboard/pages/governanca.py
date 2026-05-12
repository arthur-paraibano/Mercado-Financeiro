import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.cvm_governanca_collector import (  # noqa: E402
    CVMGovernancaCollector,
    EMPRESAS_NIVEL,
)
from dashboard.components.ticker_selector import ticker_multiselect  # noqa: E402

st.title("Governança Corporativa")

st.info(
    "Score de governança baseado no nivel de listagem na B3. "
    "Empresas no Novo Mercado possuem as regras mais rigidas de protecao ao acionista minoritario."
)

gov = CVMGovernancaCollector()

# --- Selecao de empresas ---
tickers = ticker_multiselect(
    "Selecione empresas para comparar:",
    default=["WEGE3", "ITUB4", "PETR4", "VALE3", "BBDC4", "MGLU3", "CMIG4", "BBAS3"],
    key="gov_tickers",
)

if tickers and st.button("Analisar Governança", type="primary"):
    resultados = gov.comparar_governanca(tickers)

    if resultados:
        df = pd.DataFrame(resultados)

        # --- Grafico de barras ---
        cores_nivel = {
            "Novo Mercado": "#2ca02c",
            "Nivel 2": "#1f77b4",
            "Nivel 1": "#ff7f0e",
            "Tradicional": "#d62728",
        }

        fig = px.bar(
            df,
            x="ticker", y="score_final",
            color="nivel",
            color_discrete_map=cores_nivel,
            title="Score de Governança por Empresa",
            labels={"score_final": "Score (0-100)", "ticker": ""},
            text="score_final",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(height=450, yaxis_range=[0, 110])
        st.plotly_chart(fig, width="stretch")

        st.divider()

        # --- Metricas resumidas ---
        col1, col2, col3, col4 = st.columns(4)
        nm_count = len(df[df["nivel_codigo"] == "NM"])
        n1_count = len(df[df["nivel_codigo"] == "N1"])
        n2_count = len(df[df["nivel_codigo"] == "N2"])
        tr_count = len(df[df["nivel_codigo"] == "TR"])

        col1.metric("Novo Mercado", nm_count)
        col2.metric("Nivel 2", n2_count)
        col3.metric("Nivel 1", n1_count)
        col4.metric("Tradicional", tr_count)

        st.divider()

        # --- Tabela detalhada ---
        st.subheader("Detalhes")
        df_show = df[["ticker", "nivel", "tag_along", "score_base", "score_final"]].copy()
        df_show["ajustes"] = df["ajustes"].apply(lambda x: " | ".join(x) if x else "-")
        df_show.columns = ["Ticker", "Nivel", "Tag Along %", "Score Base", "Score Final", "Ajustes"]

        def cor_score(val):
            if val >= 80:
                return "background-color: #2d6a2e; color: white"
            elif val >= 60:
                return "background-color: #c9a200; color: black"
            else:
                return "background-color: #a82020; color: white"

        st.dataframe(
            df_show.style.map(cor_score, subset=["Score Final"]),
            width="stretch",
            hide_index=True,
        )

        st.divider()

        # --- Distribuicao por nivel ---
        st.subheader("Distribuição por Nivel de Listagem")
        nivel_count = df["nivel"].value_counts().reset_index()
        nivel_count.columns = ["Nivel", "Quantidade"]

        fig = px.pie(
            nivel_count,
            names="Nivel", values="Quantidade",
            color="Nivel",
            color_discrete_map=cores_nivel,
            title="Distribuição das Empresas Selecionadas",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

        # --- Legenda ---
        st.divider()
        st.subheader("Legenda dos Niveis de Listagem")

        st.markdown("""
| Nivel | Tag Along | Descrição |
|---|---|---|
| **Novo Mercado (NM)** | 100% | Mais alto nivel. Apenas ações ON (1 ação = 1 voto). Conselho com mínimo 5 membros, 20% independentes. |
| **Nivel 2 (N2)** | 100% | Tag along 100%. Ações PN com direitos especiais. Camara de arbitragem. |
| **Nivel 1 (N1)** | 80% | Free float mínimo de 25%. Obrigacoes adicionais de divulgacao. |
| **Tradicional (TR)** | 80% ON | Regras mínimas da lei. Menor protecao ao minoritario. |

**Tag Along:** direito do minoritario receber percentual do preço pago ao controlador em caso de venda do controle.
        """)
    else:
        st.warning("Nenhum resultado. Verifique os tickers.")

st.caption("Fonte: B3 - Niveis de Governança Corporativa")
