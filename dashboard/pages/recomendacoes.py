import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.b3_collector import SETORES_B3  # noqa: E402
from src.processors.recommendation_engine import RecommendationEngine  # noqa: E402
from dashboard.components.ticker_selector import ticker_multiselect  # noqa: E402
from dashboard.components.glossario import avaliar_iniciante, tip  # noqa: E402

st.title("Recomendações de Compra")

st.warning(
    "**Aviso:** Este sistema é uma ferramenta de análise. "
    "**NÃO** constitui recomendação de investimento profissional. "
    "Sempre faça sua própria análise antes de investir."
)

ICONES_SINAL = {
    "COMPRA FORTE": "🟢",
    "COMPRA": "🔵",
    "NEUTRO": "⚪",
    "CAUTELA": "🟡",
    "EVITAR": "🔴",
}

# Toggle modo iniciante
modo_iniciante = st.sidebar.toggle(
    "👶 Modo Iniciante",
    value=False,
    help="Filtra apenas ações amigáveis para quem está começando: dividendos consistentes, empresa rentável, preço justo.",
)

# --- Seleção ---
st.sidebar.header("Configuração")
modo = st.sidebar.radio("Modo:", ["Lista curada (top ações)", "Por setor", "Personalizado"])

if modo == "Lista curada (top ações)":
    tickers = [
        "WEGE3", "ITUB4", "BBAS3", "VALE3", "PETR4",
        "EGIE3", "TAEE11", "CPFE3", "SUZB3", "KLBN11",
        "RDOR3", "FLRY3", "TOTS3", "SLCE3", "JBSS3",
        "BBDC4", "PRIO3", "VIVT3", "ABEV3", "BBSE3",
        "ITSA4", "EQTL3", "SANB11", "ENGI11", "RENT3",
    ]
elif modo == "Por setor":
    setor = st.sidebar.selectbox("Setor:", list(SETORES_B3.keys()))
    tickers = SETORES_B3[setor]
else:
    tickers = ticker_multiselect(
        "Selecione ações:",
        default=["WEGE3", "ITUB4", "VALE3", "PETR4", "BBAS3", "EGIE3", "TAEE11"],
        key="rec_custom",
        sidebar=True,
    )

# Filtros
st.sidebar.header("Filtros")
sinais_filtro = st.sidebar.multiselect(
    "Mostrar apenas:",
    ["COMPRA FORTE", "COMPRA", "NEUTRO", "CAUTELA", "EVITAR"],
    default=["COMPRA FORTE", "COMPRA", "NEUTRO"],
)

upside_min = st.sidebar.slider("Upside mínimo (%)", -50, 100, -10, 5)


# ========================================
# Geração / Cache em session_state
# ========================================
if st.button("Gerar Recomendações", type="primary"):
    engine = RecommendationEngine()
    recs_raw = []

    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"Analisando {ticker} ({i + 1}/{len(tickers)})...")
        rec = engine.analisar_ticker(ticker)
        if rec:
            recs_raw.append(rec)
        progress.progress((i + 1) / len(tickers))

    progress.empty()
    status.empty()

    st.session_state["rec_recs_raw"] = recs_raw
    st.session_state["rec_data"] = date.today().strftime("%d/%m/%Y")

# Limpar resultados manualmente (botão opcional)
if "rec_recs_raw" in st.session_state:
    if st.sidebar.button("🗑️ Limpar resultados"):
        del st.session_state["rec_recs_raw"]
        st.rerun()

# ========================================
# Renderização (a partir de session_state)
# ========================================
recs_raw = st.session_state.get("rec_recs_raw")

if not recs_raw:
    st.info("👈 Configure as opções na barra lateral e clique em **Gerar Recomendações** para começar.")
    st.stop()

# Aplicar filtros (reagem dinamicamente sem precisar gerar de novo)
recs = [
    r for r in recs_raw
    if r.sinal in sinais_filtro and r.upside_pct >= upside_min
]

