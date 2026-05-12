"""
Script de uso unico: aplica acentuacao portuguesa em strings UI dos arquivos
de dashboard/pages e dashboard/components.

Aplica substituicoes APENAS dentro de strings Python (entre aspas) para
nao quebrar nomes de variaveis/funcoes.
"""
import re
from pathlib import Path

# Subs ordenadas: termos mais longos/especificos primeiro para evitar overlap
SUBS = [
    # Termos compostos primeiro
    ("Recomendacoes de Compra", "Recomendações de Compra"),
    ("Analise de Empresa", "Análise de Empresa"),
    ("Visao Geral", "Visão Geral"),
    ("Indicadores Macro", "Indicadores Macro"),
    ("Comparacao Setorial", "Comparação Setorial"),
    ("Mapa de Calor do Mercado", "Mapa de Calor do Mercado"),
    ("Calendario de Dividendos", "Calendário de Dividendos"),
    ("Calendario Economico", "Calendário Econômico"),
    ("Acoes vs Renda Fixa", "Ações vs Renda Fixa"),
    ("Analise Tecnica", "Análise Técnica"),
    ("Scanner de Sinais", "Scanner de Sinais"),
    ("Diario do Investidor", "Diário do Investidor"),
    ("Qual e Melhor", "Qual é Melhor"),
    # Palavras isoladas (com word boundaries)
    (r"\bRecomendacoes\b", "Recomendações"),
    (r"\brecomendacoes\b", "recomendações"),
    (r"\bRecomendacao\b", "Recomendação"),
    (r"\brecomendacao\b", "recomendação"),
    (r"\bAnalise\b", "Análise"),
    (r"\banalise\b", "análise"),
    (r"\bAnalises\b", "Análises"),
    (r"\banalises\b", "análises"),
    (r"\bAnalisar\b", "Analisar"),
    (r"\banalisar\b", "analisar"),
    (r"\bAnalisando\b", "Analisando"),
    (r"\banalisando\b", "analisando"),
    (r"\bAcoes\b", "Ações"),
    (r"\bacoes\b", "ações"),
    (r"\bAcao\b", "Ação"),
    (r"\bacao\b", "ação"),
    (r"\bComparacao\b", "Comparação"),
    (r"\bcomparacao\b", "comparação"),
    (r"\bGovernanca\b", "Governança"),
    (r"\bgovernanca\b", "governança"),
    (r"\bCalendario\b", "Calendário"),
    (r"\bcalendario\b", "calendário"),
    (r"\bEconomico\b", "Econômico"),
    (r"\beconomico\b", "econômico"),
    (r"\bEconomica\b", "Econômica"),
    (r"\beconomica\b", "econômica"),
    (r"\bEconomicos\b", "Econômicos"),
    (r"\beconomicos\b", "econômicos"),
    (r"\bNoticias\b", "Notícias"),
    (r"\bnoticias\b", "notícias"),
    (r"\bNoticia\b", "Notícia"),
    (r"\bnoticia\b", "notícia"),
    (r"\bVisao\b", "Visão"),
    (r"\bvisao\b", "visão"),
    (r"\bSecao\b", "Seção"),
    (r"\bsecao\b", "seção"),
    (r"\bSecoes\b", "Seções"),
    (r"\bsecoes\b", "seções"),
    (r"\bDiario\b", "Diário"),
    (r"\bdiario\b", "diário"),
    (r"\bDiarios\b", "Diários"),
    (r"\bdiarios\b", "diários"),
    (r"\bTecnica\b", "Técnica"),
    (r"\btecnica\b", "técnica"),
    (r"\bTecnicas\b", "Técnicas"),
    (r"\btecnicas\b", "técnicas"),
    (r"\bTecnico\b", "Técnico"),
    (r"\btecnico\b", "técnico"),
    (r"\bTecnicos\b", "Técnicos"),
    (r"\btecnicos\b", "técnicos"),
    (r"\bIndice\b", "Índice"),
    (r"\bindice\b", "índice"),
    (r"\bIndices\b", "Índices"),
    (r"\bindices\b", "índices"),
    (r"\bPreco\b", "Preço"),
    (r"\bpreco\b", "preço"),
    (r"\bPrecos\b", "Preços"),
    (r"\bprecos\b", "preços"),
    (r"\bCotacao\b", "Cotação"),
    (r"\bcotacao\b", "cotação"),
    (r"\bCotacoes\b", "Cotações"),
    (r"\bcotacoes\b", "cotações"),
    (r"\bConfiguracao\b", "Configuração"),
    (r"\bconfiguracao\b", "configuração"),
    (r"\bOpcao\b", "Opção"),
    (r"\bopcao\b", "opção"),
    (r"\bOpcoes\b", "Opções"),
    (r"\bopcoes\b", "opções"),
    (r"\bAtualizacao\b", "Atualização"),
    (r"\batualizacao\b", "atualização"),
    (r"\bAtualizar\b", "Atualizar"),
    (r"\batualizar\b", "atualizar"),
    (r"\bVariacao\b", "Variação"),
    (r"\bvariacao\b", "variação"),
    (r"\bVariacoes\b", "Variações"),
    (r"\bvariacoes\b", "variações"),
    (r"\bValorizacao\b", "Valorização"),
    (r"\bvalorizacao\b", "valorização"),
    (r"\bSaude\b", "Saúde"),
    (r"\bsaude\b", "saúde"),
    (r"\bDecisao\b", "Decisão"),
    (r"\bdecisao\b", "decisão"),
    (r"\bDecisoes\b", "Decisões"),
    (r"\bdecisoes\b", "decisões"),
    (r"\bDimensao\b", "Dimensão"),
    (r"\bdimensao\b", "dimensão"),
    (r"\bDimensoes\b", "Dimensões"),
    (r"\bdimensoes\b", "dimensões"),
    (r"\bExplicacao\b", "Explicação"),
    (r"\bexplicacao\b", "explicação"),
    (r"\bExplicacoes\b", "Explicações"),
    (r"\bexplicacoes\b", "explicações"),
    (r"\bSugestao\b", "Sugestão"),
    (r"\bsugestao\b", "sugestão"),
    (r"\bSugestoes\b", "Sugestões"),
    (r"\bsugestoes\b", "sugestões"),
    (r"\bInformacao\b", "Informação"),
    (r"\binformacao\b", "informação"),
    (r"\bInformacoes\b", "Informações"),
    (r"\binformacoes\b", "informações"),
    (r"\bSelecao\b", "Seleção"),
    (r"\bselecao\b", "seleção"),
    (r"\bSimulacao\b", "Simulação"),
    (r"\bsimulacao\b", "simulação"),
    (r"\bSituacao\b", "Situação"),
    (r"\bsituacao\b", "situação"),
    (r"\bAtencao\b", "Atenção"),
    (r"\batencao\b", "atenção"),
    (r"\bDistribuicao\b", "Distribuição"),
    (r"\bdistribuicao\b", "distribuição"),
    (r"\bDescricao\b", "Descrição"),
    (r"\bdescricao\b", "descrição"),
    (r"\bReducao\b", "Redução"),
    (r"\breducao\b", "redução"),
    (r"\bExpansao\b", "Expansão"),
    (r"\bexpansao\b", "expansão"),
    (r"\bDivida\b", "Dívida"),
    (r"\bdivida\b", "dívida"),
    (r"\bDividas\b", "Dívidas"),
    (r"\bdividas\b", "dívidas"),
    (r"\bnao\b", "não"),
    (r"\bNao\b", "Não"),
    (r"\bvoce\b", "você"),
    (r"\bVoce\b", "Você"),
    (r"\bestao\b", "estão"),
    (r"\bEstao\b", "Estão"),
    (r"\bsao\b", "são"),
    (r"\bSao\b", "São"),
    (r"\bja\b", "já"),
    (r"\bJa\b", "Já"),
    (r"\bproprio\b", "próprio"),
    (r"\bproprios\b", "próprios"),
    (r"\bProprio\b", "Próprio"),
    (r"\bProprios\b", "Próprios"),
    (r"\bproxima\b", "próxima"),
    (r"\bproximo\b", "próximo"),
    (r"\bproximos\b", "próximos"),
    (r"\bproximas\b", "próximas"),
    (r"\bProxima\b", "Próxima"),
    (r"\bProximo\b", "Próximo"),
    (r"\bProximos\b", "Próximos"),
    (r"\bProximas\b", "Próximas"),
    (r"\butil\b", "útil"),
    (r"\bUtil\b", "Útil"),
    (r"\bUteis\b", "Úteis"),
    (r"\buteis\b", "úteis"),
    (r"\bUltima\b", "Última"),
    (r"\bultima\b", "última"),
    (r"\bUltimas\b", "Últimas"),
    (r"\bultimas\b", "últimas"),
    (r"\bUltimo\b", "Último"),
    (r"\bultimo\b", "último"),
    (r"\bUltimos\b", "Últimos"),
    (r"\bultimos\b", "últimos"),
    (r"\bMetrica\b", "Métrica"),
    (r"\bmetrica\b", "métrica"),
    (r"\bMetricas\b", "Métricas"),
    (r"\bmetricas\b", "métricas"),
    (r"\bperiodo\b", "período"),
    (r"\bPeriodo\b", "Período"),
    (r"\bperiodos\b", "períodos"),
    (r"\bPeriodos\b", "Períodos"),
    (r"\bMedia\b", "Média"),
    (r"\bmedia\b", "média"),
    (r"\bMedias\b", "Médias"),
    (r"\bmedias\b", "médias"),
    (r"\bGrafico\b", "Gráfico"),
    (r"\bgrafico\b", "gráfico"),
    (r"\bGraficos\b", "Gráficos"),
    (r"\bgraficos\b", "gráficos"),
    (r"\bMaximo\b", "Máximo"),
    (r"\bmaximo\b", "máximo"),
    (r"\bMinimo\b", "Mínimo"),
    (r"\bminimo\b", "mínimo"),
    (r"\bMaxima\b", "Máxima"),
    (r"\bmaxima\b", "máxima"),
    (r"\bMinima\b", "Mínima"),
    (r"\bminima\b", "mínima"),
    (r"\bMaximas\b", "Máximas"),
    (r"\bmaximas\b", "máximas"),
    (r"\bMinimas\b", "Mínimas"),
    (r"\bminimas\b", "mínimas"),
    (r"\bRapido\b", "Rápido"),
    (r"\brapido\b", "rápido"),
    (r"\bRapida\b", "Rápida"),
    (r"\brapida\b", "rápida"),
    (r"\bCalculo\b", "Cálculo"),
    (r"\bcalculo\b", "cálculo"),
    (r"\bCalculos\b", "Cálculos"),
    (r"\bcalculos\b", "cálculos"),
    (r"\bSerie\b", "Série"),
    (r"\bserie\b", "série"),
    (r"\bSeries\b", "Séries"),
    (r"\bseries\b", "séries"),
    (r"\bConcluido\b", "Concluído"),
    (r"\bconcluido\b", "concluído"),
    (r"\bMes\b", "Mês"),
    (r"\bComecar\b", "Começar"),
    (r"\bcomecar\b", "começar"),
    (r"\bComecou\b", "Começou"),
    (r"\bcomecou\b", "começou"),
    (r"\bComeco\b", "Começo"),
    (r"\bcomeco\b", "começo"),
    (r"\bcomeca\b", "começa"),
    (r"\bComeca\b", "Começa"),
    (r"\bDivisao\b", "Divisão"),
    (r"\bdivisao\b", "divisão"),
    (r"\bAvaliacao\b", "Avaliação"),
    (r"\bavaliacao\b", "avaliação"),
    (r"\bavaliar\b", "avaliar"),
    (r"\bImovel\b", "Imóvel"),
    (r"\bimovel\b", "imóvel"),
    (r"\bImoveis\b", "Imóveis"),
    (r"\bimoveis\b", "imóveis"),
    (r"\bbasico\b", "básico"),
    (r"\bBasico\b", "Básico"),
    (r"\bbasica\b", "básica"),
    (r"\bBasica\b", "Básica"),
    (r"\bbasicas\b", "básicas"),
    (r"\bClassificacao\b", "Classificação"),
    (r"\bclassificacao\b", "classificação"),
    (r"\bcriterio\b", "critério"),
    (r"\bCriterio\b", "Critério"),
    (r"\bcriterios\b", "critérios"),
    (r"\bCriterios\b", "Critérios"),
    (r"\bhistorico\b", "histórico"),
    (r"\bHistorico\b", "Histórico"),
    (r"\bhistoricos\b", "históricos"),
    (r"\bHistoricos\b", "Históricos"),
    (r"\bExtensao\b", "Extensão"),
    (r"\bextensao\b", "extensão"),
    (r"\bemergencia\b", "emergência"),
    (r"\bEmergencia\b", "Emergência"),
    (r"\bexperiencia\b", "experiência"),
    (r"\bExperiencia\b", "Experiência"),
    (r"\bestrategia\b", "estratégia"),
    (r"\bEstrategia\b", "Estratégia"),
    (r"\bvolatilidade\b", "volatilidade"),  # ja correto
    (r"\bsolido\b", "sólido"),
    (r"\bSolido\b", "Sólido"),
    (r"\bsolida\b", "sólida"),
    (r"\bSolida\b", "Sólida"),
    (r"\bsolidos\b", "sólidos"),
    (r"\bSolidos\b", "Sólidos"),
    (r"\bsolidas\b", "sólidas"),
    (r"\bSolidas\b", "Sólidas"),
    (r"\bdetalhe\b", "detalhe"),  # ja correto
    (r"\bAmigavel\b", "Amigável"),
    (r"\bamigavel\b", "amigável"),
    (r"\bAmigaveis\b", "Amigáveis"),
    (r"\bamigaveis\b", "amigáveis"),
    (r"\bRentavel\b", "Rentável"),
    (r"\brentavel\b", "rentável"),
    (r"\bRentaveis\b", "Rentáveis"),
    (r"\brentaveis\b", "rentáveis"),
    (r"\bPossivel\b", "Possível"),
    (r"\bpossivel\b", "possível"),
    (r"\bPossiveis\b", "Possíveis"),
    (r"\bpossiveis\b", "possíveis"),
    (r"\bImpossivel\b", "Impossível"),
    (r"\bimpossivel\b", "impossível"),
    (r"\bdisponivel\b", "disponível"),
    (r"\bDisponivel\b", "Disponível"),
    (r"\bdisponiveis\b", "disponíveis"),
    (r"\bDisponiveis\b", "Disponíveis"),
    (r"\bestavel\b", "estável"),
    (r"\bEstavel\b", "Estável"),
    (r"\bestaveis\b", "estáveis"),
    (r"\bEstaveis\b", "Estáveis"),
    (r"\bresponsavel\b", "responsável"),
    (r"\bResponsavel\b", "Responsável"),
    (r"\bagressivo\b", "agressivo"),  # ja correto
    (r"\bconservador\b", "conservador"),  # ja correto
    (r"\bbarata\b", "barata"),  # ja correto
    (r"\bcara\b", "cara"),  # ja correto
    (r"\borcamento\b", "orçamento"),
    (r"\bOrcamento\b", "Orçamento"),
    (r"\baco\b", "aço"),  # cuidado: pode aparecer em ticker, mas em strings raro
    (r"\bAco\b", "Aço"),
    (r"\bperguntar\b", "perguntar"),  # ja correto
    (r"\bvale\b", "vale"),  # ja correto
    (r"\bAviso\b", "Aviso"),  # ja correto
    (r"\bAtraves\b", "Através"),
    (r"\batraves\b", "através"),
    (r"\bAlem\b", "Além"),
    (r"\balem\b", "além"),
    (r"\bResumo\b", "Resumo"),  # ja correto
    (r"\bOlha\b", "Olha"),  # ja correto
    (r"\bEletrica\b", "Elétrica"),
    (r"\beletrica\b", "elétrica"),
    (r"\bEletricas\b", "Elétricas"),
    (r"\beletricas\b", "elétricas"),
    (r"\bEletrico\b", "Elétrico"),
    (r"\beletrico\b", "elétrico"),
    (r"\bTelefonica\b", "Telefônica"),
    (r"\btelefonica\b", "telefônica"),
    (r"\bIndustria\b", "Indústria"),
    (r"\bindustria\b", "indústria"),
    (r"\bIndustrias\b", "Indústrias"),
    (r"\bindustrias\b", "indústrias"),
    (r"\bMineracao\b", "Mineração"),
    (r"\bmineracao\b", "mineração"),
    (r"\bAviacao\b", "Aviação"),
    (r"\baviacao\b", "aviação"),
    (r"\bPetroleo\b", "Petróleo"),
    (r"\bpetroleo\b", "petróleo"),
    (r"\bsiderurgia\b", "siderurgia"),  # ja correto
    (r"\bsegurador\b", "segurador"),  # ja correto
    (r"\binflacao\b", "inflação"),
    (r"\bInflacao\b", "Inflação"),
    (r"\bAlocacao\b", "Alocação"),
    (r"\balocacao\b", "alocação"),
    (r"\bIntegracao\b", "Integração"),
    (r"\bintegracao\b", "integração"),
    (r"\bRegulamentacao\b", "Regulamentação"),
    (r"\bregulamentacao\b", "regulamentação"),
    (r"\bResponsabilidade\b", "Responsabilidade"),  # ja correto
    (r"\bMargens\b", "Margens"),  # ja correto
    (r"\bMargem\b", "Margem"),  # ja correto
    (r"\bMargem Liq\b", "Margem Líq."),
    (r"\bMargem Liquida\b", "Margem Líquida"),
    (r"\bmargem liquida\b", "margem líquida"),
    (r"\bliquida\b", "líquida"),
    (r"\bLiquida\b", "Líquida"),
    (r"\bliquido\b", "líquido"),
    (r"\bLiquido\b", "Líquido"),
    (r"\bliquidez\b", "liquidez"),  # ja correto
    (r"\bLiquidez\b", "Liquidez"),  # ja correto
    (r"\bDividendo\b", "Dividendo"),  # ja correto
    (r"\bDividendos\b", "Dividendos"),  # ja correto
    (r"\bGanho\b", "Ganho"),  # ja correto
    (r"\bcarteira\b", "carteira"),  # ja correto
    (r"\bbrasil\b", "Brasil"),
    (r"\bBrasil\b", "Brasil"),  # ja correto
    (r"\bbrasileiro\b", "brasileiro"),  # ja correto
    (r"\bbrasileira\b", "brasileira"),  # ja correto
    (r"\bestudo\b", "estudo"),  # ja correto
    (r"\bEstudo\b", "Estudo"),  # ja correto
    (r"\bDicas\b", "Dicas"),  # ja correto
    (r"\bDica\b", "Dica"),  # ja correto
    (r"\bcorretora\b", "corretora"),  # ja correto
    (r"\bregra\b", "regra"),  # ja correto
    (r"\bbasta\b", "basta"),  # ja correto
    (r"\bMaior\b", "Maior"),  # ja correto
    (r"\bcaixa\b", "caixa"),  # ja correto
    (r"\bConcentracao\b", "Concentração"),
    (r"\bconcentracao\b", "concentração"),
    (r"\bDiversificacao\b", "Diversificação"),
    (r"\bdiversificacao\b", "diversificação"),
    (r"\bvocabulo\b", "vocabulo"),  # ja correto
    (r"\binicial\b", "inicial"),  # ja correto
    (r"\bidealmente\b", "idealmente"),  # ja correto
    (r"\bdivulgado\b", "divulgado"),  # ja correto
    (r"\bsofre\b", "sofre"),  # ja correto
    (r"\bExibir\b", "Exibir"),  # ja correto
    (r"\bExcluir\b", "Excluir"),  # ja correto
    (r"\bSalvar\b", "Salvar"),  # ja correto
    (r"\bRemover\b", "Remover"),  # ja correto
    (r"\bAdicionar\b", "Adicionar"),  # ja correto
    (r"\bComparar\b", "Comparar"),  # ja correto
    (r"\bResponder\b", "Responder"),  # ja correto
    (r"\bPergunta\b", "Pergunta"),  # ja correto
    (r"\bResposta\b", "Resposta"),  # ja correto
    (r"\bregular\b", "regular"),  # ja correto
    (r"\bcoluna\b", "coluna"),  # ja correto
    (r"\btopo\b", "topo"),  # ja correto
    (r"\bRecente\b", "Recente"),  # ja correto
    (r"\bRecentes\b", "Recentes"),  # ja correto
    (r"\bDado\b", "Dado"),  # ja correto
    (r"\bDados\b", "Dados"),  # ja correto
    (r"\bPais\b", "País"),
    (r"\bpais\b", "país"),
    (r"\bPaises\b", "Países"),
    (r"\bpaises\b", "países"),
    (r"\bquimica\b", "química"),
    (r"\bQuimica\b", "Química"),
    (r"\beletronica\b", "eletrônica"),
    (r"\bEletronica\b", "Eletrônica"),
    (r"\bautomatica\b", "automática"),
    (r"\bAutomatica\b", "Automática"),
    (r"\bautomatico\b", "automático"),
    (r"\bAutomatico\b", "Automático"),
    (r"\bdomestica\b", "doméstica"),
    (r"\bDomestica\b", "Doméstica"),
    (r"\binvestimento\b", "investimento"),  # ja correto
    (r"\bExemplo\b", "Exemplo"),  # ja correto
    (r"\bSimples\b", "Simples"),  # ja correto
    (r"\bcredito\b", "crédito"),
    (r"\bCredito\b", "Crédito"),
    (r"\bdebito\b", "débito"),
    (r"\bDebito\b", "Débito"),
    (r"\bnumero\b", "número"),
    (r"\bNumero\b", "Número"),
    (r"\bnumeros\b", "números"),
    (r"\bNumeros\b", "Números"),
    (r"\bprojecao\b", "projeção"),
    (r"\bProjecao\b", "Projeção"),
    (r"\bprojecoes\b", "projeções"),
    (r"\bProjecoes\b", "Projeções"),
    (r"\bDecimal\b", "Decimal"),  # ja correto
    (r"\bcomum\b", "comum"),  # ja correto
    (r"\bdistante\b", "distante"),  # ja correto
    (r"\bRespostas\b", "Respostas"),  # ja correto
    (r"\bsetor concentrado\b", "setor concentrado"),  # ja correto
    (r"\bExportar\b", "Exportar"),  # ja correto
    (r"\bConcorrente\b", "Concorrente"),  # ja correto
    (r"\bConcorrentes\b", "Concorrentes"),  # ja correto
    (r"\bnenhum\b", "nenhum"),  # ja correto
    (r"\bestrutura\b", "estrutura"),  # ja correto
    (r"\bpensando\b", "pensando"),  # ja correto
    (r"\bResolucao\b", "Resolução"),
    (r"\bresolucao\b", "resolução"),
    (r"\baberta\b", "aberta"),  # ja correto
    (r"\bestresse\b", "estresse"),  # ja correto
    # Casos com mais contexto/composicao
    (r"\bAcima\b", "Acima"),  # ja correto
    (r"\bAbaixo\b", "Abaixo"),  # ja correto
    (r"\bAbaixo do teto\b", "Abaixo do teto"),  # ja correto
    (r"\bAcima do teto\b", "Acima do teto"),  # ja correto
    (r"\bcontabil\b", "contábil"),
    (r"\bContabil\b", "Contábil"),
]

