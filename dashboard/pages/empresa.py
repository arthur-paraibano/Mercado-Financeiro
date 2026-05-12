import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Adicionar raiz do projeto ao path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from src.collectors.fundamentus_collector import FundamentusCollector  # noqa: E402
from src.collectors.yahoo_collector import YahooCollector  # noqa: E402
from dashboard.components.ticker_selector import ticker_selectbox  # noqa: E402
from dashboard.components.glossario import tip  # noqa: E402

st.title("Análise de Empresa")

ticker = ticker_selectbox("Selecione a ação:", default="WEGE3", key="empresa_ticker")

if st.button("Analisar", type="primary") or ticker:
    if not ticker:
        st.warning("Selecione um ticker para analisar.")
        st.stop()

    with st.spinner(f"Buscando dados de {ticker}..."):
        try:
            # Buscar dados das duas fontes
            brapi = BrapiCollector()
            fund = FundamentusCollector()

            dados_brapi = brapi.get_cotacao(ticker)
            try:
                dados_fund = fund.get_papel(ticker)
            except Exception:
                dados_fund = {}

            # --- Linha 1: Preco e info basica ---
            preco = dados_brapi.get("regularMarketPrice", 0)
            variacao = dados_brapi.get("regularMarketChangePercent", 0)
            market_cap = dados_fund.get("market_cap") or dados_brapi.get("marketCap", 0)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Preço", f"R$ {preço:.2f}", f"{variação:.2f}%")
            col2.metric(
                "Market Cap",
                f"R$ {market_cap / 1e9:.1f}B" if market_cap else "N/A",
            )
            col3.metric("Nome", dados_brapi.get("longName", ticker)[:30])
            col4.metric(
                "Setor",
                dados_fund.get("setor") or dados_brapi.get("sector", "N/A"),
            )

            st.divider()

            # --- Linha 2: Valuation (Fundamentus como fonte primaria) ---
            st.subheader("Valuation")
            col1, col2, col3, col4, col5 = st.columns(5)

            pl = dados_fund.get("pl") or dados_brapi.get("priceEarnings")
            col1.metric("P/L", f"{pl:.2f}" if pl else "N/A", help=tip("PL"))

            pvp = dados_fund.get("pvp") or dados_brapi.get("priceToBook")
            col2.metric("P/VP", f"{pvp:.2f}" if pvp else "N/A", help=tip("PVP"))

            ev_ebitda = dados_fund.get("ev_ebitda") or dados_brapi.get("enterpriseValueOverEbitda")
            col3.metric("EV/EBITDA", f"{ev_ebitda:.2f}" if ev_ebitda else "N/A", help=tip("EV_EBITDA"))

            psr = dados_fund.get("psr") or dados_brapi.get("priceToSalesTrailing12Months")
            col4.metric("PSR", f"{psr:.2f}" if psr else "N/A", help="Preço / Receita: quanto você paga por R$ 1 de receita anual.")

            dy = dados_fund.get("dividend_yield")
            col5.metric("DY", f"{dy:.2f}%" if dy else "N/A", help=tip("DY"))

            st.divider()

            # --- Linha 3: Rentabilidade ---
            st.subheader("Rentabilidade")
            col1, col2, col3, col4, col5 = st.columns(5)

            roe = dados_fund.get("roe")
            col1.metric("ROE", f"{roe:.2f}%" if roe else "N/A", help=tip("ROE"))

            roic = dados_fund.get("roic")
            col2.metric("ROIC", f"{roic:.2f}%" if roic else "N/A", help=tip("ROIC"))

            margem_liq = dados_fund.get("margem_liquida")
            col3.metric("Margem Líquida", f"{margem_liq:.2f}%" if margem_liq else "N/A", help=tip("MARGEM_LIQUIDA"))

            margem_bruta = dados_fund.get("margem_bruta")
            col4.metric("Margem Bruta", f"{margem_bruta:.2f}%" if margem_bruta else "N/A", help="% do que sobra depois dos custos diretos do produto/servico.")

            margem_ebit = dados_fund.get("margem_ebit")
            col5.metric("Margem EBIT", f"{margem_ebit:.2f}%" if margem_ebit else "N/A", help="% da receita que vira lucro operacional (antes de impostos e juros).")

            st.divider()

            # --- Linha 4: Endividamento ---
            st.subheader("Endividamento")
            col1, col2, col3, col4 = st.columns(4)

            divida_bruta = dados_fund.get("divida_bruta")
            col1.metric(
                "Dívida Bruta",
                f"R$ {divida_bruta / 1e9:.2f}B" if divida_bruta else "N/A",
            )

            divida_liq = dados_fund.get("divida_liquida")
            col2.metric(
                "Dívida Líquida",
                f"R$ {divida_liq / 1e9:.2f}B" if divida_liq else "N/A",
            )

            patrimonio = dados_fund.get("patrimonio_liq")
            col3.metric(
                "Patrimonio Liq.",
                f"R$ {patrimonio / 1e9:.2f}B" if patrimonio else "N/A",
            )

            liq_corr = dados_fund.get("liquidez_corrente")
            col4.metric("Liquidez Corrente", f"{liq_corr:.2f}" if liq_corr else "N/A", help=tip("LIQUIDEZ_CORRENTE"))

            st.divider()

            # --- Linha 5: Resultados 12 meses ---
            st.subheader("Resultados (últimos 12 meses)")
            col1, col2, col3, col4 = st.columns(4)

            receita = dados_fund.get("receita_12m")
            col1.metric(
                "Receita Líquida",
                f"R$ {receita / 1e9:.2f}B" if receita else "N/A",
            )

            ebit = dados_fund.get("ebit_12m")
            col2.metric(
                "EBIT",
                f"R$ {ebit / 1e9:.2f}B" if ebit else "N/A",
            )

            lucro = dados_fund.get("lucro_liquido_12m")
            col3.metric(
                "Lucro Líquido",
                f"R$ {lucro / 1e9:.2f}B" if lucro else "N/A",
            )

            cres_5a = dados_fund.get("cres_rec_5a")
            col4.metric("Cresc. Receita 5a", f"{cres_5a:.1f}%" if cres_5a else "N/A")

            st.divider()

            # --- Linha 6: Por acao ---
            st.subheader("Por Ação")
            col1, col2, col3, col4 = st.columns(4)

            lpa = dados_fund.get("lpa")
            col1.metric("LPA", f"R$ {lpa:.2f}" if lpa else "N/A")

            vpa = dados_fund.get("vpa")
            col2.metric("VPA", f"R$ {vpa:.2f}" if vpa else "N/A")

            min52 = dados_fund.get("min_52sem")
            col3.metric("Min. 52 sem", f"R$ {min52:.2f}" if min52 else "N/A")

            max52 = dados_fund.get("max_52sem")
            col4.metric("Max. 52 sem", f"R$ {max52:.2f}" if max52 else "N/A")

            st.divider()

            # --- Grafico de historico ---
            periodo = st.selectbox("Período:", ["1d", "5d", "1mo", "3mo"], index=2)
            st.subheader(f"Histórico de Cotações - {ticker}")
            historico = brapi.get_historico(ticker, periodo, "1d")

            if historico:
                df = pd.DataFrame(historico)
                df["date"] = pd.to_datetime(df["date"], unit="s")

                fig = go.Figure()
                fig.add_trace(
                    go.Candlestick(
                        x=df["date"],
                        open=df["open"],
                        high=df["high"],
                        low=df["low"],
                        close=df["close"],
                        name=ticker,
                    )
                )
                fig.update_layout(
                    xaxis_rangeslider_visible=False,
                    height=450,
                    margin=dict(l=0, r=0, t=30, b=0),
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Histórico de cotações indisponivel.")

            # --- Dividendos ---
            st.subheader("Dividendos")

            yahoo = YahooCollector()
            df_div = yahoo.get_dividendos(ticker)

            if not df_div.empty:
                col1, col2, col3 = st.columns(3)
                col1.metric("DY Atual", f"{dy:.2f}%" if dy else "N/A")

                total_12m = df_div[
                    df_div["Data"] >= pd.Timestamp.now() - pd.DateOffset(years=1)
                ]["Valor"].sum()
                col2.metric("Total Pago (12m)", f"R$ {total_12m:.2f}")
                col3.metric("Total de Registros", len(df_div))

                # Tabela com ultimos 15 pagamentos
                df_show = df_div.head(15).copy()
                df_show["Data"] = df_show["Data"].dt.strftime("%d/%m/%Y")
                df_show["Valor"] = df_show["Valor"].apply(lambda v: f"R$ {v:.6f}")
                st.dataframe(df_show, width="stretch", hide_index=True)

                # Grafico de dividendos por ano
                df_ano = df_div.copy()
                df_ano["Ano"] = df_ano["Data"].dt.year
                div_por_ano = df_ano.groupby("Ano")["Valor"].sum().reset_index()
                div_por_ano.columns = ["Ano", "Total"]

                import plotly.express as px
                fig = px.bar(
                    div_por_ano.sort_values("Ano"),
                    x="Ano", y="Total",
                    title="Dividendos Pagos por Ano",
                    labels={"Total": "R$ por ação", "Ano": ""},
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sem dados de dividendos disponíveis para esta empresa.")

            # --- Fonte dos dados ---
            st.caption("Fontes: brapi.dev (cotações) + fundamentus.com.br (indicadores)")

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