# Ordenar
ordem = {"COMPRA FORTE": 0, "COMPRA": 1, "NEUTRO": 2, "CAUTELA": 3, "EVITAR": 4}
recs.sort(key=lambda r: (ordem.get(r.sinal, 9), -r.score_geral))

if not recs:
    st.info("Nenhuma ação passou nos filtros. Tente ajustar os critérios na barra lateral.")
    st.stop()

# ========================================
# RESUMO GERAL
# ========================================
st.subheader(f"Resultado: {len(recs)} ações analisadas")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🟢 Compra Forte", sum(1 for r in recs if r.sinal == "COMPRA FORTE"))
col2.metric("🔵 Compra", sum(1 for r in recs if r.sinal == "COMPRA"))
col3.metric("⚪ Neutro", sum(1 for r in recs if r.sinal == "NEUTRO"))
col4.metric("🟡 Cautela", sum(1 for r in recs if r.sinal == "CAUTELA"))
col5.metric("🔴 Evitar", sum(1 for r in recs if r.sinal == "EVITAR"))

st.divider()

# ========================================
# TABELA PRINCIPAL
# ========================================
st.subheader("Mapa de Recomendações")
st.caption(f"Data: {st.session_state.get('rec_data', '—')} | Atualização: semanal/mensal sugerida")

rows = []
motivos_iniciante = {}
for r in recs:
    eh_amigavel, motivos = avaliar_iniciante(r.indicadores, r.scores)
    motivos_iniciante[r.ticker] = motivos
    rows.append({
        "Iniciante": "🌱" if eh_amigavel else "",
        "amigavel_iniciante": eh_amigavel,
        "Sinal": f"{ICONES_SINAL.get(r.sinal, '')} {r.sinal}",
        "sinal_raw": r.sinal,
        "Ticker": r.ticker,
        "Empresa": r.empresa,
        "Cotação": r.cotacao,
        "Preço Justo": r.preco_justo,
        "Preço Teto": r.preco_teto,
        "Upside %": r.upside_pct,
        "Score": r.score_geral,
        "Saúde": r.scores.get("saude", 0),
        "Valuation": r.scores.get("valuation", 0),
        "DY %": r.indicadores.get("dividend_yield", 0),
        "ROE %": r.indicadores.get("roe", 0),
        "P/L": r.indicadores.get("pl", 0),
    })

df = pd.DataFrame(rows)

# Filtro modo iniciante
if modo_iniciante:
    df = df[df["amigavel_iniciante"]].reset_index(drop=True)
    if df.empty:
        st.info("Nenhuma ação da seleção atual passou no filtro de 'amigável para iniciantes'. Tente ampliar a lista de tickers ou desative o Modo Iniciante.")
        st.stop()
    st.info(f"🌱 **Modo Iniciante ativo:** mostrando apenas {len(df)} ações que pagam dividendos, são rentáveis e têm preço razoável.")

# Estilo condicional
def cor_sinal(val):
    if "COMPRA FORTE" in str(val):
        return "background-color: #1a5c1a; color: white"
    elif "COMPRA" in str(val):
        return "background-color: #1a4d8c; color: white"
    elif "NEUTRO" in str(val):
        return "background-color: #555; color: white"
    elif "CAUTELA" in str(val):
        return "background-color: #8c7a1a; color: white"
    elif "EVITAR" in str(val):
        return "background-color: #8c1a1a; color: white"
    return ""


def cor_upside(val):
    if val > 20:
        return "color: #2ca02c; font-weight: bold"
    elif val > 0:
        return "color: #1f77b4"
    elif val > -10:
        return "color: #ff7f0e"
    else:
        return "color: #d62728; font-weight: bold"


cols_show = [
    "Iniciante", "Sinal", "Ticker", "Empresa", "Cotação", "Preço Justo",
    "Preço Teto", "Upside %", "Score", "DY %", "ROE %", "P/L",
]

