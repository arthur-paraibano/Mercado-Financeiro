import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.processors.technical_calculator import TechnicalCalculator  # noqa: E402
from dashboard.components.ticker_selector import ticker_multiselect  # noqa: E402

st.title("📡 Scanner de Sinais Técnicos")

TICKERS_DEFAULT = [
    "PETR4", "VALE3", "ITUB4", "BBAS3", "WEGE3",
    "EGIE3", "TAEE11", "BBDC4", "SUZB3", "ABEV3",
    "PRIO3", "JBSS3", "RDOR3", "RENT3", "VIVT3",
    "KLBN11", "CPFE3", "SANB11", "ITSA4", "EQTL3",
    "TOTS3", "SLCE3", "FLRY3", "ENGI11", "CCRO3",
]

# --- Configuracao ---
usar_padrao = st.sidebar.checkbox("Usar lista padrao (25 ações)", value=True)
if usar_padrao:
    tickers = TICKERS_DEFAULT
else:
    tickers = ticker_multiselect(
        "Selecione ações:",
        default=TICKERS_DEFAULT[:10],
        key="sinais_custom",
        sidebar=True,
    )

filtro_sinal = st.sidebar.multiselect(
    "Filtrar por sinal:",
    ["COMPRA", "VENDA", "NEUTRO", "ATENCAO"],
    default=["COMPRA", "VENDA"],
)

ICONES = {"COMPRA": "🟢", "VENDA": "🔴", "NEUTRO": "⚪", "ATENCAO": "⚠️"}

if st.button("Escanear Sinais", type="primary"):
    brapi = BrapiCollector()
    resultados = []

    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"Escaneando {ticker} ({i + 1}/{len(tickers)})...")
        try:
            historico = brapi.get_historico(ticker, "3mo", "1d")
            if not historico or len(historico) < 30:
                continue

            df = pd.DataFrame(historico)
            df["date"] = pd.to_datetime(df["date"], unit="s")
            df = TechnicalCalculator.calcular_todos(df)
            sinais = TechnicalCalculator.gerar_sinais(df)

            if not sinais:
                continue

            ultima = df.iloc[-1]
            row = {
                "Ticker": ticker,
                "Preço": ultima["close"],
                "Variação %": ((ultima["close"] / df.iloc[-2]["close"]) - 1) * 100 if len(df) > 1 else 0,
            }

            # Contar sinais
            compras = 0
            vendas = 0
            for nome, info in sinais.items():
                sinal = info.get("sinal", "NEUTRO")
                row[nome] = f"{ICONES.get(sinal, '')} {sinal}"
                row[f"{nome}_raw"] = sinal
                if sinal == "COMPRA":
                    compras += 1
                elif sinal == "VENDA":
                    vendas += 1

            # Sinal geral
            if compras >= 3:
                row["Sinal Geral"] = "🟢 COMPRA FORTE"
                row["sinal_geral_raw"] = "COMPRA"
            elif compras > vendas:
                row["Sinal Geral"] = "🟢 COMPRA"
                row["sinal_geral_raw"] = "COMPRA"
            elif vendas >= 3:
                row["Sinal Geral"] = "🔴 VENDA FORTE"
                row["sinal_geral_raw"] = "VENDA"
            elif vendas > compras:
                row["Sinal Geral"] = "🔴 VENDA"
                row["sinal_geral_raw"] = "VENDA"
            else:
                row["Sinal Geral"] = "⚪ NEUTRO"
                row["sinal_geral_raw"] = "NEUTRO"

            row["Compras"] = compras
            row["Vendas"] = vendas

            resultados.append(row)
            time.sleep(0.3)
        except Exception:
            pass
        progress.progress((i + 1) / len(tickers))

    progress.empty()
    status.empty()

    if not resultados:
        st.warning("Nenhum resultado. Verifique os tickers.")
        st.stop()

    df_res = pd.DataFrame(resultados)

    # Filtrar
    if filtro_sinal:
        df_res = df_res[df_res["sinal_geral_raw"].isin(filtro_sinal)]

    if df_res.empty:
        st.info("Nenhuma ação passou no filtro de sinais.")
        st.stop()

    # Ordenar por sinal
    ordem = {"COMPRA": 0, "VENDA": 1, "NEUTRO": 2, "ATENCAO": 3}
    df_res = df_res.sort_values(
        by=["sinal_geral_raw", "Compras"],
        key=lambda x: x.map(ordem) if x.name == "sinal_geral_raw" else -x,
        ascending=[True, True],
    ).reset_index(drop=True)

    # --- Resumo ---
    st.subheader("Resumo")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Escaneadas", len(df_res))
    col2.metric("🟢 Compra", len(df_res[df_res["sinal_geral_raw"] == "COMPRA"]))
    col3.metric("🔴 Venda", len(df_res[df_res["sinal_geral_raw"] == "VENDA"]))
    col4.metric("⚪ Neutro", len(df_res[df_res["sinal_geral_raw"] == "NEUTRO"]))

    st.divider()

    # --- Tabela ---
    st.subheader("Sinais por Ação")
    cols_show = ["Sinal Geral", "Ticker", "Preço", "Variação %"]
    for col in ["RSI", "MACD", "MEDIAS", "BOLLINGER", "VOLUME"]:
        if col in df_res.columns:
            cols_show.append(col)

    st.dataframe(
        df_res[cols_show].style.format({
            "Preço": "R$ {:.2f}",
            "Variação %": "{:+.2f}%",
        }),
        width="stretch",
        hide_index=True,
        height=500,
    )

    st.divider()

    # --- Grafico de distribuicao ---
    st.subheader("Distribuição de Sinais")
    sinal_count = df_res["sinal_geral_raw"].value_counts().reset_index()
    sinal_count.columns = ["Sinal", "Quantidade"]
    fig = px.pie(
        sinal_count, names="Sinal", values="Quantidade",
        color="Sinal",
        color_discrete_map={"COMPRA": "#2ca02c", "VENDA": "#d62728", "NEUTRO": "#7f7f7f", "ATENCAO": "#ff7f0e"},
        title="Distribuição de Sinais no Mercado",
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, width="stretch")

st.caption("Fonte: brapi.dev | Indicadores: RSI-14, MACD(12,26,9), SMA 20/50/200, Bollinger(20,2)")
