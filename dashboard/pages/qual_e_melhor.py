import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.collectors.fundamentus_collector import FundamentusCollector  # noqa: E402
from src.processors.recommendation_engine import RecommendationEngine  # noqa: E402
from dashboard.components.ticker_selector import ticker_selectbox  # noqa: E402
from dashboard.components.glossario import tip  # noqa: E402

st.title("🆚 Qual é Melhor? — Comparador de Ações")
st.caption("Compare duas (ou tres) ações lado a lado e veja quem vence em cada critério.")


# ========================================
# Selecao de acoes
# ========================================
col1, col2, col3 = st.columns(3)
with col1:
    ticker1 = ticker_selectbox("Ação 1:", default="ITUB4", key="qem_t1")
with col2:
    ticker2 = ticker_selectbox("Ação 2:", default="BBAS3", key="qem_t2")
with col3:
    incluir_3 = st.checkbox("Comparar 3 ações")
    ticker3 = None
    if incluir_3:
        ticker3 = ticker_selectbox("Ação 3:", default="BBDC4", key="qem_t3")

tickers_sel = [t for t in [ticker1, ticker2, ticker3] if t]

if len(tickers_sel) != len(set(tickers_sel)):
    st.warning("Selecione ações diferentes.")
    st.stop()


# ========================================
# Definicao dos criterios (maior_melhor=True significa que valor mais alto vence)
# ========================================
CRITERIOS = [
    # (chave, nome_amigavel, fonte, maior_melhor, formato, tooltip_key, peso)
    ("dividend_yield", "💰 Dividend Yield (DY)", "fund", True, "{:.2f}%", "DY", 1.5),
    ("roe", "📈 ROE (Rentabilidade)", "fund", True, "{:.2f}%", "ROE", 1.5),
    ("roic", "📊 ROIC", "fund", True, "{:.2f}%", "ROIC", 1.0),
    ("pl", "💲 P/L (preço barato)", "fund", False, "{:.2f}", "PL", 1.2),
    ("pvp", "📕 P/VP", "fund", False, "{:.2f}", "PVP", 1.0),
    ("margem_liquida", "🟢 Margem Líquida", "fund", True, "{:.2f}%", "MARGEM_LIQUIDA", 1.0),
    ("margem_ebit", "⚙️ Margem EBIT", "fund", True, "{:.2f}%", "", 0.8),
    ("liquidez_corrente", "💧 Liquidez Corrente", "fund", True, "{:.2f}", "LIQUIDEZ_CORRENTE", 0.8),
    ("cres_rec_5a", "🚀 Crescimento Receita 5a", "fund", True, "{:.1f}%", "", 1.0),
]


def safe_get(d: dict, key: str):
    v = d.get(key)
    if v is None:
        return None
    try:
        v = float(v)
        if v != v:  # NaN
            return None
        return v
    except (TypeError, ValueError):
        return None


