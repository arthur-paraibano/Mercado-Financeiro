"""
Glossario centralizado de termos financeiros para tooltips e textos amigáveis.
Use `glossario.tip("PL")` em `help=` de st.metric, ou `glossario.explicar("PL")` em markdown.
"""

# Definicoes curtas (para tooltips em st.metric)
TIPS = {
    # --- Valuation ---
    "PL": "Preço / Lucro: quanto você paga por R$ 1 de lucro anual. < 10 = barato, 10-15 = justo, > 20 = caro.",
    "PVP": "Preço / Valor Patrimonial: quanto você paga em relacao ao patrimonio líquido. < 1 = abaixo do livro contábil.",
    "EV_EBITDA": "Valor da empresa / Geracao de caixa operacional. < 8 = atrativo.",
    "PRECO_JUSTO": "Estimativa do quanto a ação deveria valer com base nos fundamentos. Acima = barata, abaixo = cara.",
    "PRECO_TETO": "Preço máximo recomendado para compra (preço justo com margem de seguranca de 20%).",
    "UPSIDE": "Potencial de valorização ate o preço justo. Positivo = espaco para subir.",

    # --- Rentabilidade ---
    "ROE": "Return on Equity: lucro / patrimonio. Mede eficiencia. > 15% = excelente.",
    "ROIC": "Retorno sobre capital investido. Mede a qualidade do negocio. > 15% = forte.",
    "MARGEM_LIQUIDA": "% da receita que vira lucro líquido. > 10% = saudavel.",
    "MARGEM_EBITDA": "% da receita que vira caixa operacional. Importante para empresas com alto investimento.",

    # --- Dividendos ---
    "DY": "Dividend Yield: dividendos pagos no ano / cotação. > 5% = bom pagador. > 8% = atenção a sustentabilidade.",
    "PAYOUT": "% do lucro distribuido como dividendos. > 80% pode ser insustentavel a longo prazo.",
    "DIVIDENDO_CONSISTENTE": "Quantos anos seguidos a empresa pagou dividendos. > 10 anos = previsivel.",

    # --- Endividamento ---
    "DIVIDA_EBITDA": "Quantos anos de caixa operacional para quitar a dívida. < 2 = saudavel. > 4 = risco.",
    "LIQUIDEZ_CORRENTE": "Capacidade de pagar dívidas de curto prazo. > 1.5 = confortavel.",
    "DIVIDA_PL": "Dívida / Patrimonio. > 1 = empresa alavancada.",

    # --- Tecnico ---
    "RSI": "Índice de Forca Relativa (0-100). < 30 = sobrevendida (pode subir). > 70 = sobrecomprada (pode cair).",
    "MACD": "Mostra mudancas de tendencia. Cruzamento da linha do sinal indica compra/venda.",
    "MEDIA_MOVEL": "Média dos preços dos últimos N dias. Preço acima da média = tendencia de alta.",
    "BOLLINGER": "Bandas de volatilidade. Preço próximo da banda inferior pode ser bom momento de entrada.",

    # --- Outros ---
    "MARKET_CAP": "Valor de mercado da empresa = preço x quantidade de ações.",
    "LIQUIDEZ": "Volume medio de negociacao diaria. Alta = facil comprar e vender.",
    "VOLATILIDADE": "O quanto o preço oscila. Alta volatilidade = mais risco e mais oportunidade.",
    "SCORE_SAUDE": "Avalia se a empresa esta financeiramente saudavel (lucro, dívida, margens). 0-100.",
    "SCORE_VALUATION": "Avalia se a ação esta cara ou barata. 0-100.",
    "SCORE_DIVIDENDOS": "Avalia histórico e sustentabilidade dos dividendos. 0-100.",
    "SCORE_CRESCIMENTO": "Avalia se a empresa esta crescendo lucro e receita. 0-100.",
    "SCORE_TECNICO": "Avalia momentum do preço (médias moveis, RSI, MACD). 0-100.",
    "SCORE_GERAL": "Média ponderada de todos os scores. > 70 = excelente.",

    # --- Macro ---
    "SELIC": "Taxa básica de juros do Brasil. Define rendimento da renda fixa.",
    "CDI": "Taxa entre bancos. Quase igual a Selic. Base da maioria dos investimentos de renda fixa.",
    "IPCA": "Inflação oficial. Mostra perda de poder de compra. CDI > IPCA = você ganha dinheiro real.",
    "IBOVESPA": "Índice das ~80 ações mais negociadas da B3. Termometro do mercado.",
}

