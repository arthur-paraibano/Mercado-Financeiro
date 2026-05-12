import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.b3_collector import B3Collector  # noqa: E402
from src.collectors.brapi_collector import BrapiCollector  # noqa: E402

st.title("Visão Geral - Mercado Brasileiro")


@st.cache_data(ttl=600)
def carregar_ibovespa():
    b3 = B3Collector()
    return b3.get_composicao_ibovespa()


composicao = carregar_ibovespa()

if composicao.empty:
    st.error("Não foi possível carregar a composicao do Ibovespa.")
    st.stop()

# --- Metricas gerais ---
col1, col2, col3 = st.columns(3)
col1.metric("Ações no Ibovespa", len(composicao))

if "peso" in composicao.columns:
    top1 = composicao.nlargest(1, "peso").iloc[0]
    col2.metric("Maior Peso", f"{top1['ticker']} ({top1['peso']:.2f}%)")
    top5_peso = composicao.nlargest(5, "peso")["peso"].sum()
    col3.metric("Concentração Top 5", f"{top5_peso:.1f}%")

st.divider()

# --- Top 20 por peso ---
if "peso" in composicao.columns:
    st.subheader("Top 20 - Maiores Pesos no Ibovespa")
    top20 = composicao.nlargest(20, "peso")
    fig = px.bar(
        top20,
        x="ticker",
        y="peso",
        color="peso",
        color_continuous_scale="Blues",
        title="",
        labels={"peso": "Peso (%)", "ticker": ""},
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, width="stretch")

st.divider()

# --- Distribuicao por Setor ---
st.subheader("Distribuição por Setor")
df_setor = composicao.dropna(subset=["setor"])

if not df_setor.empty:
    setor_peso = (
        df_setor.groupby("setor")["peso"]
        .sum()
        .reset_index()
        .sort_values("peso", ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(
            setor_peso,
            names="setor",
            values="peso",
            title="Peso por Setor (%)",
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig = px.bar(
            setor_peso,
            x="peso",
            y="setor",
            orientation="h",
            title="Peso por Setor",
            labels={"peso": "Peso (%)", "setor": ""},
        )
        fig.update_layout(height=450, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")
else:
    st.info("Classificação setorial parcial. Nem todas as ações possuem setor mapeado.")

st.divider()

# --- Cotacoes rapidas do Top 10 ---
st.subheader("Cotações Atuais - Top 10")

if "peso" in composicao.columns:
    top10_tickers = composicao.nlargest(10, "peso")["ticker"].tolist()
else:
    top10_tickers = composicao["ticker"].head(10).tolist()

brapi = BrapiCollector()
cotacoes = []

progress = st.progress(0)
for i, t in enumerate(top10_tickers):
    try:
        d = brapi.get_cotacao(t)
        cotacoes.append({
            "Ticker": t,
            "Preço": f"R$ {d.get('regularMarketPrice', 0):.2f}",
            "Variação": f"{d.get('regularMarketChangePercent', 0):.2f}%",
            "Market Cap": f"R$ {d.get('marketCap', 0) / 1e9:.1f}B" if d.get("marketCap") else "N/A",
            "Volume": f"{d.get('regularMarketVolume', 0):,.0f}",
        })
    except Exception:
        pass
    progress.progress((i + 1) / len(top10_tickers))

progress.empty()

if cotacoes:
    st.dataframe(pd.DataFrame(cotacoes), width="stretch", hide_index=True)

st.divider()

# --- Tabela completa ---
st.subheader("Todas as Ações do Ibovespa")
cols_show = [c for c in ["ticker", "nome", "peso", "setor"] if c in composicao.columns]
st.dataframe(
    composicao[cols_show].sort_values("peso", ascending=False) if "peso" in composicao.columns else composicao[cols_show],
    width="stretch",
    hide_index=True,
    height=400,
)

st.caption("Fonte: B3 - Composicao do Ibovespa")
