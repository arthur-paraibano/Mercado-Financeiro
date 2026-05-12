import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from dashboard.components.ticker_selector import ticker_multiselect  # noqa: E402

st.title("💸 Calendário de Dividendos")
st.caption("Histórico e projeção de dividendos para sua carteira.")

TICKERS_SUGERIDOS = [
    "TAEE11", "EGIE3", "CPFE3", "BBAS3", "ITUB4",
    "PETR4", "VALE3", "BBSE3", "KLBN11", "SANB11",
]

# --- Selecao de tickers ---
tickers = ticker_multiselect(
    "Selecione ações para analisar dividendos:",
    default=TICKERS_SUGERIDOS[:6],
    key="div_tickers",
)

if not tickers:
    st.info("Selecione pelo menos uma ação.")
    st.stop()

# --- Filtro de periodo ---
col1, col2 = st.columns(2)
with col1:
    meses_passados = st.slider("Histórico (meses atrás):", 1, 36, 12)
with col2:
    meses_futuros = st.slider("Futuro (meses a frente):", 0, 12, 3)

# --- Calculadora de carteira ---
with st.expander("Calculadora de Renda por Dividendos"):
    st.caption("Informe quantas cotas você possui de cada ação para calcular sua renda estimada.")
    qtd_cotas = {}
    cols_calc = st.columns(min(len(tickers), 4))
    for i, ticker in enumerate(tickers):
        with cols_calc[i % 4]:
            qtd_cotas[ticker] = st.number_input(
                f"{ticker}:", min_value=0, value=100, step=10, key=f"qtd_{ticker}"
            )

