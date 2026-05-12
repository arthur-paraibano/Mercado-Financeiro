import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.collectors.bcb_collector import BCBCollector  # noqa: E402
from dashboard.components.ticker_selector import ticker_selectbox  # noqa: E402

st.title("⚖️ Ações vs Renda Fixa")
st.caption("Simule R$ 10.000 investidos e compare o desempenho de uma ação com benchmarks de renda fixa.")

# --- Configuracao ---
col1, col2, col3 = st.columns(3)
with col1:
    ticker = ticker_selectbox("Ação para comparar:", default="PETR4", key="rf_ticker")
with col2:
    periodo_opcoes = {
        "6 meses": ("6mo", 180),
        "1 ano": ("1y", 365),
        "2 anos": ("2y", 730),
        "5 anos": ("5y", 1825),
    }
    periodo_sel = st.selectbox("Período:", list(periodo_opcoes.keys()), index=1)
with col3:
    valor_inicial = st.number_input("Valor inicial (R$):", min_value=100.0, value=10000.0, step=1000.0)

periodo_brapi, dias = periodo_opcoes[periodo_sel]

# Benchmarks a exibir
st.sidebar.header("Benchmarks")
exibir_cdi = st.sidebar.checkbox("CDI", value=True)
exibir_ipca = st.sidebar.checkbox("IPCA+", value=True)
exibir_ibov = st.sidebar.checkbox("Ibovespa", value=True)
exibir_poup = st.sidebar.checkbox("Poupanca", value=True)

CORES = {
    "Ação": "#1f77b4",
    "CDI": "#ff7f0e",
    "IPCA+": "#2ca02c",
    "Ibovespa": "#9467bd",
    "Poupanca": "#8c564b",
}


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_bcb_cdi(inicio: str) -> pd.DataFrame:
    bcb = BCBCollector()
    return bcb.get_cdi(inicio)


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_bcb_ipca(inicio: str) -> pd.DataFrame:
    bcb = BCBCollector()
    return bcb.get_ipca(inicio)


def acumular_serie(df: pd.DataFrame, valor_base: float) -> pd.Series:
    """Acumula taxa percentual diaria em valor monetario."""
    fatores = 1 + df["valor"] / 100
    acumulado = fatores.cumprod()
    return acumulado * valor_base / acumulado.iloc[0]


def retorno_anualizado(retorno_total: float, dias: int) -> float:
    if dias <= 0:
        return 0.0
    return ((1 + retorno_total / 100) ** (365 / dias) - 1) * 100