styled = (
    df[cols_show]
    .style
    .map(cor_sinal, subset=["Sinal"])
    .map(cor_upside, subset=["Upside %"])
    .format({
        "Cotação": "R$ {:.2f}",
        "Preço Justo": "R$ {:.2f}",
        "Preço Teto": "R$ {:.2f}",
        "Upside %": "{:+.1f}%",
        "Score": "{:.0f}",
        "DY %": "{:.1f}%",
        "ROE %": "{:.1f}%",
        "P/L": "{:.1f}",
    }, na_rep="N/A")
)

st.dataframe(styled, width="stretch", height=450, hide_index=True)

st.divider()

# ========================================
# GRÁFICO SCATTER: UPSIDE vs SCORE
# ========================================
st.subheader("Mapa: Score vs Upside")

fig = px.scatter(
    df,
    x="Score", y="Upside %",
    size="DY %", color="sinal_raw",
    hover_name="Ticker",
    hover_data=["Cotação", "Preço Justo", "Preço Teto", "ROE %"],
    color_discrete_map={
        "COMPRA FORTE": "#2ca02c",
        "COMPRA": "#1f77b4",
        "NEUTRO": "#7f7f7f",
        "CAUTELA": "#ff7f0e",
        "EVITAR": "#d62728",
    },
    title="Score Geral vs Potencial de Valorização (tamanho = DY)",
    labels={"sinal_raw": "Sinal", "Score": "Score (0-100)", "Upside %": "Upside (%)"},
)
fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
fig.add_annotation(x=75, y=30, text="Zona Ideal", showarrow=False, font=dict(size=14, color="green"))
fig.update_layout(height=500)
st.plotly_chart(fig, width="stretch")

st.divider()

# ========================================
# DETALHES POR AÇÃO
# ========================================
st.subheader("Detalhes por Ação")

ticker_sel = st.selectbox(
    "Selecione:",
    [r.ticker for r in recs],
    key="rec_ticker_sel",
)
rec_sel = next((r for r in recs if r.ticker == ticker_sel), None)

