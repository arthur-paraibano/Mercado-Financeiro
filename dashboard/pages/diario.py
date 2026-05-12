import random
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.brapi_collector import BrapiCollector  # noqa: E402
from dashboard.components.storage import carregar, salvar  # noqa: E402

st.title("📓 Diário do Investidor")
st.caption("Acompanhe sua carteira, anote decisões e aprenda um pouco a cada dia.")


wl = carregar("watchlist", {"tickers": [], "alertas": {}})
diario = carregar("diario", {"entradas": []})
quiz_prog = carregar("quiz_progresso", {"acertos": 0, "total": 0, "ultima_data": None, "perguntas_feitas": []})


# ========================================
# Tabs
# ========================================
tab1, tab2, tab3 = st.tabs(["📊 Hoje", "✍️ Minhas Anotacoes", "🎓 Quiz do Dia"])


# ========================================
# TAB 1 — Visao do dia
# ========================================
with tab1:
    st.header(f"Visão do Dia — {date.today().strftime('%d/%m/%Y')}")

    if not wl["tickers"]:
        st.info("Você ainda não tem ações na watchlist. Adicione em **⭐ Watchlist** para ver o resumo aqui.")
    else:
        brapi = BrapiCollector()
        rows = []

        with st.spinner("Carregando cotações da sua carteira..."):
            cotacoes = brapi.get_cotacao_lote(wl["tickers"])

        for t in wl["tickers"]:
            d = cotacoes.get(t)
            if d:
                rows.append({
                    "Ticker": t,
                    "Preço": d.get("regularMarketPrice", 0) or 0,
                    "Variação": d.get("regularMarketChangePercent", 0) or 0,
                    "Volume": d.get("regularMarketVolume", 0) or 0,
                })

        if rows:
            df = pd.DataFrame(rows)
            variacao_media = df["Variação"].mean()
            altas = df[df["Variação"] > 0]
            quedas = df[df["Variação"] < 0]

            # Resumo
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(
                "Variação Média",
                f"{variacao_media:+.2f}%",
                delta="bom dia" if variacao_media > 0 else "dia dificil" if variacao_media < -1 else "neutro",
            )
            col2.metric("Ações em Alta 🟢", len(altas))
            col3.metric("Ações em Queda 🔴", len(quedas))

            # Maior alta/queda
            if not df.empty:
                maior_alta = df.loc[df["Variação"].idxmax()]
                maior_queda = df.loc[df["Variação"].idxmin()]
                col4.metric(
                    "Destaque do dia",
                    f"{maior_alta['Ticker']}: {maior_alta['Variação']:+.2f}%",
                    f"{maior_queda['Ticker']}: {maior_queda['Variação']:+.2f}%",
                )

            # Tabela
            st.divider()
            st.subheader("Suas ações hoje")

            def cor_var(v):
                if v > 2:
                    return "background-color: #1a5c1a; color: white"
                elif v > 0:
                    return "background-color: #2d6a2e; color: white"
                elif v < -2:
                    return "background-color: #8c1a1a; color: white"
                elif v < 0:
                    return "background-color: #7a2020; color: white"
                return ""

            df_sorted = df.sort_values("Variação", ascending=False)
            styled = df_sorted.style.map(cor_var, subset=["Variação"]).format({
                "Preço": "R$ {:.2f}",
                "Variação": "{:+.2f}%",
                "Volume": "{:,.0f}",
            })
            st.dataframe(styled, width="stretch", hide_index=True)

            # Dica do dia
            st.divider()
            DICAS = [
                "💡 **Não olhe a carteira todo dia.** O preço oscila — fundamentos mudam devagar.",
                "💡 **Dividendos são reinvestidos** automaticamente se você comprar mais ações. Esse e o segredo do juro composto.",
                "💡 **Quando o mercado cai, geralmente e quando se ganha dinheiro a longo prazo.** Comprar barato e dificil emocionalmente.",
                "💡 **Diversifique entre setores diferentes.** Bancos, energia, consumo, saúde — cada um reage diferente a crises.",
                "💡 **Nunca invista por 'dica de amigo' ou influencer.** Estude os fundamentos da empresa antes.",
                "💡 **Tenha uma reserva de emergência** em Tesouro Selic antes de comprar ações.",
                "💡 **Ações são para o longo prazo.** Menos de 5 anos? Va de renda fixa.",
                "💡 **DY alto demais (>15%) e suspeito.** Ou a empresa caiu muito, ou o dividendo não e sustentavel.",
                "💡 **ROE consistente acima de 15% por 5+ anos** e um dos melhores sinais de empresa de qualidade.",
                "💡 **P/L baixo nem sempre e barato.** Empresas em crise tem P/L baixo. Investigue antes de comprar.",
                "💡 **Aporte regularmente** (mensal). Isso e mais importante que tentar acertar o melhor momento.",
            ]
            dica_idx = date.today().toordinal() % len(DICAS)
            st.info(DICAS[dica_idx])

        else:
            st.warning("Não foi possível carregar suas cotações.")