# Explicacoes longas em portugues simples (para expanders)
EXPLICACOES = {
    "PL": """
**P/L (Preço / Lucro)** mede quantos anos de lucro você esta pagando ao comprar a ação.

**Exemplo:** Se ITUB4 vale R$ 30 e teve R$ 3 de lucro por ação no ano, P/L = 10.
Isso significa que, mantendo o lucro atual, você levaria 10 anos para "recuperar" seu investimento.

- **Abaixo de 10** → geralmente barata
- **10 a 15** → preço justo
- **Acima de 20** → cara (so vale se o crescimento for muito alto)

⚠️ **Cuidado:** P/L sozinho engana. Empresas em crise tem P/L baixo. Compare com o setor.
""",

    "DY": """
**Dividend Yield (DY)** e quanto a empresa paga de dividendo em relacao ao preço da ação.

**Exemplo:** TAEE11 vale R$ 35 e pagou R$ 3 em dividendos no ano. DY = 8,5%.
Isso quer dizer que, além de eventual valorização, você recebe ~8,5% ao ano em dinheiro.

- **Abaixo de 3%** → empresa reinveste o lucro (foco em crescimento)
- **3% a 6%** → bom pagador
- **Acima de 6%** → pagador forte (energia, bancos, papel)
- **Acima de 10%** → 🚨 verifique se e sustentavel. As vezes a ação caiu muito e o DY ficou alto por isso.
""",

    "ROE": """
**ROE (Return on Equity)** mede quanto a empresa lucra em relacao ao patrimonio que tem.

E como saber se uma loja esta usando bem o capital dos socios.

**Exemplo:** Empresa com R$ 100 milhoes de patrimonio que lucra R$ 20 milhoes/ano tem ROE de 20%.

- **Acima de 15%** → empresa eficiente, gera muito retorno
- **5% a 15%** → mediana
- **Abaixo de 5%** → empresa pouco rentável

ROE alto e consistente por varios anos = sinal de empresa de qualidade.
""",

    "DIVIDA_EBITDA": """
**Dívida / EBITDA** mede em quantos anos a empresa quitaria toda a dívida usando seu caixa operacional.

E como o banco analisa se você consegue pagar o financiamento da casa: dívida vs sua renda.

- **Abaixo de 2x** → confortavel
- **2x a 3x** → atenção
- **Acima de 4x** → 🚨 risco elevado

Empresas como bancos tem regras diferentes (são alavancadas por natureza).
""",
}


def tip(termo: str) -> str:
    """Retorna a definicao curta para usar em help= de st.metric."""
    return TIPS.get(termo.upper(), "")


def explicar(termo: str) -> str:
    """Retorna explicação longa em markdown para usar em st.markdown ou st.expander."""
    return EXPLICACOES.get(termo.upper(), TIPS.get(termo.upper(), f"Termo '{termo}' não encontrado."))


# Criterios para selo "Amigável para Iniciantes"
CRITERIOS_INICIANTE = {
    "dy_minimo": 4.0,        # Paga dividendos relevantes
    "roe_minimo": 12.0,       # Rentabilidade comprovada
    "pl_minimo": 3.0,         # Evita P/L muito baixo (geralmente problema)
    "pl_maximo": 18.0,        # Nao esta supervalorizada
    "score_saude_minimo": 60, # Empresa saudavel
    "margem_liquida_minima": 5.0,  # Lucra de verdade
}


def avaliar_iniciante(indicadores: dict, scores: dict) -> tuple[bool, list[str]]:
    """
    Avalia se uma ação e adequada para iniciantes.
    Retorna (eh_amigavel, lista_de_motivos).
    """
    motivos = []
    pontos = 0
    total = 6

    dy = indicadores.get("dividend_yield", 0) or 0
    roe = indicadores.get("roe", 0) or 0
    pl = indicadores.get("pl", 0) or 0
    margem = indicadores.get("margem_liquida", 0) or 0
    saude = scores.get("saude", 0) or 0

    if dy >= CRITERIOS_INICIANTE["dy_minimo"]:
        motivos.append(f"✅ Paga dividendo relevante ({dy:.1f}%)")
        pontos += 1
    if roe >= CRITERIOS_INICIANTE["roe_minimo"]:
        motivos.append(f"✅ Empresa rentável (ROE {roe:.1f}%)")
        pontos += 1
    if CRITERIOS_INICIANTE["pl_minimo"] <= pl <= CRITERIOS_INICIANTE["pl_maximo"]:
        motivos.append(f"✅ Preço razoavel (P/L {pl:.1f})")
        pontos += 1
    if margem >= CRITERIOS_INICIANTE["margem_liquida_minima"]:
        motivos.append(f"✅ Lucra de verdade (margem {margem:.1f}%)")
        pontos += 1
    if saude >= CRITERIOS_INICIANTE["score_saude_minimo"]:
        motivos.append(f"✅ Saúde financeira boa (score {saude:.0f})")
        pontos += 1
    if pl > 0 and roe > 0:
        motivos.append("✅ Empresa lucrativa hoje (não tem prejuizo)")
        pontos += 1

    eh_amigavel = pontos >= 5  # 5 de 6 criterios
    return eh_amigavel, motivos
