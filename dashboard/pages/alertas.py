import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.alerts.alert_engine import AlertEngine  # noqa: E402
from src.collectors.b3_collector import B3Collector, SETORES_B3  # noqa: E402
from dashboard.components.ticker_selector import ticker_selectbox, ticker_multiselect  # noqa: E402

st.title("Painel de Alertas - Cruzamento de Dados")

ICONES = {
    "CRITICO": "🔴",
    "ALTO": "🟠",
    "MEDIO": "🟡",
    "INFO": "🔵",
}

# --- Opcoes de analise ---
opcao = st.radio(
    "Analisar:",
    ["Ticker especifico", "Lista personalizada", "Setor completo"],
    horizontal=True,
)

tickers_alvo = []

if opcao == "Ticker especifico":
    t = ticker_selectbox("Selecione a ação:", default="PETR4", key="alertas_ticker")
    tickers_alvo = [t] if t else []

elif opcao == "Lista personalizada":
    tickers_alvo = ticker_multiselect(
        "Selecione ações:",
        default=["PETR4", "VALE3", "ITUB4", "MGLU3", "WEGE3"],
        key="alertas_multi",
    )

elif opcao == "Setor completo":
    setor = st.selectbox("Selecione o setor:", list(SETORES_B3.keys()))
    tickers_alvo = SETORES_B3[setor]
    st.caption(f"Empresas: {', '.join(tickers_alvo)}")

# Filtros
severidades = st.multiselect(
    "Filtrar por severidade:",
    ["CRITICO", "ALTO", "MEDIO", "INFO"],
    default=["CRITICO", "ALTO", "MEDIO"],
)

if tickers_alvo and st.button("Executar Análise", type="primary"):
    engine = AlertEngine()
    todos_alertas = []

    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers_alvo):
        status.text(f"Analisando {ticker} ({i + 1}/{len(tickers_alvo)})...")
        try:
            alertas = engine.analisar_ticker(ticker)
            for a in alertas:
                if a.severidade in severidades:
                    todos_alertas.append({
                        "severidade_raw": a.severidade,
                        "Severidade": f"{ICONES.get(a.severidade, '')} {a.severidade}",
                        "Ticker": a.ticker,
                        "Tipo": a.tipo,
                        "Alerta": a.titulo,
                        "Descrição": a.descricao,
                    })
        except Exception as e:
            st.warning(f"{ticker}: {e}")
        progress.progress((i + 1) / len(tickers_alvo))

    progress.empty()
    status.empty()

    if todos_alertas:
        df = pd.DataFrame(todos_alertas)

        # --- Resumo ---
        st.subheader("Resumo")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total", len(df))
        col2.metric("🔴 Criticos", len(df[df["severidade_raw"] == "CRITICO"]))
        col3.metric("🟠 Altos", len(df[df["severidade_raw"] == "ALTO"]))
        col4.metric("🟡 Medios", len(df[df["severidade_raw"] == "MEDIO"]))
        col5.metric("🔵 Info", len(df[df["severidade_raw"] == "INFO"]))

        st.divider()

        # --- Distribuicao por tipo ---
        col1, col2 = st.columns(2)

        with col1:
            tipo_count = df["Tipo"].value_counts().reset_index()
            tipo_count.columns = ["Tipo", "Qtd"]
            fig = px.bar(
                tipo_count.head(10),
                x="Qtd", y="Tipo",
                orientation="h",
                title="Alertas por Tipo",
                color="Qtd",
                color_continuous_scale="OrRd",
            )
            fig.update_layout(height=350, showlegend=False, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, width="stretch")

        with col2:
            ticker_count = df["Ticker"].value_counts().reset_index()
            ticker_count.columns = ["Ticker", "Qtd"]
            fig = px.bar(
                ticker_count.head(10),
                x="Qtd", y="Ticker",
                orientation="h",
                title="Alertas por Empresa",
                color="Qtd",
                color_continuous_scale="OrRd",
            )
            fig.update_layout(height=350, showlegend=False, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, width="stretch")

        st.divider()

        # --- Tabela de alertas ---
        st.subheader("Todos os Alertas")
        st.dataframe(
            df[["Severidade", "Ticker", "Tipo", "Alerta"]],
            width="stretch",
            hide_index=True,
            height=400,
        )

        # --- Detalhe por empresa ---
        st.divider()
        st.subheader("Detalhes por Empresa")
        ticker_sel = st.selectbox("Ver detalhes de:", sorted(df["Ticker"].unique()))

        if ticker_sel:
            df_sel = df[df["Ticker"] == ticker_sel]
            for _, row in df_sel.iterrows():
                icon = ICONES.get(row["severidade_raw"], "")
                with st.expander(f"{icon} {row['severidade_raw']} | {row['Alerta']}"):
                    st.write(f"**Tipo:** {row['Tipo']}")
                    st.write(row["Descrição"])

    else:
        st.success("Nenhum alerta detectado para os filtros selecionados.")

st.caption("Fontes: fundamentus.com.br (indicadores) | BCB (dados macro)")
