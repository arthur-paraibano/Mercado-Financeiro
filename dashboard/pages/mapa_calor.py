import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.collectors.b3_collector import SETORES_B3  # noqa: E402

st.title("🌡️ Mapa de Calor do Mercado")
st.caption("Variação percentual do dia por setor. Verde = alta, Vermelho = queda.")

# --- Configurações ---
with st.expander("⚙️ Configurações", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        setores_opcoes = ["Todos"] + sorted(SETORES_B3.keys())
        setor_filtro = st.selectbox("Setor:", setores_opcoes)
    with col2:
        escala = st.slider("Escala de cor (% max)", 1, 10, 5)

if st.button("Atualizar Mapa", type="primary"):
    brapi = BrapiCollector()

    # Montar lista de tickers filtrada
    if setor_filtro == "Todos":
        tickers_por_setor = SETORES_B3
    else:
        tickers_por_setor = {setor_filtro: SETORES_B3[setor_filtro]}

    todos_tickers = []
    for setor, tickers in tickers_por_setor.items():
        for t in tickers:
            todos_tickers.append((setor, t))

    # Remover duplicatas mantendo primeiro setor encontrado
    vistos = set()
    tickers_unicos = []
    for setor, t in todos_tickers:
        if t not in vistos:
            vistos.add(t)
            tickers_unicos.append((setor, t))

    # Carregar todas as cotacoes em lote (muito mais rapido)
    with st.spinner(f"Carregando {len(tickers_unicos)} cotações em lote..."):
        tickers_apenas = [t for _, t in tickers_unicos]
        cotacoes = brapi.get_cotacao_lote(tickers_apenas)

    rows = []
    for setor, ticker in tickers_unicos:
        dados = cotacoes.get(ticker)
        if dados:
            variacao = dados.get("regularMarketChangePercent", 0) or 0
            preco = dados.get("regularMarketPrice", 0) or 0
            volume = dados.get("regularMarketVolume", 0) or 0
            market_cap = dados.get("marketCap", 0) or 0
            nome = dados.get("shortName", ticker) or ticker
            rows.append({
                "Setor": setor,
                "Ticker": ticker,
                "Nome": nome[:25],
                "Variação %": round(variacao, 2),
                "Preço": preco,
                "Volume": volume,
                "MarketCap": max(market_cap, 1),
            })
        else:
            rows.append({
                "Setor": setor,
                "Ticker": ticker,
                "Nome": ticker,
                "Variação %": 0.0,
                "Preço": 0.0,
                "Volume": 0,
                "MarketCap": 1,
            })

    if not rows:
        st.error("Nenhum dado carregado.")
        st.stop()

    df = pd.DataFrame(rows)

    # ========================================
    # Treemap principal
    # ========================================
    fig = px.treemap(
        df,
        path=["Setor", "Ticker"],
        values="MarketCap",
        color="Variação %",
        color_continuous_scale="RdYlGn",
        range_color=[-escala, escala],
        color_continuous_midpoint=0,
        custom_data=["Nome", "Preço", "Variação %", "Volume"],
        title="Mapa de Calor — Variação do Dia (%)",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Empresa: %{customdata[0]}<br>"
            "Preço: R$ %{customdata[1]:.2f}<br>"
            "Variação: %{customdata[2]:+.2f}%<br>"
            "Volume: %{customdata[3]:,.0f}<br>"
            "<extra></extra>"
        ),
        texttemplate="<b>%{label}</b><br>%{customdata[2]:+.1f}%",
    )

    fig.update_layout(
        height=600,
        coloraxis_colorbar=dict(
            title="Variação %",
            tickvals=[-escala, -escala / 2, 0, escala / 2, escala],
            ticktext=[f"-{escala}%", f"-{escala/2:.0f}%", "0%", f"+{escala/2:.0f}%", f"+{escala}%"],
        ),
    )

    st.plotly_chart(fig, width="stretch")

    # ========================================
    # Tabela detalhada
    # ========================================
    st.divider()
    st.subheader("Detalhes por Ação")

    df_show = df[["Setor", "Ticker", "Nome", "Preço", "Variação %", "Volume"]].copy()
    df_show = df_show.sort_values("Variação %", ascending=False).reset_index(drop=True)

    def cor_variacao(val):
        if val > 2:
            return "background-color: #1a5c1a; color: white"
        elif val > 0:
            return "background-color: #2d6a2e; color: white"
        elif val < -2:
            return "background-color: #8c1a1a; color: white"
        elif val < 0:
            return "background-color: #7a2020; color: white"
        return ""

    styled = df_show.style.map(cor_variacao, subset=["Variação %"]).format({
        "Preço": "R$ {:.2f}",
        "Variação %": "{:+.2f}%",
        "Volume": "{:,.0f}",
    })

    st.dataframe(styled, width="stretch", hide_index=True, height=400)

    # ========================================
    # Resumo por setor
    # ========================================
    st.divider()
    st.subheader("Variação Média por Setor")

    df_setor = (
        df.groupby("Setor")["Variação %"]
        .mean()
        .reset_index()
        .sort_values("Variação %", ascending=True)
    )

    fig2 = px.bar(
        df_setor,
        x="Variação %",
        y="Setor",
        orientation="h",
        color="Variação %",
        color_continuous_scale="RdYlGn",
        range_color=[-escala, escala],
        color_continuous_midpoint=0,
        title="Média de Variação por Setor (%)",
    )
    fig2.update_layout(height=400, showlegend=False)
    fig2.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
    st.plotly_chart(fig2, width="stretch")

else:
    st.info("Clique em **Atualizar Mapa** para carregar as cotações do dia.")

    # Preview estatico do mapa com dados ficticios
    st.markdown("""
**Como usar:**
- Cada quadrado representa uma ação
- O tamanho e proporcional ao market cap
- Verde = alta no dia, Vermelho = queda
- Use o filtro de setor para focar em um segmento especifico
- Ajuste a escala de cor para ampliar ou reduzir a sensibilidade visual
    """)

st.caption("Fonte: brapi.dev | Setores: mapeamento B3")