# ========================================
# TAB 2 — Anotacoes
# ========================================
with tab2:
    st.header("Minhas Anotacoes de Investimento")
    st.caption("Anote por que você comprou cada ação, suas expectativas e revisoes. Ajuda a aprender com erros e acertos.")

    with st.expander("➕ Nova Anotacao", expanded=len(diario["entradas"]) == 0):
        col1, col2 = st.columns([1, 2])
        with col1:
            tipo = st.selectbox("Tipo:", ["📝 Observacao", "🛒 Comprei", "💸 Vendi", "🎯 Decisão", "📚 Estudo"])
            ticker_opt = st.text_input("Ticker (opcional):", placeholder="Ex: PETR4")
        with col2:
            texto = st.text_area("Anotacao:", placeholder="Por que você esta acompanhando ou tomou essa decisão?", height=100)

        if st.button("Salvar Anotacao", type="primary"):
            if texto.strip():
                diario["entradas"].insert(0, {
                    "data": datetime.now().isoformat(),
                    "tipo": tipo,
                    "ticker": ticker_opt.upper().strip() if ticker_opt else None,
                    "texto": texto.strip(),
                })
                salvar("diario", diario)
                st.success("Anotacao salva!")
                st.rerun()
            else:
                st.warning("Escreva algo antes de salvar.")

    st.divider()

    # Filtro
    filtro_ticker = st.text_input("🔎 Filtrar por ticker:", placeholder="Ex: VALE3 (deixe vazio para ver todos)")

    entradas_filtradas = diario["entradas"]
    if filtro_ticker:
        entradas_filtradas = [e for e in entradas_filtradas if e.get("ticker") == filtro_ticker.upper().strip()]

    if not entradas_filtradas:
        st.info("Nenhuma anotacao encontrada. Use o formulario acima para registrar suas decisões!")
    else:
        st.subheader(f"{len(entradas_filtradas)} anotacao(oes)")

        for i, entrada in enumerate(entradas_filtradas):
            dt = datetime.fromisoformat(entrada["data"])
            data_str = dt.strftime("%d/%m/%Y %H:%M")
            ticker_tag = f" — `{entrada['ticker']}`" if entrada.get("ticker") else ""

            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{entrada['tipo']}**{ticker_tag}  \n*{data_str}*")
                    st.markdown(entrada["texto"])
                with col2:
                    if st.button("🗑️", key=f"del_{i}", help="Excluir anotacao"):
                        diario["entradas"].remove(entrada)
                        salvar("diario", diario)
                        st.rerun()