if st.button("Buscar Dividendos", type="primary"):
    brapi = BrapiCollector()
    todos_divs = []
    data_corte_passado = pd.Timestamp(date.today()) - pd.DateOffset(months=meses_passados)
    data_corte_futuro = pd.Timestamp(date.today()) + pd.DateOffset(months=meses_futuros)

    with st.spinner("Carregando histórico de dividendos..."):
        progress = st.progress(0)
        for i, ticker in enumerate(tickers):
            try:
                divs = brapi.get_dividendos(ticker)
                for d in divs:
                    # Campos da brapi: paymentDate, rate, approvedOn, lastDatePrior, assetIssued, label
                    payment_raw = d.get("paymentDate", "") or ""
                    ex_raw = d.get("lastDatePrior", "") or ""
                    rate = d.get("rate", 0) or 0

                    # Parsear datas (formato: "2024-03-15T00:00:00.000Z" ou timestamp)
                    try:
                        if isinstance(payment_raw, (int, float)) and payment_raw > 0:
                            payment_dt = pd.to_datetime(payment_raw, unit="ms")
                        else:
                            payment_dt = pd.to_datetime(payment_raw)
                    except Exception:
                        payment_dt = None

                    try:
                        if isinstance(ex_raw, (int, float)) and ex_raw > 0:
                            ex_dt = pd.to_datetime(ex_raw, unit="ms")
                        else:
                            ex_dt = pd.to_datetime(ex_raw)
                    except Exception:
                        ex_dt = None

                    if payment_dt is None:
                        continue

                    todos_divs.append({
                        "Ticker": ticker,
                        "Data Pagamento": payment_dt,
                        "Data Ex": ex_dt,
                        "Valor/Cota (R$)": rate,
                        "Tipo": d.get("label", "Dividendo"),
                        "Qtd Cotas": qtd_cotas.get(ticker, 0),
                        "Renda Estimada": rate * qtd_cotas.get(ticker, 0),
                    })
            except Exception as e:
                st.warning(f"{ticker}: {e}")
            progress.progress((i + 1) / len(tickers))
        progress.empty()

    if not todos_divs:
        st.error("Nenhum dado de dividendos encontrado.")
        st.stop()

    df = pd.DataFrame(todos_divs)
    df["Data Pagamento"] = pd.to_datetime(df["Data Pagamento"])

    # Filtrar pelo periodo
    df_periodo = df[
        (df["Data Pagamento"] >= data_corte_passado) &
        (df["Data Pagamento"] <= data_corte_futuro)
    ].copy()

    if df_periodo.empty:
        st.warning("Nenhum dividendo encontrado no período selecionado. Tente ampliar o intervalo.")
        df_periodo = df.copy()

    df_periodo = df_periodo.sort_values("Data Pagamento").reset_index(drop=True)

    # ========================================
    # Metricas
    # ========================================
    hoje = pd.Timestamp(date.today())
    df_proximos = df_periodo[df_periodo["Data Pagamento"] >= hoje]
    df_passados = df_periodo[df_periodo["Data Pagamento"] < hoje]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Pagamentos", len(df_periodo))
    col2.metric("Próximos Pagamentos", len(df_proximos))
    col3.metric(
        "Renda Estimada (próximos)",
        f"R$ {df_proximos['Renda Estimada'].sum():,.2f}" if not df_proximos.empty else "R$ 0,00"
    )
    col4.metric(
        "Renda Recebida (histórico)",
        f"R$ {df_passados['Renda Estimada'].sum():,.2f}" if not df_passados.empty else "R$ 0,00"
    )

    st.divider()

    # ========================================
    # Timeline de pagamentos
    # ========================================
    st.subheader("Timeline de Dividendos")

    cores_tickers = px.colors.qualitative.Set2
    mapa_cores = {t: cores_tickers[i % len(cores_tickers)] for i, t in enumerate(tickers)}

    fig = go.Figure()
    for ticker_t in tickers:
        df_t = df_periodo[df_periodo["Ticker"] == ticker_t]
        if df_t.empty:
            continue
        fig.add_trace(go.Scatter(
            x=df_t["Data Pagamento"],
            y=[ticker_t] * len(df_t),
            mode="markers+text",
            name=ticker_t,
            marker=dict(
                size=df_t["Valor/Cota (R$)"].apply(lambda v: max(10, min(40, v * 20))),
                color=mapa_cores.get(ticker_t, "#1f77b4"),
                symbol="circle",
                line=dict(width=1, color="white"),
            ),
            text=df_t["Valor/Cota (R$)"].apply(lambda v: f"R${v:.3f}"),
            textposition="top center",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Data: %{x|%d/%m/%Y}<br>"
                "Valor/Cota: R$ %{customdata[0]:.4f}<br>"
                "Tipo: %{customdata[1]}<br>"
                "<extra></extra>"
            ),
            customdata=df_t[["Valor/Cota (R$)", "Tipo"]].values,
        ))

    # Linha do hoje
    fig.add_vline(
        x=hoje, line_dash="dash", line_color="yellow",
        annotation_text="Hoje", annotation_position="top",
    )

    fig.update_layout(
        height=max(300, len(tickers) * 60 + 100),
        yaxis_title="",
        xaxis_title="Data de Pagamento",
        legend=dict(orientation="h", y=1.05),
        hovermode="closest",
    )
    st.plotly_chart(fig, width="stretch")

    st.divider()

    # ========================================
    # Dividendos por mes (barras)
    # ========================================
    st.subheader("Renda por Mês")

    df_periodo["Mês"] = df_periodo["Data Pagamento"].dt.to_period("M").astype(str)
    df_mes = (
        df_periodo.groupby(["Mês", "Ticker"])["Renda Estimada"]
        .sum()
        .reset_index()
    )

    if not df_mes.empty:
        fig2 = px.bar(
            df_mes,
            x="Mês",
            y="Renda Estimada",
            color="Ticker",
            barmode="stack",
            title="Renda Mensal Estimada por Ação (R$)",
            labels={"Renda Estimada": "Renda (R$)", "Mês": "Mês"},
            color_discrete_map=mapa_cores,
        )
        fig2.update_layout(height=350, xaxis_tickangle=-45)
        st.plotly_chart(fig2, width="stretch")

    st.divider()

    # ========================================
    # Tabela detalhada
    # ========================================
    st.subheader("Todos os Pagamentos")

    cols_show = ["Ticker", "Data Pagamento", "Data Ex", "Valor/Cota (R$)", "Tipo", "Qtd Cotas", "Renda Estimada"]
    df_show = df_periodo[cols_show].copy()

    # Destacar proximos
    def destacar_linha(row):
        if row["Data Pagamento"] >= hoje:
            return ["background-color: #1a3a1a"] * len(row)
        return [""] * len(row)

    styled = (
        df_show.style
        .apply(destacar_linha, axis=1)
        .format({
            "Data Pagamento": lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "—",
            "Data Ex": lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "—",
            "Valor/Cota (R$)": "R$ {:.4f}",
            "Renda Estimada": "R$ {:.2f}",
        }, na_rep="—")
    )

    st.dataframe(styled, width="stretch", hide_index=True, height=400)

st.caption("Fonte: brapi.dev | Dividendos históricos e projetados")