if st.button("Comparar", type="primary"):
    brapi = BrapiCollector()
    data_inicio = (date.today() - timedelta(days=dias)).strftime("%d/%m/%Y")
    data_inicio_brapi = (date.today() - timedelta(days=dias)).strftime("%Y-%m-%d")

    resultados = {}
    erros = []

    with st.spinner("Carregando dados..."):

        # --- Acao ---
        try:
            hist = brapi.get_historico(ticker, periodo_brapi, "1d")
            if hist and len(hist) > 5:
                df_acao = pd.DataFrame(hist)
                df_acao["date"] = pd.to_datetime(df_acao["date"], unit="s")
                df_acao = df_acao.sort_values("date").reset_index(drop=True)
                base = df_acao["close"].iloc[0]
                df_acao["valor_acum"] = (df_acao["close"] / base) * valor_inicial
                resultados["Ação"] = df_acao[["date", "valor_acum"]].rename(columns={"date": "data"})
            else:
                erros.append(f"Ação {ticker}: histórico insuficiente")
        except Exception as e:
            erros.append(f"Ação {ticker}: {e}")

        # --- Ibovespa ---
        if exibir_ibov:
            try:
                hist_ibov = brapi.get_historico("^BVSP", periodo_brapi, "1d")
                if not hist_ibov:
                    hist_ibov = brapi.get_historico("BOVA11", periodo_brapi, "1d")
                if hist_ibov and len(hist_ibov) > 5:
                    df_ibov = pd.DataFrame(hist_ibov)
                    df_ibov["date"] = pd.to_datetime(df_ibov["date"], unit="s")
                    df_ibov = df_ibov.sort_values("date").reset_index(drop=True)
                    base_ibov = df_ibov["close"].iloc[0]
                    df_ibov["valor_acum"] = (df_ibov["close"] / base_ibov) * valor_inicial
                    resultados["Ibovespa"] = df_ibov[["date", "valor_acum"]].rename(columns={"date": "data"})
            except Exception as e:
                erros.append(f"Ibovespa: {e}")

        # --- CDI ---
        if exibir_cdi:
            try:
                df_cdi = buscar_bcb_cdi(data_inicio)
                if not df_cdi.empty:
                    df_cdi = df_cdi.rename(columns={"data": "data"})
                    df_cdi = df_cdi.sort_values("data").reset_index(drop=True)
                    df_cdi["valor_acum"] = acumular_serie(df_cdi, valor_inicial)
                    resultados["CDI"] = df_cdi[["data", "valor_acum"]]
            except Exception as e:
                erros.append(f"CDI: {e}")

        # --- IPCA ---
        if exibir_ipca:
            try:
                df_ipca = buscar_bcb_ipca(data_inicio)
                if not df_ipca.empty:
                    df_ipca = df_ipca.sort_values("data").reset_index(drop=True)
                    # IPCA e mensal: converter para diario por interpolacao
                    df_ipca_daily = df_ipca.set_index("data").resample("D").interpolate(method="linear").reset_index()
                    # Converter taxa mensal (%) em taxa diaria equivalente: (1+m/100)^(1/30)-1, em %
                    df_ipca_daily["valor"] = ((1 + df_ipca_daily["valor"] / 100) ** (1 / 30) - 1) * 100
                    df_ipca_daily["valor_acum"] = acumular_serie(df_ipca_daily, valor_inicial)
                    resultados["IPCA+"] = df_ipca_daily[["data", "valor_acum"]]
            except Exception as e:
                erros.append(f"IPCA: {e}")

        # --- Poupanca (0.5%/mes ou 70% Selic/12 se Selic < 8.5%) ---
        if exibir_poup:
            try:
                # Usar taxa fixa de poupanca (Selic atual ~10.5%, portanto 0.5%/mes + TR)
                taxa_poup_mensal = 0.005  # 0.5% ao mes
                taxa_poup_diaria = (1 + taxa_poup_mensal) ** (1 / 30) - 1
                n_dias = dias
                datas = pd.date_range(
                    end=date.today(),
                    periods=n_dias,
                    freq="D",
                )
                valores_poup = [valor_inicial * (1 + taxa_poup_diaria) ** i for i in range(n_dias)]
                resultados["Poupanca"] = pd.DataFrame({"data": datas, "valor_acum": valores_poup})
            except Exception as e:
                erros.append(f"Poupanca: {e}")

    for erro in erros:
        st.warning(erro)

    if not resultados:
        st.error("Nenhum dado carregado. Verifique sua conexao.")
        st.stop()

    # ========================================
    # Grafico principal
    # ========================================
    st.subheader(f"Simulação: R$ {valor_inicial:,.2f} investidos")

    fig = go.Figure()
    for nome, df_r in resultados.items():
        cor = CORES.get(nome, "#7f7f7f")
        largura = 3 if nome == "Ação" else 2
        dash = "solid" if nome == "Ação" else "dash" if nome in ("CDI", "IPCA+") else "dot"
        fig.add_trace(go.Scatter(
            x=df_r["data"],
            y=df_r["valor_acum"],
            name=nome if nome != "Ação" else ticker,
            line=dict(color=cor, width=largura, dash=dash),
        ))

    fig.add_hline(y=valor_inicial, line_dash="dash", line_color="gray", opacity=0.4)
    fig.update_layout(
        height=450,
        yaxis_title=f"Valor acumulado (R$)",
        yaxis_tickprefix="R$ ",
        yaxis_tickformat=",.0f",
        legend=dict(orientation="h", y=1.05),
        hovermode="x unified",
    )
    st.plotly_chart(fig, width="stretch")

    # ========================================
    # Tabela resumo
    # ========================================
    st.subheader("Resumo de Performance")

    resumo = []
    for nome, df_r in resultados.items():
        valor_final = df_r["valor_acum"].iloc[-1]
        retorno_total = ((valor_final / valor_inicial) - 1) * 100
        n_dias_real = (df_r["data"].iloc[-1] - df_r["data"].iloc[0]).days or 1
        ret_anual = retorno_anualizado(retorno_total, n_dias_real)

        # Volatilidade (apenas para acao e ibovespa — series diarias)
        vol = None
        if nome in ("Ação", "Ibovespa"):
            retornos_diarios = df_r["valor_acum"].pct_change().dropna()
            if len(retornos_diarios) > 5:
                vol = retornos_diarios.std() * np.sqrt(252) * 100

        resumo.append({
            "Benchmark": ticker if nome == "Ação" else nome,
            "Valor Final": valor_final,
            "Retorno Total": retorno_total,
            "Retorno Anualizado": ret_anual,
            "Volatilidade (anual)": vol,
        })

    df_resumo = pd.DataFrame(resumo).sort_values("Retorno Total", ascending=False).reset_index(drop=True)

    # Destacar melhor
    melhor = df_resumo.iloc[0]["Benchmark"]
    st.success(f"Melhor desempenho no período: **{melhor}** com retorno de **{df_resumo.iloc[0]['Retorno Total']:+.2f}%**")

    def cor_retorno(val):
        if isinstance(val, float):
            if val > 10:
                return "color: #2ca02c; font-weight: bold"
            elif val > 0:
                return "color: #1f77b4"
            else:
                return "color: #d62728"
        return ""

    styled = (
        df_resumo.style
        .map(cor_retorno, subset=["Retorno Total", "Retorno Anualizado"])
        .format({
            "Valor Final": "R$ {:,.2f}",
            "Retorno Total": "{:+.2f}%",
            "Retorno Anualizado": "{:+.2f}%",
            "Volatilidade (anual)": lambda x: f"{x:.1f}%" if x is not None else "N/A",
        }, na_rep="N/A")
    )
    st.dataframe(styled, width="stretch", hide_index=True)

st.caption("Fontes: brapi.dev (cotações) | Banco Central do Brasil (CDI, IPCA) | Cálculo próprio (Poupanca)")