# ========================================
# TAB 3 — Quiz
# ========================================
with tab3:
    st.header("Quiz do Dia — Aprenda Investindo")

    PERGUNTAS = [
        {
            "p": "O que e Dividend Yield (DY)?",
            "opções": [
                "Lucro por ação",
                "Dividendos pagos / cotação da ação",
                "Crescimento esperado da empresa",
                "Imposto pago sobre dividendos",
            ],
            "correta": 1,
            "explicação": "DY = dividendos pagos no ano / preço da ação. Um DY de 6% significa que você recebe 6% do valor investido em dinheiro por ano.",
        },
        {
            "p": "Um P/L de 8 geralmente indica:",
            "opções": [
                "Ação cara",
                "Ação em prejuizo",
                "Ação potencialmente barata (mas verifique o setor)",
                "Empresa que não paga dividendos",
            ],
            "correta": 2,
            "explicação": "P/L 8 significa que você paga 8 anos de lucro pela ação — geralmente considerado barato. Mas atenção: empresas em problema tambem tem P/L baixo.",
        },
        {
            "p": "Antes de investir em ações, você deve ter:",
            "opções": [
                "Pelo menos R$ 100.000",
                "Reserva de emergência equivalente a 6 meses de despesas",
                "Conhecimento avancado de análise técnica",
                "Conta em corretora premium",
            ],
            "correta": 1,
            "explicação": "A regra de ouro: monte uma reserva de 6 meses em Tesouro Selic ANTES de investir em ações. Ações oscilam — você não quer ser obrigado a vender no fundo.",
        },
        {
            "p": "Diversificação significa:",
            "opções": [
                "Comprar muitas ações da mesma empresa",
                "Investir em ações de varios setores e empresas",
                "Comprar so empresas estrangeiras",
                "Trocar de ação toda semana",
            ],
            "correta": 1,
            "explicação": "Diversificar = espalhar o risco em varios setores (bancos, energia, consumo, saúde...). Se um setor cai, os outros podem proteger sua carteira.",
        },
        {
            "p": "ROE alto (acima de 15%) significa:",
            "opções": [
                "A ação esta cara",
                "A empresa endividou muito",
                "A empresa e eficiente em gerar lucro com o patrimonio",
                "A empresa não paga dividendos",
            ],
            "correta": 2,
            "explicação": "ROE = Return on Equity. Mede o quanto a empresa lucra em relacao ao patrimonio dos socios. Acima de 15% por varios anos = sinal de qualidade.",
        },
        {
            "p": "Qual e a melhor estratégia para iniciantes?",
            "opções": [
                "Comprar e vender toda semana (day trade)",
                "Apostar tudo na 'próxima Tesla'",
                "Aportar mensalmente em empresas sólidas, pensando em 5-10 anos",
                "Seguir a dica do influencer com mais seguidores",
            ],
            "correta": 2,
            "explicação": "Para iniciantes: aportes regulares (DCA - Dollar Cost Averaging) em empresas sólidas, com horizonte longo. Day trade tem 90%+ de prejuizo entre iniciantes.",
        },
        {
            "p": "Quando uma empresa paga dividendos, o que acontece com o preço da ação?",
            "opções": [
                "Sobe pelo valor do dividendo",
                "Cai aproximadamente pelo valor do dividendo (data ex)",
                "Não muda",
                "Dobra de preço",
            ],
            "correta": 1,
            "explicação": "Na 'data ex', o preço da ação cai pelo valor do dividendo, pois quem comprar depois não recebe esse dividendo. E uma transferencia de valor da empresa para o acionista.",
        },
        {
            "p": "O que e Ibovespa?",
            "opções": [
                "Uma corretora de ações",
                "O índice das principais ações da B3",
                "Um tipo de imposto",
                "O nome do CEO da bolsa",
            ],
            "correta": 1,
            "explicação": "Ibovespa e o principal índice da bolsa brasileira (B3), composto por ~80 ações mais negociadas. E o 'termometro' do mercado acionario brasileiro.",
        },
        {
            "p": "Qual destes NAO e um bom motivo para vender uma ação?",
            "opções": [
                "A tese original mudou (empresa entrou em crise)",
                "Você precisa do dinheiro agora",
                "A ação caiu 5% essa semana",
                "Você achou uma oportunidade muito melhor",
            ],
            "correta": 2,
            "explicação": "Oscilacoes de curto prazo (-5%) são normais e não justificam venda. So venda se: (1) a tese mudou, (2) precisa do dinheiro, ou (3) ha alternativa claramente melhor.",
        },
        {
            "p": "Liquidez de uma ação significa:",
            "opções": [
                "Quanto a empresa lucra",
                "Facilidade de comprar e vender sem afetar muito o preço",
                "Quantos dividendos paga",
                "Tamanho da empresa",
            ],
            "correta": 1,
            "explicação": "Ação com alta liquidez (ex: PETR4, VALE3) e facil negociar a qualquer momento. Baixa liquidez = pode demorar para vender ou ter que aceitar preço ruim.",
        },
    ]

    hoje_iso = date.today().isoformat()
    ja_respondeu_hoje = quiz_prog.get("ultima_data") == hoje_iso

    # Estatisticas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Acertos", quiz_prog.get("acertos", 0))
    col2.metric("Perguntas Respondidas", quiz_prog.get("total", 0))
    taxa = (quiz_prog["acertos"] / quiz_prog["total"] * 100) if quiz_prog.get("total", 0) > 0 else 0
    col3.metric("Taxa de Acerto", f"{taxa:.0f}%")

    st.divider()

    if ja_respondeu_hoje:
        st.info("✅ **Você já respondeu o quiz de hoje.** Volte amanha para uma nova pergunta!")
        if st.button("🔄 Quero responder outra mesmo assim"):
            quiz_prog["ultima_data"] = None
            salvar("quiz_progresso", quiz_prog)
            st.rerun()
    else:
        # Selecionar pergunta nao feita recentemente
        feitas_recentes = set(quiz_prog.get("perguntas_feitas", [])[-7:])
        disponiveis = [i for i in range(len(PERGUNTAS)) if i not in feitas_recentes]
        if not disponiveis:
            disponiveis = list(range(len(PERGUNTAS)))

        # Seed por data para consistencia ao recarregar
        random.seed(hoje_iso)
        idx_pergunta = random.choice(disponiveis)
        p = PERGUNTAS[idx_pergunta]

        st.markdown(f"### {p['p']}")

        resposta_idx = st.radio(
            "Escolha:",
            range(len(p["opções"])),
            format_func=lambda i: p["opções"][i],
            key=f"quiz_{idx_pergunta}",
        )

        if st.button("Responder", type="primary"):
            quiz_prog["total"] += 1
            if resposta_idx == p["correta"]:
                quiz_prog["acertos"] += 1
                st.balloons()
                st.success(f"🎉 **Correto!** {p['explicação']}")
            else:
                certa = p["opções"][p["correta"]]
                st.error(f"❌ **Errado.** A resposta correta era: **{certa}**.\n\n{p['explicação']}")

            quiz_prog["ultima_data"] = hoje_iso
            quiz_prog.setdefault("perguntas_feitas", []).append(idx_pergunta)
            salvar("quiz_progresso", quiz_prog)

st.caption("Seus dados ficam salvos localmente em `dashboard/data/`")
