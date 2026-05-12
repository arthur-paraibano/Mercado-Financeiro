import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.components.formatos import fmt_brl, fmt_num, fmt_pct  # noqa: E402

PERFIL_FILE = Path(__file__).parent.parent / "data" / "perfil.json"

st.title("🎓 Começar Aqui — Guia do Investidor Iniciante")
st.caption("Antes de comprar sua primeira ação, vamos garantir que você está no caminho certo.")


def carregar_perfil() -> dict:
    if PERFIL_FILE.exists():
        try:
            return json.loads(PERFIL_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def salvar_perfil(data: dict):
    PERFIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    PERFIL_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


perfil = carregar_perfil()

# ========================================
# Tabs do wizard
# ========================================
tabs = st.tabs([
    "1️⃣ O que é investir?",
    "2️⃣ Reserva de Emergência",
    "3️⃣ Perfil de Risco",
    "4️⃣ Quanto Investir",
    "5️⃣ Sua Carteira",
])

# ========================================
# TAB 1 — Conceitos básicos
# ========================================
with tabs[0]:
    st.header("Você sabe o que vai fazer?")

    with st.expander("O que é uma ação?", expanded=True):
        st.markdown("""
Quando você **compra uma ação**, você se torna **sócio** de uma empresa — mesmo que de uma fatia minúscula.

**Exemplo simples:**
- A Petrobras tem ~13 bilhões de ações no mercado.
- Você compra 100 ações da PETR4 a R$ 35,00.
- Você passa a ser **sócio com 0,0000007% da Petrobras**.
- Se a empresa lucrar e distribuir dividendos, você recebe sua parte.
- Se a empresa valorizar, suas ações também valorizam.
        """)

    with st.expander("Como ganhar dinheiro com ações?"):
        st.markdown("""
Existem **2 formas** principais:

1. **Valorização** — Comprar barato e vender mais caro (geralmente no longo prazo)
2. **Dividendos** — Receber periodicamente parte do lucro da empresa em dinheiro

**Atenção:** você TAMBÉM pode perder. Se a empresa quebrar, suas ações podem virar zero.
Por isso a regra de ouro: **NUNCA coloque em ações dinheiro que você vai precisar nos próximos 5 anos.**
        """)

    with st.expander("Quanto rende investir em ações?"):
        st.markdown("""
**Historicamente** (Ibovespa, últimos 25 anos):
- Média de **~12% ao ano** (acima da inflação)
- Mas com **muita volatilidade**: anos de +50% e anos de -40%

**Comparativo:**
- 📈 Ações: ~12% a.a. (com risco)
- 🏦 Tesouro Selic: ~11% a.a. (sem risco, hoje)
- 💰 Poupança: ~6% a.a. (perde para a inflação)

Por que investir em ações então? Porque a longo prazo (10+ anos), elas tendem a ganhar.
**Curto prazo = risco. Longo prazo = oportunidade.**
        """)

    with st.expander("Onde abrir conta para investir?"):
        st.markdown("""
Você precisa de uma **corretora**. São gratuitas e regulamentadas pela CVM.

**Mais populares no Brasil:**
- **XP Investimentos** — completa, atendimento bom
- **Rico** — interface simples, ligada à XP
- **Clear** — focada em day trade, taxa zero
- **NuInvest** — integrada ao Nubank
- **Inter** — banco digital com corretora
- **Itaú, Bradesco** — bancos tradicionais (taxas maiores)

✅ **Dica:** procure por "corretagem zero" em ações. A maioria hoje cobra zero.
        """)

    st.success("👉 **Próximo passo:** vamos verificar se você tem reserva de emergência antes de investir!")


# ========================================
# TAB 2 — Reserva de Emergência
# ========================================
with tabs[1]:
    st.header("⛑️ Você TEM reserva de emergência?")
    st.markdown(
        "**Antes de comprar ações**, você precisa de uma reserva guardada em "
        "lugar **seguro e com liquidez** (Tesouro Selic ou CDB de liquidez diária 100% CDI)."
    )

    col1, col2 = st.columns(2)
    with col1:
        despesa_mensal = st.number_input(
            "Quanto você gasta por mês (em média)? (R$)",
            min_value=0,
            value=perfil.get("despesa_mensal", 3000),
            step=100,
            help="Some aluguel/financiamento + alimentação + transporte + contas + lazer.",
        )
    with col2:
        reserva_atual = st.number_input(
            "Quanto você já tem guardado em reserva? (R$)",
            min_value=0,
            value=perfil.get("reserva_atual", 0),
            step=500,
            help="Só conta o que está em Tesouro Selic, CDB líquido ou poupança.",
        )

    reserva_ideal_6m = despesa_mensal * 6
    reserva_ideal_12m = despesa_mensal * 12

    perfil["despesa_mensal"] = despesa_mensal
    perfil["reserva_atual"] = reserva_atual

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Reserva Ideal (6 meses)", fmt_brl(reserva_ideal_6m, 0))
    col2.metric("Reserva Ideal (12 meses)", fmt_brl(reserva_ideal_12m, 0))
    pct_alvo = (reserva_atual / reserva_ideal_6m * 100) if reserva_ideal_6m > 0 else 0
    col3.metric(
        "Você já tem",
        fmt_brl(reserva_atual, 0),
        f"{fmt_pct(pct_alvo, 0)} do alvo" if reserva_ideal_6m > 0 else None,
    )

    if reserva_atual >= reserva_ideal_6m:
        st.success(
            "🎉 **Parabéns!** Você já tem reserva de emergência de pelo menos 6 meses. "
            "Você está pronto para começar a investir em ações."
        )
        perfil["reserva_ok"] = True
    elif reserva_atual >= despesa_mensal * 3:
        meses_atual = reserva_atual // despesa_mensal if despesa_mensal > 0 else 0
        st.warning(
            f"⚠️ Você tem reserva para ~{int(meses_atual)} meses. "
            f"O ideal é ter pelo menos **6 meses ({fmt_brl(reserva_ideal_6m, 0)})**. "
            "Você pode começar a investir pequenas quantias, mas priorize completar a reserva."
        )
        perfil["reserva_ok"] = False
    else:
        st.error(
            f"🚨 **Antes de comprar ações**, monte sua reserva de emergência! "
            f"Você precisa de pelo menos **{fmt_brl(reserva_ideal_6m, 0)}** "
            f"em **Tesouro Selic** ou **CDB liquidez diária 100% CDI**."
        )
        st.markdown("""
**Como montar reserva (sem estresse):**

1. Abra conta na corretora (XP, Rico, Inter, etc.)
2. Compre **Tesouro Selic 2029** (ou similar)
3. Aporte mensalmente uma parte do salário até atingir 6 meses de despesa
4. **Só depois** comece em ações
        """)
        perfil["reserva_ok"] = False


# ========================================
# TAB 3 — Perfil de Risco
# ========================================
with tabs[2]:
    st.header("🎯 Qual é o seu perfil de risco?")
    st.markdown("Responda honestamente. Não existe resposta certa — existe resposta verdadeira.")

    q1 = st.radio(
        "**1. Se sua carteira cair 30% em 1 mês, você:**",
        [
            "Vendo tudo, não aguento perder mais.",
            "Fico preocupado, mas mantenho.",
            "Aproveito a queda e compro mais.",
        ],
        index=perfil.get("q1_idx", 1),
        key="q1",
    )

    q2 = st.radio(
        "**2. Seu objetivo principal é:**",
        [
            "Preservar o que tenho, com baixo risco.",
            "Crescer aos poucos, aceitando alguma oscilação.",
            "Multiplicar meu capital, mesmo com volatilidade alta.",
        ],
        index=perfil.get("q2_idx", 1),
        key="q2",
    )

    q3 = st.radio(
        "**3. Seu horizonte de investimento é:**",
        [
            "Menos de 2 anos.",
            "De 2 a 5 anos.",
            "Mais de 5 anos.",
        ],
        index=perfil.get("q3_idx", 1),
        key="q3",
    )

    q4 = st.radio(
        "**4. Sua experiência com ações é:**",
        [
            "Nenhuma. É minha primeira vez.",
            "Já investi um pouco antes.",
            "Tenho boa experiência e estudo o mercado.",
        ],
        index=perfil.get("q4_idx", 0),
        key="q4",
    )

    opcoes_map = {
        "Vendo tudo, não aguento perder mais.": 0,
        "Fico preocupado, mas mantenho.": 1,
        "Aproveito a queda e compro mais.": 2,
        "Preservar o que tenho, com baixo risco.": 0,
        "Crescer aos poucos, aceitando alguma oscilação.": 1,
        "Multiplicar meu capital, mesmo com volatilidade alta.": 2,
        "Menos de 2 anos.": 0,
        "De 2 a 5 anos.": 1,
        "Mais de 5 anos.": 2,
        "Nenhuma. É minha primeira vez.": 0,
        "Já investi um pouco antes.": 1,
        "Tenho boa experiência e estudo o mercado.": 2,
    }

    score = opcoes_map[q1] + opcoes_map[q2] + opcoes_map[q3] + opcoes_map[q4]

    perfil["q1_idx"] = [
        "Vendo tudo, não aguento perder mais.",
        "Fico preocupado, mas mantenho.",
        "Aproveito a queda e compro mais.",
    ].index(q1)
    perfil["q2_idx"] = [
        "Preservar o que tenho, com baixo risco.",
        "Crescer aos poucos, aceitando alguma oscilação.",
        "Multiplicar meu capital, mesmo com volatilidade alta.",
    ].index(q2)
    perfil["q3_idx"] = [
        "Menos de 2 anos.",
        "De 2 a 5 anos.",
        "Mais de 5 anos.",
    ].index(q3)
    perfil["q4_idx"] = [
        "Nenhuma. É minha primeira vez.",
        "Já investi um pouco antes.",
        "Tenho boa experiência e estudo o mercado.",
    ].index(q4)

    st.divider()

    if score <= 2:
        perfil_nome = "Conservador 🛡️"
        cor = "info"
        desc = (
            "Você prioriza segurança. Em ações, foque em **dividendos consistentes** "
            "(bancos, energia elétrica, saneamento) e **blue chips** (grandes empresas estabelecidas)."
        )
        sugestao_rv = 20
    elif score <= 5:
        perfil_nome = "Moderado ⚖️"
        cor = "success"
        desc = (
            "Você aceita alguma volatilidade pensando no longo prazo. "
            "Diversifique entre **blue chips** e algumas ações de **crescimento**."
        )
        sugestao_rv = 40
    else:
        perfil_nome = "Agressivo 🚀"
        cor = "warning"
        desc = (
            "Você está confortável com volatilidade e busca retorno alto. "
            "Pode incluir **small caps**, **tech** e **commodities** além das blue chips."
        )
        sugestao_rv = 60

    perfil["perfil_nome"] = perfil_nome
    perfil["score_perfil"] = score
    perfil["sugestao_rv_pct"] = sugestao_rv

    getattr(st, cor)(f"### Seu perfil: **{perfil_nome}** (score: {score}/8)\n\n{desc}")
    st.markdown(
        f"💡 **Sugestão de alocação:** **{sugestao_rv}%** em Renda Variável (ações) "
        f"e **{100 - sugestao_rv}%** em Renda Fixa (Tesouro, CDB)."
    )


# ========================================
# TAB 4 — Quanto Investir
# ========================================
with tabs[3]:
    st.header("💵 Quanto você pode investir?")
    st.markdown("Vamos descobrir um valor que NÃO vá atrapalhar suas contas.")

    col1, col2 = st.columns(2)
    with col1:
        renda_mensal = st.number_input(
            "Sua renda mensal líquida (R$):",
            min_value=0,
            value=perfil.get("renda_mensal", 5000),
            step=500,
        )
    with col2:
        pode_investir_mes = st.number_input(
            "Quanto sobra por mês para investir? (R$)",
            min_value=0,
            value=perfil.get("pode_investir_mes", 500),
            step=100,
            help="Depois de pagar tudo, quanto sobra livre por mês?",
        )

    valor_inicial = st.number_input(
        "Quanto você tem disponível AGORA para investir (além da reserva)? (R$)",
        min_value=0,
        value=perfil.get("valor_inicial", 1000),
        step=500,
    )

    perfil["renda_mensal"] = renda_mensal
    perfil["pode_investir_mes"] = pode_investir_mes
    perfil["valor_inicial"] = valor_inicial

    pct_renda = (pode_investir_mes / renda_mensal * 100) if renda_mensal > 0 else 0

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("% da renda investida/mês", fmt_pct(pct_renda, 1))
    col2.metric("Em 1 ano", fmt_brl(valor_inicial + pode_investir_mes * 12, 0))
    col3.metric("Em 5 anos (10% a.a.)", fmt_brl((valor_inicial + pode_investir_mes * 12 * 5) * 1.10, 0))

    if pct_renda > 30:
        st.warning("⚠️ Você está investindo mais de 30% da renda. Garanta que não vai apertar seu orçamento.")
    elif pct_renda < 5:
        st.info("💡 Investir 10-20% da renda é ideal. Se possível, considere aumentar gradualmente.")
    else:
        st.success("✅ Ótimo equilíbrio entre investir e viver o presente.")


# ========================================
# TAB 5 — Carteira Sugerida
# ========================================
with tabs[4]:
    st.header("📊 Sua Carteira Sugerida")

    if not perfil.get("perfil_nome"):
        st.warning("Complete os passos 1 a 4 primeiro.")
        st.stop()

    valor_total = perfil.get("valor_inicial", 1000)
    perc_rv = perfil.get("sugestao_rv_pct", 40)
    perc_rf = 100 - perc_rv

    valor_rv = valor_total * perc_rv / 100
    valor_rf = valor_total * perc_rf / 100

    st.markdown(f"### Perfil: **{perfil.get('perfil_nome')}**")
    st.markdown(f"### Investimento inicial: **{fmt_brl(valor_total)}**")

    col1, col2 = st.columns(2)
    col1.metric(
        f"🟢 Renda Fixa ({perc_rf}%)",
        fmt_brl(valor_rf),
        help="Tesouro Selic 2029 ou CDB 100% CDI.",
    )
    col2.metric(
        f"🟦 Renda Variável ({perc_rv}%)",
        fmt_brl(valor_rv),
        help="Ações diversificadas em pelo menos 5-8 papéis.",
    )

    st.divider()

    if perfil.get("score_perfil", 4) <= 2:
        carteira = {
            "ITUB4": ("Itaú — Banco sólido", 25),
            "BBAS3": ("Banco do Brasil — DY alto", 20),
            "TAEE11": ("Transmissora — Dividendos previsíveis", 20),
            "EGIE3": ("Engie — Energia elétrica", 15),
            "VIVT3": ("Telefônica — Telecom estável", 10),
            "BBSE3": ("BB Seguridade — Seguradora estável", 10),
        }
        titulo_carteira = "Carteira Conservadora — Foco em Dividendos"
    elif perfil.get("score_perfil", 4) <= 5:
        carteira = {
            "ITUB4": ("Itaú — Banco sólido", 15),
            "WEGE3": ("WEG — Indústria com crescimento", 15),
            "VALE3": ("Vale — Mineração global", 10),
            "PETR4": ("Petrobras — Petróleo + dividendos", 10),
            "BBAS3": ("Banco do Brasil", 10),
            "EGIE3": ("Engie — Energia", 10),
            "SUZB3": ("Suzano — Papel/celulose", 10),
            "TAEE11": ("Transmissora — Dividendos", 10),
            "BOVA11": ("ETF Ibovespa — Diversificação", 10),
        }
        titulo_carteira = "Carteira Moderada — Equilíbrio entre Crescimento e Dividendos"
    else:
        carteira = {
            "WEGE3": ("WEG — Crescimento global", 15),
            "TOTS3": ("Totvs — Tech B2B", 12),
            "VALE3": ("Vale — Mineração", 10),
            "PRIO3": ("PRIO — Petróleo independente", 10),
            "RDOR3": ("Rede D'Or — Saúde em crescimento", 10),
            "LREN3": ("Lojas Renner — Varejo", 8),
            "ITUB4": ("Itaú — Base estável", 10),
            "EMBR3": ("Embraer — Aviação", 10),
            "BOVA11": ("ETF Ibovespa — Diversificação", 8),
            "SMAL11": ("ETF Small Caps — Crescimento", 7),
        }
        titulo_carteira = "Carteira Agressiva — Foco em Crescimento"

    st.subheader(titulo_carteira)

    rows = []
    for ticker, (desc, peso) in carteira.items():
        valor = valor_rv * peso / 100
        rows.append({
            "Ticker": ticker,
            "Empresa": desc,
            "% da RV": f"{peso}%",
            "Valor a Investir": fmt_brl(valor),
        })

    import pandas as pd
    df_carteira = pd.DataFrame(rows)
    st.dataframe(df_carteira, width="stretch", hide_index=True)

    st.divider()

    st.markdown(f"""
### 📝 Plano de Ação

1. **Garanta a reserva de emergência primeiro** ({"✅ feito" if perfil.get("reserva_ok") else "🚨 prioridade!"})
2. **Abra conta numa corretora** (XP, Rico, NuInvest, Inter)
3. **Compre Tesouro Selic 2029** com {fmt_brl(valor_rf)}
4. **Compre cada ação da tabela acima** com os valores sugeridos
5. **Aporte mensalmente** {fmt_brl(perfil.get('pode_investir_mes', 0))}, mantendo a proporção
6. **Revise sua carteira a cada 3 meses** — não mexa toda hora!

### ⚠️ Regras de Ouro
- **Nunca** invista em ações dinheiro que você vai precisar em < 5 anos
- **Diversifique:** nunca > 25% em uma única ação
- **Não tente acertar o "timing"** — aporte regularmente
- **Ignore o ruído diário** — foque em fundamentos
- **Reinvista dividendos** sempre que possível
""")

    if st.button("💾 Salvar meu perfil", type="primary"):
        salvar_perfil(perfil)
        st.success("Perfil salvo! Sua próxima sessão vai abrir com seus dados.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Seu Status")
if perfil.get("perfil_nome"):
    st.sidebar.markdown(f"**Perfil:** {perfil['perfil_nome']}")
if perfil.get("reserva_ok"):
    st.sidebar.success("✅ Reserva OK")
elif perfil.get("despesa_mensal"):
    st.sidebar.error("🚨 Sem reserva")
if perfil.get("valor_inicial"):
    st.sidebar.markdown(f"**Investir:** {fmt_brl(perfil['valor_inicial'], 0)}")

st.caption("Este é um guia educacional. NÃO constitui recomendação profissional de investimento.")
