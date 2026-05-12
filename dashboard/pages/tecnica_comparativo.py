import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.processors.technical_calculator import TechnicalCalculator  # noqa: E402
from dashboard.components.ticker_selector import ticker_selectbox, TICKERS_DISPONIVEIS  # noqa: E402

def make_subplots_for_prices(dados, cores):
    """Cria gráfico com eixo Y duplo para ações com preços muito diferentes."""
    from plotly.subplots import make_subplots as _make_subplots

    tickers_list = list(dados.keys())
    fig = _make_subplots(specs=[[{"secondary_y": True}]])

    for i, (ticker, df) in enumerate(dados.items()):
        secondary = i > 0
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["close"],
                name=ticker, line=dict(color=cores[i % 3], width=2),
            ),
            secondary_y=secondary,
        )

    fig.update_yaxes(title_text=tickers_list[0], secondary_y=False)
    if len(tickers_list) > 1:
        fig.update_yaxes(title_text=" / ".join(tickers_list[1:]), secondary_y=True)

    fig.update_layout(height=400, legend=dict(orientation="h", y=1.05))
    return fig


st.title("🔀 Comparativo de Ações")

# --- Selecao ---
col1, col2, col3 = st.columns(3)
with col1:
    ticker1 = ticker_selectbox("Ação 1:", default="PETR4", key="comp_t1")
with col2:
    ticker2 = ticker_selectbox("Ação 2:", default="VALE3", key="comp_t2")
with col3:
    opcoes_3 = ["(nenhuma)"] + [f"{t} - {n}" for t, n in TICKERS_DISPONIVEIS.items()]
    sel3 = st.selectbox("Ação 3 (opcional):", opcoes_3, index=0, key="comp_t3")
    ticker3 = sel3.split(" - ")[0].strip() if sel3 != "(nenhuma)" else ""

periodo = st.selectbox("Período:", ["1mo", "3mo"], index=1)

tickers = [t for t in [ticker1, ticker2, ticker3] if t]

if len(tickers) < 2:
    st.info("Selecione pelo menos 2 ações para comparar.")
    st.stop()

if st.button("Comparar", type="primary"):
    brapi = BrapiCollector()
    dados = {}

    with st.spinner("Carregando dados..."):
        for ticker in tickers:
            try:
                hist = brapi.get_historico(ticker, periodo, "1d")
                if hist and len(hist) > 5:
                    df = pd.DataFrame(hist)
                    df["date"] = pd.to_datetime(df["date"], unit="s")
                    df = df.sort_values("date").reset_index(drop=True)
                    dados[ticker] = df
            except Exception as e:
                st.warning(f"{ticker}: {e}")

    if len(dados) < 2:
        st.error("Dados insuficientes para comparação.")
        st.stop()

    # ========================================
    # 1. Performance Relativa (normalizada)
    # ========================================
    st.subheader("Performance Relativa (%)")
    st.caption("Todas as ações normalizadas para 100 no inicio do período")

    fig = go.Figure()
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for i, (ticker, df) in enumerate(dados.items()):
        base = df["close"].iloc[0]
        df["normalizado"] = (df["close"] / base) * 100
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["normalizado"],
            name=ticker, line=dict(color=cores[i % 3], width=2),
        ))

    fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        height=400,
        yaxis_title="Performance (%)",
        legend=dict(orientation="h", y=1.05),
    )
    st.plotly_chart(fig, width="stretch")

    # Metricas de performance
    st.subheader("Resumo de Performance")
    cols = st.columns(len(dados))
    for i, (ticker, df) in enumerate(dados.items()):
        retorno = ((df["close"].iloc[-1] / df["close"].iloc[0]) - 1) * 100
        volatilidade = df["close"].pct_change().std() * np.sqrt(252) * 100
        maxima = df["high"].max()
        minima = df["low"].min()

        with cols[i]:
            st.markdown(f"**{ticker}**")
            st.metric("Retorno", f"{retorno:+.2f}%")
            st.metric("Volatilidade (anualiz.)", f"{volatilidade:.1f}%")
            st.metric("Máxima", f"R$ {máxima:.2f}")
            st.metric("Mínima", f"R$ {mínima:.2f}")

    st.divider()

    # ========================================
    # 2. Graficos Sobrepostos (preco real)
    # ========================================
    st.subheader("Cotações Sobrepostas")

    fig2 = make_subplots_for_prices(dados, cores)
    st.plotly_chart(fig2, width="stretch")

    st.divider()

    # ========================================
    # 3. Volume Comparativo
    # ========================================
    st.subheader("Volume Diário")
    fig3 = go.Figure()
    for i, (ticker, df) in enumerate(dados.items()):
        fig3.add_trace(go.Bar(
            x=df["date"], y=df["volume"],
            name=ticker, opacity=0.6,
            marker_color=cores[i % 3],
        ))
    fig3.update_layout(height=300, barmode="group", legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig3, width="stretch")

    st.divider()

    # ========================================
    # 4. Correlacao
    # ========================================
    st.subheader("Correlacao de Retornos")

    # Alinhar datas
    retornos = {}
    for ticker, df in dados.items():
        ret = df.set_index("date")["close"].pct_change().dropna()
        retornos[ticker] = ret

    df_ret = pd.DataFrame(retornos).dropna()

    if len(df_ret) > 5:
        corr = df_ret.corr()

        fig4 = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdYlGn",
            zmin=-1, zmax=1,
            title="Matriz de Correlacao (retornos diários)",
        )
        fig4.update_layout(height=350)
        st.plotly_chart(fig4, width="stretch")

        # Interpretacao
        for i, t1 in enumerate(corr.columns):
            for j, t2 in enumerate(corr.columns):
                if i < j:
                    val = corr.iloc[i, j]
                    if val > 0.7:
                        st.info(f"**{t1}** e **{t2}** tem correlacao alta ({val:.2f}) - tendem a se mover juntas.")
                    elif val < -0.3:
                        st.info(f"**{t1}** e **{t2}** tem correlacao negativa ({val:.2f}) - bom para diversificação.")

    # ========================================
    # 5. Sinais Tecnicos Comparados
    # ========================================
    st.divider()
    st.subheader("Sinais Técnicos Comparados")

    sinais_comp = []
    for ticker, df in dados.items():
        df_tech = TechnicalCalculator.calcular_todos(df)
        sinais = TechnicalCalculator.gerar_sinais(df_tech)

        row = {"Ticker": ticker}
        for nome, info in sinais.items():
            sinal = info.get("sinal", "NEUTRO")
            icone = "🟢" if sinal == "COMPRA" else "🔴" if sinal == "VENDA" else "⚪"
            row[nome] = f"{icone} {sinal}"
        sinais_comp.append(row)

    st.dataframe(pd.DataFrame(sinais_comp), width="stretch", hide_index=True)

st.caption("Fonte: brapi.dev | Indicadores calculados com pandas")