# String literal regex (3 quote styles, no multiline triple-quote handling)
PATTERN_DOUBLE = re.compile(r'"((?:[^"\\]|\\.)*)"')
PATTERN_SINGLE = re.compile(r"'((?:[^'\\]|\\.)*)'")


def aplicar_subs(texto: str) -> str:
    for pat, repl in SUBS:
        if pat.startswith("\\b") or pat.endswith("\\b"):
            texto = re.sub(pat, repl, texto)
        else:
            texto = texto.replace(pat, repl)
    return texto


def transformar_string(match):
    interior = match.group(1)
    novo = aplicar_subs(interior)
    if novo == interior:
        return match.group(0)
    delim = match.group(0)[0]
    return f"{delim}{novo}{delim}"


def processar_arquivo(path: Path):
    txt = path.read_text(encoding="utf-8")
    novo = PATTERN_DOUBLE.sub(transformar_string, txt)
    novo = PATTERN_SINGLE.sub(transformar_string, novo)
    if novo != txt:
        path.write_text(novo, encoding="utf-8")
        return True
    return False


targets = list(Path("dashboard/pages").glob("*.py")) + list(Path("dashboard/components").glob("*.py"))
total = 0
for path in targets:
    if processar_arquivo(path):
        total += 1
        print(f"Atualizado: {path}")
print(f"\nTotal: {total} arquivos atualizados")