if st.button("Comparar", type="primary"):
    brapi = BrapiCollector()
    fund_collector = FundamentusCollector()
    engine = RecommendationEngine()

    dados_por_ticker = {}
    recs_por_ticker = {}

    with st.spinner("Carregando dados..."):
        for t in tickers_sel:
            try:
                dados_brapi = brapi.get_cotacao(t)
                try:
                    dados_fund = fund_collector.get_indicadores(t)
                except Exception:
                    dados_fund = {}
                dados_por_ticker[t] = {**dados_fund, **{
                    "preço": dados_brapi.get("regularMarketPrice", 0),
                    "variação": dados_brapi.get("regularMarketChangePercent", 0),
                    "empresa": dados_brapi.get("shortName", t),
                }}
                try:
                    recs_por_ticker[t] = engine.analisar_ticker(t)
                except Exception:
                    recs_por_ticker[t] = None
            except Exception as e:
                st.error(f"Erro ao carregar {t}: {e}")
                st.stop()

    # ========================================
    # Header com cotacoes
    # ========================================
    cols_header = st.columns(len(tickers_sel))
    for i, t in enumerate(tickers_sel):
        d = dados_por_ticker[t]
        cols_header[i].markdown(f"### {t}")
        cols_header[i].caption(d.get("empresa", t)[:35])
        cols_header[i].metric(
            "Cotação",
            f"R$ {d['preço']:.2f}",
            f"{d['variação']:+.2f}%",
        )

    st.divider()

    # ========================================
    # Placar de Vencedor
    # ========================================
    st.subheader("🏆 Placar Geral")

    vitorias = {t: 0 for t in tickers_sel}
    pontuacao = {t: 0.0 for t in tickers_sel}
    rows_comparacao = []

    for chave, nome, fonte, maior_melhor, fmt, tooltip_key, peso in CRITERIOS:
        valores = {t: safe_get(dados_por_ticker[t], chave) for t in tickers_sel}

        if all(v is None for v in valores.values()):
            continue

        # Determinar vencedor entre os que tem dado
        valores_validos = {t: v for t, v in valores.items() if v is not None}
        if not valores_validos:
            continue

        if maior_melhor:
            vencedor = max(valores_validos, key=valores_validos.get)
        else:
            # Para PL/PVP, ignorar valores <= 0 (prejuizo ou erro)
            valores_pos = {t: v for t, v in valores_validos.items() if v > 0}
            if not valores_pos:
                continue
            vencedor = min(valores_pos, key=valores_pos.get)

        vitorias[vencedor] += 1
        pontuacao[vencedor] += peso

        linha = {"Critério": nome, "tooltip": tooltip_key}
        for t in tickers_sel:
            v = valores.get(t)
            if v is None:
                linha[t] = "—"
            else:
                marcador = "🏆 " if t == vencedor else ""
                linha[t] = f"{marcador}{fmt.format(v)}"
        rows_comparacao.append(linha)

    # Cards de placar
    cols_placar = st.columns(len(tickers_sel))
    max_pts = max(pontuacao.values()) if pontuacao.values() else 0
    for i, t in enumerate(tickers_sel):
        emoji_pos = "🥇" if pontuacao[t] == max_pts and max_pts > 0 else ""
        cols_placar[i].metric(
            f"{emoji_pos} {t}",
            f"{vitorias[t]} vitorias",
            f"{pontuacao[t]:.1f} pts ponderados",
        )

    # Veredicto
    vencedor_geral = max(pontuacao, key=pontuacao.get)
    pontos_vencedor = pontuacao[vencedor_geral]
    total_pontos = sum(pontuacao.values())
    if total_pontos > 0:
        pct_dominancia = (pontos_vencedor / total_pontos) * 100
        if pct_dominancia >= 60:
            st.success(
                f"🥇 **{vencedor_geral} venceu** em {vitorias[vencedor_geral]} de "
                f"{len(rows_comparacao)} critérios com folga ({pct_dominancia:.0f}% dos pontos)."
            )
        elif pct_dominancia >= 45:
            st.info(
                f"📊 **{vencedor_geral} venceu por pouco** ({vitorias[vencedor_geral]} de "
                f"{len(rows_comparacao)} critérios). Considere os fatores qualitativos."
            )
        else:
            st.warning(
                f"⚖️ **Empate técnico.** Os concorrentes estão muito próximos. "
                "Diversificar entre ambos pode ser uma boa ideia."
            )

    st.divider()

    # ========================================
    # Tabela detalhada com vencedores
    # ========================================
    st.subheader("📋 Comparativo Detalhado")
    st.caption("🏆 = vencedor de cada critério")

    df = pd.DataFrame(rows_comparacao)
    df_show = df.drop(columns=["tooltip"])

    # Estilo: destacar coluna do vencedor
    def cor_vencedor(val):
        if isinstance(val, str) and "🏆" in val:
            return "background-color: #1a5c1a; color: white; font-weight: bold"
        return ""

    styled = df_show.style.map(cor_vencedor, subset=tickers_sel)
    st.dataframe(styled, width="stretch", hide_index=True, height=400)

    st.divider()

    # ========================================
    # Radar — Scores das recomendacoes
    # ========================================
    if any(recs_por_ticker.get(t) for t in tickers_sel):
        st.subheader("🎯 Radar de Scores")
        st.caption("Comparativo de qualidade nos 5 pilares principais (0-100).")

        categorias = ["Saúde", "Valuation", "Dividendos", "Crescimento", "Técnico"]
        cores_ticker = ["#1f77b4", "#ff7f0e", "#2ca02c"]

        fig_radar = go.Figure()
        for i, t in enumerate(tickers_sel):
            rec = recs_por_ticker.get(t)
            if not rec:
                continue
            valores = [
                rec.scores.get("saude", 0),
                rec.scores.get("valuation", 0),
                rec.scores.get("dividendos", 0),
                rec.scores.get("crescimento", 0),
                rec.scores.get("tecnico", 0),
            ]
            fig_radar.add_trace(go.Scatterpolar(
                r=valores + [valores[0]],
                theta=categorias + [categorias[0]],
                fill="toself",
                name=t,
                line_color=cores_ticker[i % len(cores_ticker)],
                opacity=0.6,
            ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=450,
            showlegend=True,
        )
        st.plotly_chart(fig_radar, width="stretch")

        st.divider()

        # ========================================
        # Recomendacao final de cada
        # ========================================
        st.subheader("🎬 Sinal de Recomendação")
        ICONES_SINAL = {
            "COMPRA FORTE": "🟢", "COMPRA": "🔵", "NEUTRO": "⚪",
            "CAUTELA": "🟡", "EVITAR": "🔴",
        }

        cols_sinal = st.columns(len(tickers_sel))
        for i, t in enumerate(tickers_sel):
            rec = recs_por_ticker.get(t)
            if rec:
                cols_sinal[i].metric(
                    f"{t} — {ICONES_SINAL.get(rec.sinal, '')} {rec.sinal}",
                    f"Score: {rec.score_geral:.0f}",
                    f"Upside: {rec.upside_pct:+.1f}%",
                )
            else:
                cols_sinal[i].info(f"{t}: sem análise disponível")

        st.divider()

        # ========================================
        # Motivos lado a lado
        # ========================================
        st.subheader("✅ Motivos para Comprar / ⚠️ Riscos")

        cols_motivos = st.columns(len(tickers_sel))
        for i, t in enumerate(tickers_sel):
            rec = recs_por_ticker.get(t)
            with cols_motivos[i]:
                st.markdown(f"### {t}")
                if rec:
                    st.markdown("**Motivos:**")
                    if rec.motivos:
                        for m in rec.motivos:
                            st.markdown(f"- ✅ {m}")
                    else:
                        st.markdown("- (nenhum motivo forte)")

                    st.markdown("**Riscos:**")
                    if rec.riscos:
                        for r in rec.riscos:
                            st.markdown(f"- ⚠️ {r}")
                    else:
                        st.markdown("- (nenhum risco relevante)")
                else:
                    st.info("Sem análise disponível.")

    st.divider()

    # ========================================
    # Dica final
    # ========================================
    st.info("""
💡 **Dica para iniciantes:**
- Quando duas ações são do **mesmo setor** (ex: ITUB4 vs BBDC4), focar no DY, ROE e P/L.
- Quando são de **setores diferentes** (ex: ITUB4 vs VALE3), pondere conforme seu objetivo:
  - **Renda:** DY mais alto
  - **Crescimento:** ROE/ROIC mais altos
  - **Seguranca:** menor endividamento e maior liquidez corrente
- **Diversificar e melhor que escolher a "melhor"**: comprar as duas em proporcoes diferentes geralmente reduz risco.
    """)

st.caption("Fontes: brapi.dev | fundamentus.com.br")
