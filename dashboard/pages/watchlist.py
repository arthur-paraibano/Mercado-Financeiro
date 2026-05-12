import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.collectors.b3_collector import SETORES_B3, get_setor_do_ticker  # noqa: E402
from dashboard.components.ticker_selector import ticker_selectbox, TICKERS_DISPONIVEIS  # noqa: E402

WATCHLIST_FILE = Path(__file__).parent.parent / "data" / "watchlist.json"


def carregar_watchlist() -> dict:
    if WATCHLIST_FILE.exists():
        try:
            return json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tickers": [], "alertas": {}}


def salvar_watchlist(data: dict):
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


st.title("⭐ Watchlist — Meus Favoritos")

wl = carregar_watchlist()

# ========================================
# Gerenciar lista
# ========================================
with st.expander("Gerenciar Watchlist", expanded=len(wl["tickers"]) == 0):
    col1, col2 = st.columns([3, 1])
    with col1:
        novo_ticker = ticker_selectbox("Adicionar ação:", default="PETR4", key="wl_add")
    with col2:
        st.write("")
        st.write("")
        if st.button("Adicionar ➕", width="stretch"):
            if novo_ticker and novo_ticker not in wl["tickers"]:
                wl["tickers"].append(novo_ticker)
                salvar_watchlist(wl)
                st.success(f"{novo_ticker} adicionado!")
                st.rerun()
            elif novo_ticker in wl["tickers"]:
                st.warning(f"{novo_ticker} já esta na watchlist.")

    if wl["tickers"]:
        st.markdown("**Remover ações:**")
        ticker_remover = st.selectbox(
            "Selecione para remover:",
            [""] + wl["tickers"],
            key="wl_remove",
        )
        if st.button("Remover ❌") and ticker_remover:
            wl["tickers"].remove(ticker_remover)
            wl["alertas"].pop(ticker_remover, None)
            salvar_watchlist(wl)
            st.success(f"{ticker_remover} removido.")
            st.rerun()

if not wl["tickers"]:
    st.info("Sua watchlist esta vazia. Adicione ações acima para começar.")
    st.stop()

# ========================================
# Alertas de preco
# ========================================
with st.expander("Configurar Alertas de Preço"):
    st.caption("Sera exibido um destaque quando o preço atingir ou ficar abaixo do valor-alvo.")
    for ticker in wl["tickers"]:
        alerta_atual = wl["alertas"].get(ticker, {}).get("preco_alvo", 0.0)
        novo_alerta = st.number_input(
            f"{ticker} — Preço-alvo (R$):",
            min_value=0.0,
            value=float(alerta_atual),
            step=0.50,
            format="%.2f",
            key=f"alerta_{ticker}",
        )
        if novo_alerta != alerta_atual:
            if novo_alerta > 0:
                wl["alertas"][ticker] = {"preco_alvo": novo_alerta}
            else:
                wl["alertas"].pop(ticker, None)
    if st.button("Salvar Alertas 💾"):
        salvar_watchlist(wl)
        st.success("Alertas salvos!")

# ========================================
# Analise de Diversificacao
# ========================================
st.subheader("🎯 Análise de Diversificação")

# Setores presentes
setores_cont = {}
sem_setor = []
for t in wl["tickers"]:
    s = get_setor_do_ticker(t)
    if s:
        setores_cont[s] = setores_cont.get(s, 0) + 1
    else:
        sem_setor.append(t)

n_acoes = len(wl["tickers"])
n_setores = len(setores_cont)

col1, col2, col3 = st.columns(3)
col1.metric("Ações na carteira", n_acoes, help="Recomendado: 5-15 ações")
col2.metric("Setores diferentes", n_setores, help="Recomendado: pelo menos 4-5 setores")
maior_setor_pct = (max(setores_cont.values()) / n_acoes * 100) if setores_cont else 0
col3.metric(
    "Concentração máxima",
    f"{maior_setor_pct:.0f}%",
    help="Quanto % esta no setor mais representado. < 30% e ideal.",
)

# Avisos
avisos = []
if n_acoes < 5:
    avisos.append(("⚠️", f"**Pouca diversificação:** você so tem {n_acoes} ação(oes). Idealmente, tenha pelo menos 5-8."))
elif n_acoes > 20:
    avisos.append(("ℹ️", f"**Muitas ações ({n_acoes}):** acima de 20 e dificil acompanhar. Considere consolidar."))

if n_setores < 3 and n_acoes >= 3:
    avisos.append(("🚨", f"**Concentração setorial:** seus papeis estão em apenas {n_setores} setor(es). Diversifique entre Bancos, Energia, Saúde, Consumo, etc."))

if maior_setor_pct > 50 and n_acoes >= 4:
    setor_concentrado = max(setores_cont, key=setores_cont.get)
    avisos.append(("🚨", f"**Risco setorial:** {maior_setor_pct:.0f}% das suas ações são do setor **{setor_concentrado}**. Se esse setor cair, você sofre muito."))

if sem_setor:
    avisos.append(("ℹ️", f"Sem setor mapeado: {', '.join(sem_setor)}"))

