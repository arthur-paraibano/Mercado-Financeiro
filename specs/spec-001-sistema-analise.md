# SPEC-001: Sistema de Analise Financeira de Acoes Brasileiras

## Contexto
Sistema que coleta, cruza e analisa dados financeiros de empresas listadas na B3 a partir de multiplas fontes publicas. O objetivo e identificar padroes como empresas com prejuizo, oportunidades subvalorizadas, dividendos insustentaveis e impactos macroeconomicos nos setores.

## Comportamento Esperado

### Coleta de Dados
- O sistema coleta dados de 7+ fontes: CVM, BCB, B3, IBGE, brapi, Fundamentus, Yahoo Finance
- Cada coletor trata erros e timeouts graciosamente
- Dados sao normalizados para formato padrao (divisao por 100 do Fundamentus, sufixo .SA do Yahoo, etc.)
- Token da brapi e configurado via .env

### Cruzamentos de Dados
O sistema executa 5 cruzamentos automaticos:
1. **Saude Financeira:** Detecta prejuizo, endividamento critico, ROE negativo, liquidez baixa
2. **Divergencia Resultados:** Trimestre com prejuizo vs lucro anual, receita caindo, lucro extraordinario
3. **Valuation vs Setor:** Empresa cara ou barata comparada a mediana dos pares
4. **Impacto Macro:** SELIC e cambio pressionando ou beneficiando setores especificos
5. **Dividendos:** Payout insustentavel, DY abaixo da SELIC, DY muito alto

### Scores (0-100)
O sistema calcula 5 scores por dimensao + score geral:
- Saude Financeira (peso 30%)
- Valuation (peso 25%)
- Dividendos (peso 20%)
- Crescimento (peso 15%)
- Tecnico (peso 10%)

### Recomendacoes
O motor de recomendacoes gera sinais de compra baseados em:
- Score geral (combinacao dos 5 scores)
- Preco justo estimado (media de 4 metodos: Graham, Bazin, P/L justo, VPA x ROE)
- Preco teto (preco justo com 20% de margem de seguranca)
- Sinais tecnicos (RSI, MACD, Medias Moveis, Bollinger)

### Dashboard
10 paginas Streamlit:
1. Recomendacoes de Compra (sinal, preco teto, upside)
2. Analise de Empresa (indicadores + grafico + dividendos)
3. Visao Geral do Mercado (Ibovespa, setores)
4. Indicadores Macro (SELIC, IPCA, Dolar, PIB)
5. Comparacao Setorial (indicadores entre pares)
6. Painel de Alertas (cruzamentos automaticos)
7. Ranking por Score (tabela + radar)
8. Screening com Filtros (P/L, ROE, DY, etc.)
9. Analise de Fundos (Smart Money, concentracao)
10. Governanca Corporativa (nivel de listagem B3)

## Cenarios

### Cenario: Analise de empresa com prejuizo
**Dado** que MGLU3 tem lucro liquido negativo nos ultimos 12 meses
**Quando** o motor de alertas analisa MGLU3
**Entao** deve gerar alerta de severidade "CRITICO" ou "ALTO" do tipo "PREJUIZO_LIQUIDO"

### Cenario: Empresa subvalorizada vs setor
**Dado** que uma empresa tem P/L de 5x e a mediana do setor e 12x
**Quando** o cruzamento de valuation e executado
**Entao** deve gerar alerta "VALUATION_BARATO" de severidade "INFO"

### Cenario: Dividendo insustentavel
**Dado** que o payout estimado de uma empresa e 150%
**Quando** o cruzamento de dividendos e executado
**Entao** deve gerar alerta "DIVIDENDO_INSUSTENTAVEL" de severidade "ALTO"

### Cenario: Recomendacao de compra
**Dado** que uma empresa tem score >= 65, upside > 20% e sinais tecnicos de compra
**Quando** o motor de recomendacoes analisa a empresa
**Entao** deve classificar como "COMPRA FORTE"

### Cenario: API indisponivel
**Dado** que a API do BCB esta com timeout
**Quando** o sistema tenta buscar SELIC
**Entao** deve usar valor padrao (14.25%) e informar o usuario que dados estao indisponiveis

## Metricas de Sucesso
- 36+ testes unitarios passando
- Dashboard carrega em < 5 segundos (exceto busca de dados externos)
- Todos os 5 cruzamentos detectam alertas reais em empresas conhecidas
- Preco justo estimado dentro de +/- 30% do consenso de mercado
