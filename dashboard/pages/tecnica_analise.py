import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.processors.technical_calculator import TechnicalCalculator  # noqa: E402
from dashboard.components.ticker_selector import ticker_selectbox  # noqa: E402

st.title("📈 Análise Técnica")

# --- Sidebar ---
ticker = ticker_selectbox("Selecione a ação:", default="PETR4", key="tec_analise_ticker", sidebar=True)
periodo = st.sidebar.selectbox("Período:", ["1mo", "3mo"], index=1)

st.sidebar.subheader("Overlays")
show_sma20 = st.sidebar.checkbox("SMA 20", value=True)
show_sma50 = st.sidebar.checkbox("SMA 50", value=True)
show_ema9 = st.sidebar.checkbox("EMA 9", value=False)
show_ema21 = st.sidebar.checkbox("EMA 21", value=False)
show_bollinger = st.sidebar.checkbox("Bollinger Bands", value=True)

st.sidebar.subheader("Sub-gráficos")
show_rsi = st.sidebar.checkbox("RSI (14)", value=True)
show_macd = st.sidebar.checkbox("MACD", value=True)
show_volume = st.sidebar.checkbox("Volume", value=True)

if st.button("Analisar", type="primary") or ticker:
    brapi = BrapiCollector()

    with st.spinner(f"Carregando {ticker}..."):
        try:
            historico = brapi.get_historico(ticker, periodo, "1d")
        except Exception as e:
            st.error(f"Erro ao buscar {ticker}: {e}")
            st.stop()

    if not historico or len(historico) < 10:
        st.warning("Dados insuficientes para análise técnica.")
        st.stop()

    df = pd.DataFrame(historico)
    df["date"] = pd.to_datetime(df["date"], unit="s")
    df = TechnicalCalculator.calcular_todos(df)
    sinais = TechnicalCalculator.gerar_sinais(df)

    # --- Sinais atuais ---
    st.subheader(f"Sinais Atuais - {ticker}")
    cols = st.columns(min(len(sinais), 5)) if sinais else []
    for i, (nome, info) in enumerate(sinais.items()):
        sinal = info.get("sinal", "NEUTRO")
        icone = "🟢" if sinal == "COMPRA" else "🔴" if sinal == "VENDA" else "⚠️" if sinal == "ATENCAO" else "⚪"
        cols[i % len(cols)].metric(f"{icone} {nome}", sinal, info.get("desc", "")[:35])

    st.divider()

    # --- Calcular altura dos sub-graficos ---
    sub_count = sum([show_rsi, show_macd, show_volume])
    total_rows = 1 + sub_count
    row_heights = [0.5] + [0.5 / max(sub_count, 1)] * sub_count if sub_count > 0 else [1.0]

    specs = [[{"secondary_y": False}]] * total_rows
    subtitles = [f"{ticker} - Candlestick"]
    if show_rsi:
        subtitles.append("RSI (14)")
    if show_macd:
        subtitles.append("MACD")
    if show_volume:
        subtitles.append("Volume")

    fig = make_subplots(
        rows=total_rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=subtitles,
    )

    # --- Candlestick ---
    fig.add_trace(
        go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"],
            low=df["low"], close=df["close"], name="OHLC",
            increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # Overlays
    if show_sma20 and "sma_20" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["sma_20"], name="SMA 20", line=dict(color="#ff9800", width=1)), row=1, col=1)
    if show_sma50 and "sma_50" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["sma_50"], name="SMA 50", line=dict(color="#2196f3", width=1)), row=1, col=1)
    if show_ema9 and "ema_9" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ema_9"], name="EMA 9", line=dict(color="#e91e63", width=1, dash="dot")), row=1, col=1)
    if show_ema21 and "ema_21" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ema_21"], name="EMA 21", line=dict(color="#9c27b0", width=1, dash="dot")), row=1, col=1)

    if show_bollinger:
        if "bollinger_upper" in df.columns:
            fig.add_trace(go.Scatter(x=df["date"], y=df["bollinger_upper"], name="BB Superior", line=dict(color="rgba(150,150,150,0.4)", width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df["date"], y=df["bollinger_lower"], name="BB Inferior", line=dict(color="rgba(150,150,150,0.4)", width=1), fill="tonexty", fillcolor="rgba(150,150,150,0.08)"), row=1, col=1)

    # --- Sub-graficos ---
    current_row = 2

    if show_rsi and "rsi_14" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["rsi_14"], name="RSI 14", line=dict(color="#7c4dff", width=1.5)), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)
        fig.add_hrect(y0=30, y1=70, fillcolor="rgba(150,150,150,0.05)", line_width=0, row=current_row, col=1)
        current_row += 1

    if show_macd and "macd" in df.columns:
        cores_hist = ["#26a69a" if v >= 0 else "#ef5350" for v in df["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df["date"], y=df["macd_hist"], name="MACD Hist", marker_color=cores_hist), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df["date"], y=df["macd"], name="MACD", line=dict(color="#2196f3", width=1.5)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df["date"], y=df["macd_signal"], name="Signal", line=dict(color="#ff9800", width=1)), row=current_row, col=1)
        current_row += 1

    if show_volume and "volume" in df.columns:
        cores_vol = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(df["close"], df["open"])]
        fig.add_trace(go.Bar(x=df["date"], y=df["volume"], name="Volume", marker_color=cores_vol, opacity=0.7), row=current_row, col=1)
        if "volume_sma_20" in df.columns:
            fig.add_trace(go.Scatter(x=df["date"], y=df["volume_sma_20"], name="Vol SMA 20", line=dict(color="#ff9800", width=1)), row=current_row, col=1)

    # Layout
    fig.update_layout(
        height=200 + (250 * total_rows),
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", y=1.02, x=0),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    fig.update_xaxes(type="date")

    st.plotly_chart(fig, width="stretch")

    # --- Dados da ultima barra ---
    st.divider()
    st.subheader("Dados do Último Pregao")
    ultima = df.iloc[-1]
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Fechamento", f"R$ {última['close']:.2f}")
    col2.metric("Abertura", f"R$ {última['open']:.2f}")
    col3.metric("Máxima", f"R$ {última['high']:.2f}")
    col4.metric("Mínima", f"R$ {última['low']:.2f}")
    col5.metric("Volume", f"{última['volume']:,.0f}")

    if pd.notna(ultima.get("atr_14")):
        col6.metric("ATR (14)", f"{última['atr_14']:.2f}")

    # Suporte e Resistencia
    st.divider()
    st.subheader("Suporte e Resistencia (últimos pregoes)")
    recente = df.tail(20)
    suporte = recente["low"].min()
    resistencia = recente["high"].max()
    col1, col2, col3 = st.columns(3)
    col1.metric("Suporte", f"R$ {suporte:.2f}", help="Mínima dos últimos 20 pregoes")
    col2.metric("Resistencia", f"R$ {resistencia:.2f}", help="Máxima dos últimos 20 pregoes")
    dist_suporte = ((ultima["close"] - suporte) / suporte) * 100
    col3.metric("Distancia do Suporte", f"{dist_suporte:.1f}%")

st.caption("Fonte: brapi.dev | Indicadores calculados com pandas")