if rec_sel:
    icone = ICONES_SINAL.get(rec_sel.sinal, "")
    eh_amigavel_sel, motivos_sel = avaliar_iniciante(rec_sel.indicadores, rec_sel.scores)
    selo_iniciante = " 🌱 *Amigável para iniciantes*" if eh_amigavel_sel else ""
    st.markdown(f"### {icone} {rec_sel.ticker} - {rec_sel.empresa}{selo_iniciante}")
    st.markdown(f"**Setor:** {rec_sel.setor}")

    if eh_amigavel_sel:
        with st.expander("🌱 Por que esta ação é amigável para iniciantes?", expanded=False):
            for m in motivos_sel:
                st.markdown(f"- {m}")

    # Preços
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cotação Atual", f"R$ {rec_sel.cotação:.2f}")
    col2.metric("Preço Justo", f"R$ {rec_sel.preco_justo:.2f}", help=tip("PRECO_JUSTO"))
    col3.metric(
        "Preço Teto (c/ margem)",
        f"R$ {rec_sel.preco_teto:.2f}",
        f"{'Abaixo do teto' if rec_sel.cotação <= rec_sel.preco_teto else 'Acima do teto'}",
        help=tip("PRECO_TETO"),
    )
    col4.metric("Upside", f"{rec_sel.upside_pct:+.1f}%", help=tip("UPSIDE"))

    st.divider()

    st.markdown("**Faixa de Preço:**")
    min_p = min(rec_sel.cotacao, rec_sel.preco_teto) * 0.7
    max_p = max(rec_sel.cotacao, rec_sel.preco_justo) * 1.2

    fig_preco = go.Figure()
    fig_preco.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=rec_sel.cotacao,
        delta={"reference": rec_sel.preco_justo, "relative": True, "valueformat": ".1%"},
        title={"text": f"{rec_sel.ticker} - Cotação vs Preço Justo"},
        gauge={
            "axis": {"range": [min_p, max_p]},
            "bar": {"color": "#1f77b4"},
            "steps": [
                {"range": [min_p, rec_sel.preco_teto], "color": "#2ca02c"},
                {"range": [rec_sel.preco_teto, rec_sel.preco_justo], "color": "#ffdd57"},
                {"range": [rec_sel.preco_justo, max_p], "color": "#ff6b6b"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 3},
                "thickness": 0.8,
                "value": rec_sel.preco_justo,
            },
        },
    ))
    fig_preco.update_layout(height=300)
    st.plotly_chart(fig_preco, width="stretch")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Scores por Dimensão:**")
        categorias = ["Saúde", "Valuation", "Dividendos", "Crescimento", "Técnico"]
        valores = [
            rec_sel.scores.get("saude", 0),
            rec_sel.scores.get("valuation", 0),
            rec_sel.scores.get("dividendos", 0),
            rec_sel.scores.get("crescimento", 0),
            rec_sel.scores.get("tecnico", 0),
        ]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=valores + [valores[0]],
            theta=categorias + [categorias[0]],
            fill="toself",
            name=rec_sel.ticker,
            line_color="#1f77b4",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=350,
        )
        st.plotly_chart(fig_radar, width="stretch")

    with col2:
        st.markdown("**Motivos para Compra:**")
        if rec_sel.motivos:
            for m in rec_sel.motivos:
                st.markdown(f"- ✅ {m}")
        else:
            st.markdown("- Nenhum motivo forte identificado")

        st.markdown("**Riscos Identificados:**")
        if rec_sel.riscos:
            for r in rec_sel.riscos:
                st.markdown(f"- ⚠️ {r}")
        else:
            st.markdown("- Nenhum risco relevante identificado")

    if rec_sel.sinais_tecnicos:
        st.divider()
        st.markdown("**Sinais Técnicos:**")
        cols_tec = st.columns(len(rec_sel.sinais_tecnicos))
        for i, (nome, info) in enumerate(rec_sel.sinais_tecnicos.items()):
            sinal = info.get("sinal", "NEUTRO")
            cor = "🟢" if sinal == "COMPRA" else "🔴" if sinal == "VENDA" else "⚪"
            cols_tec[i].metric(
                f"{cor} {nome}",
                info.get("desc", "")[:30],
            )

    st.divider()
    st.markdown("**Indicadores-Chave:** *(passe o mouse sobre cada um para entender)*")
    ind = rec_sel.indicadores
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("P/L", f"{ind.get('pl', 0):.1f}", help=tip("PL"))
    col2.metric("P/VP", f"{ind.get('pvp', 0):.1f}", help=tip("PVP"))
    col3.metric("ROE", f"{ind.get('roe', 0):.1f}%", help=tip("ROE"))
    col4.metric("ROIC", f"{ind.get('roic', 0):.1f}%", help=tip("ROIC"))
    col5.metric("DY", f"{ind.get('dividend_yield', 0):.1f}%", help=tip("DY"))
    col6.metric("Margem Líq.", f"{ind.get('margem_liquida', 0):.1f}%", help=tip("MARGEM_LIQUIDA"))

# ========================================
# LEGENDA
# ========================================
st.divider()
st.markdown("""
**Legenda dos Sinais:**

| Sinal | Significado | Critério |
|---|---|---|
| 🟢 **COMPRA FORTE** | Score alto + upside > 20% + sinais técnicos favoráveis | Melhor momento para compra |
| 🔵 **COMPRA** | Score bom + upside > 10% | Boa oportunidade |
| ⚪ **NEUTRO** | Score mediano ou upside limitado | Manter posição se já tiver |
| 🟡 **CAUTELA** | Score baixo ou sinais mistos | Evitar novas compras |
| 🔴 **EVITAR** | Prejuízo, riscos críticos ou sinais de venda | Não comprar |

**Selo Especial:**
- 🌱 **Amigável para iniciantes** — empresa rentável, paga dividendos consistentes, preço razoável e saúde financeira boa. Ideal para quem está começando.

**Preços:**
- **Preço Justo:** Média de 4 métodos (Graham, Bazin, P/L justo, VPA × ROE)
- **Preço Teto:** Preço justo com margem de segurança de 20% (comprar abaixo deste valor)
- **Upside:** Potencial de valorização até o preço justo
""")

st.caption("Fontes: fundamentus.com.br | brapi.dev | Cálculos próprios")
