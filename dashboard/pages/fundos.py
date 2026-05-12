import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.cvm_fundos_collector import CVMFundosCollector  # noqa: E402
from src.processors.smart_money_analyzer import SmartMoneyAnalyzer  # noqa: E402
from dashboard.components.ticker_selector import ticker_selectbox  # noqa: E402

st.title("Fundos de Investimento - Smart Money")

st.info(
    "Esta pagina baixa carteiras mensais dos fundos diretamente da CVM. "
    "Os arquivos são grandes (~200MB) e podem demorar alguns minutos."
)

ticker = ticker_selectbox("Selecione a ação:", default="PETR4", key="fundos_ticker")

col1, col2 = st.columns(2)
hoje = date.today()
# CVM tem atraso de ~2-3 meses
with col1:
    ano = st.number_input("Ano:", min_value=2020, max_value=hoje.year, value=hoje.year)
with col2:
    mes_default = max(1, hoje.month - 3)
    mes = st.number_input("Mês:", min_value=1, max_value=12, value=mes_default)

if st.button("Analisar Fundos", type="primary"):
    cvm = CVMFundosCollector()
    analyzer = SmartMoneyAnalyzer()

    # --- Baixar carteiras ---
    with st.spinner(f"Baixando carteiras da CVM ({ano}/{mes:02d})... Pode demorar."):
        carteira = cvm.get_carteira_mensal(ano, mes)

    if carteira.empty:
        st.error(
            f"Carteiras de {ano}/{mes:02d} indisponiveis. "
            "A CVM tem atraso de 2-3 meses na publicacao. Tente um mes anterior."
        )
        st.stop()

    st.success(f"Carteiras carregadas: {len(carteira):,} posicoes totais.")

    # --- Concentracao ---
    st.subheader(f"Concentração de Fundos em {ticker}")
    concentracao = analyzer.analisar_concentracao(carteira, ticker)

    col1, col2, col3 = st.columns(3)
    col1.metric("Fundos com posicao", concentracao["num_fundos"])
    col2.metric("Concentração Top 5", f"{concentração['concentracao_top5_pct']:.1f}%")
    col3.metric("Risco Concentração", concentracao["risco_concentracao"])

    if concentracao["valor_total"] > 0:
        st.metric(
            "Valor Total em Fundos",
            f"R$ {concentração['valor_total'] / 1e9:.2f}B",
        )

    st.divider()

    # --- Top 20 fundos ---
    st.subheader(f"Top 20 Fundos com Maior Posicao em {ticker}")
    top_fundos = cvm.ranking_fundos_por_acao(carteira, ticker, top_n=20)

    if not top_fundos.empty:
        # Tentar enriquecer com nomes
        with st.spinner("Buscando nomes dos fundos..."):
            cadastro = cvm.get_cadastro_fundos()

        if not cadastro.empty and "CNPJ_FUNDO" in top_fundos.columns:
            col_nome = None
            for col in ["DENOM_SOCIAL", "NM_FANTASIA"]:
                if col in cadastro.columns:
                    col_nome = col
                    break

            if col_nome:
                top_fundos = top_fundos.merge(
                    cadastro[["CNPJ_FUNDO", col_nome]].drop_duplicates(subset=["CNPJ_FUNDO"]),
                    on="CNPJ_FUNDO", how="left",
                )
                top_fundos["nome"] = top_fundos[col_nome].fillna(top_fundos["CNPJ_FUNDO"])
            else:
                top_fundos["nome"] = top_fundos["CNPJ_FUNDO"]
        else:
            top_fundos["nome"] = top_fundos.get("CNPJ_FUNDO", range(len(top_fundos)))

        top_fundos["valor_MM"] = top_fundos["valor_total"] / 1e6

        fig = px.bar(
            top_fundos.head(15),
            x="valor_MM",
            y="nome",
            orientation="h",
            title=f"Posicao em {ticker} por Fundo (R$ Milhoes)",
            labels={"valor_MM": "R$ Milhoes", "nome": ""},
        )
        fig.update_layout(height=500, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")

        st.dataframe(
            top_fundos[["nome", "valor_total"]].rename(
                columns={"nome": "Fundo", "valor_total": "Valor (R$)"}
            ).style.format({"Valor (R$)": "R$ {:,.0f}"}),
            width="stretch",
            hide_index=True,
        )

        # --- Smart Money ---
        st.divider()
        st.subheader("Smart Money - Gestoras de Referencia")

        if not cadastro.empty:
            smart = analyzer.identificar_smart_money(carteira, cadastro, ticker)
            if not smart.empty:
                smart["valor_MM"] = smart["valor_total"] / 1e6
                fig = px.bar(
                    smart,
                    x="valor_MM", y="gestora",
                    orientation="h",
                    title=f"Gestoras de Referencia com Posicao em {ticker}",
                    labels={"valor_MM": "R$ Milhoes", "gestora": ""},
                    color="valor_MM",
                    color_continuous_scale="Greens",
                )
                fig.update_layout(height=400, yaxis=dict(autorange="reversed"), showlegend=False)
                st.plotly_chart(fig, width="stretch")

                st.dataframe(
                    smart[["gestora", "num_fundos", "valor_total"]].rename(columns={
                        "gestora": "Gestora",
                        "num_fundos": "Fundos",
                        "valor_total": "Valor Total (R$)",
                    }).style.format({"Valor Total (R$)": "R$ {:,.0f}"}),
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info(f"Nenhuma gestora de referencia encontrada com posicao em {ticker}.")
        else:
            st.warning("Cadastro de fundos indisponivel para identificar gestoras.")
    else:
        st.warning(f"Nenhum fundo encontrado com posicao em {ticker} neste período.")

st.caption("Fonte: CVM - Portal de Dados Abertos (carteiras de fundos)")