if not avisos:
    st.success(f"✅ **Boa diversificação!** {n_acoes} ações em {n_setores} setores, maior concentração de {maior_setor_pct:.0f}%.")
else:
    for icone, msg in avisos:
        if icone == "🚨":
            st.error(f"{icone} {msg}")
        elif icone == "⚠️":
            st.warning(f"{icone} {msg}")
        else:
            st.info(f"{icone} {msg}")

# Pizza setorial
if setores_cont:
    import plotly.express as px
    df_setor = pd.DataFrame(
        [{"Setor": s, "Ações": c} for s, c in setores_cont.items()]
    )
    fig_pie = px.pie(
        df_setor, values="Ações", names="Setor",
        title="Distribuição por Setor",
        hole=0.4,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(height=350)
    st.plotly_chart(fig_pie, width="stretch")

st.divider()

# ========================================
# Cotacoes ao vivo
# ========================================
st.subheader(f"Cotações — {len(wl['tickers'])} ações")

if st.button("🔄 Atualizar Cotações", type="primary"):
    st.rerun()

brapi = BrapiCollector()
rows = []

with st.spinner("Carregando cotações..."):
    cotacoes = brapi.get_cotacao_lote(wl["tickers"])

for ticker in wl["tickers"]:
    dados = cotacoes.get(ticker)
    preco_alvo = wl["alertas"].get(ticker, {}).get("preco_alvo", 0)
    if dados:
        preco = dados.get("regularMarketPrice", 0) or 0
        variacao = dados.get("regularMarketChangePercent", 0) or 0
        variacao_abs = dados.get("regularMarketChange", 0) or 0
        minima = dados.get("regularMarketDayLow", 0) or 0
        maxima = dados.get("regularMarketDayHigh", 0) or 0
        volume = dados.get("regularMarketVolume", 0) or 0
        nome = dados.get("shortName", ticker)
        alerta_ativo = preco_alvo > 0 and preco <= preco_alvo
        rows.append({
            "Ticker": ticker,
            "Empresa": (TICKERS_DISPONIVEIS.get(ticker, nome) or nome)[:30],
            "Preço": preco,
            "Variação": variacao,
            "Variação R$": variacao_abs,
            "Mínima": minima,
            "Máxima": maxima,
            "Volume": volume,
            "Alvo": preco_alvo if preco_alvo > 0 else None,
            "Alerta": "🔔 ALVO!" if alerta_ativo else "",
        })
    else:
        rows.append({
            "Ticker": ticker,
            "Empresa": TICKERS_DISPONIVEIS.get(ticker, ticker),
            "Preço": None,
            "Variação": None,
            "Variação R$": None,
            "Mínima": None,
            "Máxima": None,
            "Volume": None,
            "Alvo": preco_alvo if preco_alvo > 0 else None,
            "Alerta": "⚠️ sem dados",
        })

if not rows:
    st.warning("Nenhuma cotação carregada.")
    st.stop()

df = pd.DataFrame(rows)

# Alertas disparados
alertas_ativos = df[df["Alerta"] == "🔔 ALVO!"]
if not alertas_ativos.empty:
    for _, row in alertas_ativos.iterrows():
        st.warning(
            f"🔔 **{row['Ticker']}** atingiu o preço-alvo! "
            f"Cotação: R$ {row['Preço']:.2f} | Alvo: R$ {row['Alvo']:.2f}"
        )

# Metricas rapidas
cols_met = st.columns(min(len(df), 4))
for i, (_, row) in enumerate(df.head(4).iterrows()):
    if row["Preço"] is not None:
        delta = f"{row['Variação']:+.2f}%" if row["Variação"] is not None else None
        cols_met[i].metric(row["Ticker"], f"R$ {row['Preço']:.2f}", delta)

st.divider()

# Tabela completa
def cor_variacao(val):
    if val is None:
        return ""
    if val > 2:
        return "background-color: #1a5c1a; color: white"
    elif val > 0:
        return "background-color: #2d6a2e; color: white"
    elif val < -2:
        return "background-color: #8c1a1a; color: white"
    elif val < 0:
        return "background-color: #7a2020; color: white"
    return ""

cols_show = ["Alerta", "Ticker", "Empresa", "Preço", "Variação", "Variação R$", "Mínima", "Máxima", "Volume", "Alvo"]
styled = (
    df[cols_show]
    .style
    .map(cor_variacao, subset=["Variação"])
    .format({
        "Preço": "R$ {:.2f}",
        "Variação": "{:+.2f}%",
        "Variação R$": "R$ {:+.2f}",
        "Mínima": "R$ {:.2f}",
        "Máxima": "R$ {:.2f}",
        "Volume": "{:,.0f}",
        "Alvo": lambda x: f"R$ {x:.2f}" if x is not None else "—",
    }, na_rep="—")
)

st.dataframe(styled, width="stretch", hide_index=True)

st.caption("Fonte: brapi.dev | Dados atualizados ao clicar em Atualizar Cotações")
