# Sistema de Analise Financeira de Acoes Brasileiras

## Visao Geral

Sistema que coleta, cruza e analisa dados financeiros de empresas listadas na B3 (Bolsa de Valores Brasileira) a partir de multiplas fontes publicas. O objetivo e identificar padroes como:

- Empresas com **prejuizo recorrente** ou deterioracao financeira
- Empresas com **fundamentos solidos** subvalorizadas pelo mercado
- **Divergencias** entre indicadores (ex: lucro contabil vs fluxo de caixa)
- **Tendencias macroeconomicas** que impactam setores especificos
- **Oportunidades de dividendos** consistentes
- **Sinais de alerta** (endividamento crescente, margens caindo, etc.)

---

## Fontes de Dados e APIs Publicas

### 1. CVM - Comissao de Valores Mobiliarios

**URL:** https://dados.cvm.gov.br

A CVM e o orgao regulador do mercado de capitais brasileiro. Seu portal de dados abertos e a **fonte mais rica e confiavel** para dados contabeis de empresas.

**Dados Disponiveis:**
- **DFP (Demonstracoes Financeiras Padronizadas)** - balanco anual completo
  - Balanco Patrimonial (Ativo, Passivo, Patrimonio Liquido)
  - Demonstracao de Resultado (DRE) - Receita, Custos, Lucro/Prejuizo
  - Demonstracao de Fluxo de Caixa (DFC)
  - Demonstracao de Valor Adicionado (DVA)
- **ITR (Informacoes Trimestrais)** - balanco trimestral
- **Cadastro de Companhias Abertas** - CNPJ, setor, situacao do registro
- **Formulario de Referencia** - informacoes detalhadas sobre governanca, riscos, remuneracao
- **Fatos Relevantes** - comunicados oficiais das empresas
- **Dados de Fundos de Investimento** - composicao de carteiras, cotas, patrimonio

**Formato:** CSV (download direto via URL)

**Endpoints principais:**
```
# DFP - Demonstracoes Financeiras Anuais
https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp

# ITR - Informacoes Trimestrais
https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr

# Cadastro de Companhias
https://dados.cvm.gov.br/dataset/cia_aberta-cad

# Formulario de Referencia
https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre

# Fatos Relevantes
https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre

# Fundos de Investimento
https://dados.cvm.gov.br/dataset/?groups=fundos
```

**Uso no projeto:** Fonte primaria para dados contabeis. Cruzar DFP + ITR para detectar prejuizos, endividamento, margens e evolucao patrimonial.

---

### 2. Banco Central do Brasil (BCB)

**URL:** https://dadosabertos.bcb.gov.br

O Banco Central disponibiliza dados macroeconomicos essenciais para contextualizar o desempenho das empresas.

**Dados Disponiveis:**
- **SGS (Sistema Gerenciador de Series Temporais)** - milhares de series economicas
  - Taxa SELIC (meta e efetiva)
  - IPCA (inflacao)
  - IGP-M
  - PIB
  - Producao industrial
  - Taxa de desemprego
- **PTAX** - cotacao oficial do dolar e outras moedas
- **Expectativas de Mercado (Focus)** - projecoes de economistas
- **Taxa de juros por instituicao financeira**
- **Dados do mercado imobiliario**
- **Indicadores de credito**

**Formato:** JSON via API REST (OData)

**Endpoints principais:**
```
# SGS - Series Temporais
https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json

# Series importantes:
# 432  = IPCA mensal
# 433  = IPCA acumulado 12 meses
# 4390 = Taxa SELIC meta
# 11   = Taxa SELIC efetiva
# 1    = Taxa de cambio (dolar)
# 4380 = PIB mensal
# 24363 = IPCA-15

# PTAX - Cotacao do dolar
https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/

# Expectativas Focus
https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/

# Taxa de juros bancaria
https://olinda.bcb.gov.br/olinda/servico/taxaJuros/versao/v2/odata/
```

**Bibliotecas Python:**
```
pip install python-bcb
```
```python
from bcb import sgs, PTAX, Expectativas

# Buscar SELIC
selic = sgs.get({"SELIC": 432}, start="2020-01-01")

# Buscar PTAX
ptax = PTAX().get_close("2024-01-01", "2024-12-31")

# Expectativas Focus
exp = Expectativas().get_endpoint("ExpectativasMercadoTop5Anuais")
```

**Uso no projeto:** Contextualizar resultados das empresas com cenario macro. Ex: empresa exportadora + dolar em alta = potencial beneficio. Setor de varejo + SELIC alta = pressao nos resultados.

---

### 3. B3 - Bolsa de Valores

**URL:** https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/

A B3 fornece dados de mercado: cotacoes, volumes, proventos e composicao de indices.

**Dados Disponiveis:**
- **Cotacoes Historicas** - OHLCV (abertura, maxima, minima, fechamento, volume)
- **Proventos** - dividendos, JCP, bonificacoes, desdobramentos, grupamentos
- **Composicao de Indices** - quais acoes compoem Ibovespa, IBrX, Small Caps, etc.
- **Dados de Derivativos** - opcoes, futuros
- **Aluguel de acoes (BTC)** - taxa de aluguel, quantidade disponivel
- **Emprestimo de acoes** - indicador de short selling

**Formato:** Arquivos TXT/CSV compactados (.zip)

**URLs de Download:**
```
# Cotacoes historicas diarias
https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_D{DDMMAAAA}.ZIP

# Cotacoes historicas anuais
https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{AAAA}.ZIP

# Proventos em dinheiro
https://bvmf.bmfbovespa.com.br/Cblc/CblcInvestidores/EventosCorporativos

# Composicao do Ibovespa (atualizada a cada 4 meses)
https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br
```

**Portal B3 for Developers:**
```
https://developers.b3.com.br/apis
```

**Uso no projeto:** Dados de preco e volume para calcular indicadores tecnicos. Proventos para calcular dividend yield real. Composicao de indices para filtrar universo de acoes.

---

### 4. brapi.dev - API Brasileira de Acoes

**URL:** https://brapi.dev

API REST dedicada ao mercado brasileiro. Agrega dados de diversas fontes em endpoints simples.

**Dados Disponiveis:**
- Cotacao em tempo real e historica
- Indicadores fundamentalistas (P/L, P/VP, ROE, ROA, ROIC, DY, etc.)
- Balanco patrimonial resumido
- DRE resumida
- Fluxo de caixa
- Dividendos historicos
- Logo das empresas
- FIIs (Fundos Imobiliarios)
- Criptomoedas e moedas
- Inflacao (IPCA, IGP-M)

**Formato:** JSON via API REST

**Endpoints principais:**
```
# Cotacao atual
GET https://brapi.dev/api/quote/{ticker}

# Cotacao historica
GET https://brapi.dev/api/quote/{ticker}?range=1y&interval=1d

# Dados fundamentalistas
GET https://brapi.dev/api/quote/{ticker}?fundamental=true

# Lista de acoes
GET https://brapi.dev/api/quote/list

# Dividendos
GET https://brapi.dev/api/quote/{ticker}?dividends=true

# Inflacao
GET https://brapi.dev/api/v2/inflation
```

**Autenticacao:** Token gratuito (limite de requisicoes no plano free)

**Uso no projeto:** Fonte rapida para indicadores fundamentalistas ja calculados. Ideal para prototipacao e validacao antes de calcular indicadores manualmente a partir dos dados da CVM.

---

### 5. Dados de Mercado

**URL:** https://www.dadosdemercado.com.br/api/docs

Plataforma brasileira que agrega dados de CVM, BCB, ANBIMA e B3 em uma API unificada.

**Dados Disponiveis:**
- Acoes: cotacoes, indicadores, dividendos, splits
- Fundos de investimento
- Tesouro Direto
- Indicadores macroeconomicos
- Setores e subsetores da B3

**Formato:** JSON via API REST

**Endpoints principais:**
```
# Cotacao de acao
GET https://api.dadosdemercado.com.br/v1/tickers/{ticker}

# Indicadores fundamentalistas
GET https://api.dadosdemercado.com.br/v1/tickers/{ticker}/indicators

# Historico de cotacoes
GET https://api.dadosdemercado.com.br/v1/tickers/{ticker}/prices

# Dividendos
GET https://api.dadosdemercado.com.br/v1/tickers/{ticker}/dividends

# Dados macroeconomicos
GET https://api.dadosdemercado.com.br/v1/economic-indicators
```

**Uso no projeto:** API complementar com dados ja consolidados. Boa para comparacoes rapidas entre empresas.

---

### 6. Yahoo Finance (via yfinance)

**URL:** https://pypi.org/project/yfinance/

Acesso gratuito a dados globais, incluindo acoes brasileiras (sufixo `.SA`).

**Dados Disponiveis:**
- Cotacoes historicas (OHLCV)
- Balanco patrimonial
- DRE
- Fluxo de caixa
- Informacoes da empresa (setor, industria, funcionarios)
- Recomendacoes de analistas
- Holders (maiores acionistas)
- Opcoes

**Formato:** Python (pandas DataFrames)

**Uso:**
```python
import yfinance as yf

# Ticker brasileiro = codigo + .SA
acao = yf.Ticker("PETR4.SA")

# Cotacoes historicas
hist = acao.history(period="5y")

# Demonstracao de resultado
dre = acao.financials

# Balanco patrimonial
balanco = acao.balance_sheet

# Fluxo de caixa
fluxo_caixa = acao.cashflow

# Dividendos
dividendos = acao.dividends

# Informacoes gerais
info = acao.info  # setor, P/L, market cap, etc.
```

**Limitacoes:** Dados fundamentais podem estar incompletos para acoes BR. API gratuita mas com rate limits.

**Uso no projeto:** Fonte secundaria para validacao cruzada. Util para dados de mercado (preco, volume) e como fallback.

---

### 7. ANBIMA

**URL:** https://developers.anbima.com.br / https://data.anbima.com.br

Associacao que regula fundos de investimento e renda fixa no Brasil.

**Dados Disponiveis:**
- **Fundos de investimento** - cotas, patrimonio, rentabilidade, composicao
- **Renda fixa** - curvas de juros, precos de titulos
- **Tesouro Direto** - precos e taxas
- **IMA (Indice de Mercado ANBIMA)** - benchmark de renda fixa
- **ETFs** - informacoes de fundos negociados em bolsa

**Formato:** JSON via API REST

**Endpoints:**
```
# Fundos
GET https://api.anbima.com.br/feed/fundos/v1/fundos/{codigoANBIMA}

# Curva de juros
GET https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/mercado-secundario-TPF
```

**Autenticacao:** Requer cadastro e aprovacao (OAuth 2.0)

**Uso no projeto:** Dados de fundos de investimento para cruzar com acoes (ex: quais fundos estao comprando/vendendo determinada acao). Curva de juros para valuation (DCF).

---

### 8. Fundamentus (Web Scraping)

**URL:** https://www.fundamentus.com.br

Site referencia para analise fundamentalista no Brasil. Nao possui API oficial, mas existem bibliotecas Python para scraping.

**Dados Disponiveis:**
- Todos os indicadores fundamentalistas (P/L, P/VP, PSR, DY, ROE, ROA, ROIC, etc.)
- Balanco patrimonial resumido
- DRE resumida
- Dados historicos de indicadores
- Screening/filtro de acoes

**Bibliotecas Python:**
```
pip install fundamentus
pip install pyfundamentus
```
```python
import fundamentus

# Dados de todas as acoes
df = fundamentus.get_resultado()

# Dados detalhados de uma acao
detalhes = fundamentus.get_papel("PETR4")
```

**Uso no projeto:** Screening rapido e indicadores pre-calculados para validacao.

---

### 9. HG Brasil Finance

**URL:** https://hgbrasil.com/finance

API brasileira com dados financeiros simplificados.

**Dados Disponiveis:**
- Cotacao de acoes da B3
- Ibovespa
- Dolar, Euro, Bitcoin
- Impostos (CDI, IPCA)

**Formato:** JSON

**Endpoint:**
```
GET https://api.hgbrasil.com/finance?key={API_KEY}
GET https://api.hgbrasil.com/finance/stock_price?key={API_KEY}&symbol=PETR4
```

**Uso no projeto:** Dados rapidos de cotacao e indicadores macro para dashboard.

---

### 10. Alpha Vantage

**URL:** https://www.alphavantage.co

API global com suporte a acoes brasileiras (sufixo `.SAO`).

**Dados Disponiveis:**
- Cotacoes historicas
- Indicadores tecnicos (SMA, EMA, RSI, MACD, Bollinger, etc.)
- Dados fundamentais (para empresas com cobertura)
- Forex e criptomoedas
- Dados economicos globais

**Formato:** JSON/CSV

**Endpoints:**
```
# Cotacao diaria
GET https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=PETR4.SAO&apikey={KEY}

# Indicador tecnico
GET https://www.alphavantage.co/query?function=RSI&symbol=PETR4.SAO&interval=daily&time_period=14&apikey={KEY}
```

**Uso no projeto:** Indicadores tecnicos pre-calculados para cruzar com dados fundamentalistas.

---

### 11. Tesouro Direto / Tesouro Transparente

**URL:** https://www.tesourotransparente.gov.br/

**Dados Disponiveis:**
- Precos e taxas de todos os titulos publicos
- Historico de vendas e resgates
- Estoque por titulo

**Formato:** CSV/Excel

**Uso no projeto:** Comparar retorno das acoes com renda fixa (Tesouro). Se o Tesouro paga mais que o dividend yield + valorizacao esperada, a acao pode nao ser atrativa.

---

### 12. IBGE - Dados Economicos

**URL:** https://servicodados.ibge.gov.br/api/docs

**Dados Disponiveis:**
- PIB por setor
- Inflacao (IPCA detalhado por grupo)
- Pesquisa Mensal do Comercio (PMC)
- Pesquisa Industrial Mensal (PIM)
- Producao agricola
- Dados demograficos

**Formato:** JSON

**Endpoints:**
```
# IPCA
GET https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/-6/variaveis/69?localidades=N1[all]

# PIB
GET https://servicodados.ibge.gov.br/api/v3/agregados/5932/periodos/-4/variaveis/6561?localidades=N1[all]
```

**Uso no projeto:** Dados setoriais para cruzar com desempenho de empresas do mesmo setor. Ex: producao industrial caindo + empresa industrial com queda de receita = tendencia confirmada.

---

## Estrategias de Cruzamento de Dados

### Cruzamento 1: Saude Financeira da Empresa
**Fontes:** CVM (DFP/ITR) + brapi + Fundamentus

| Verificacao | Dados | Fonte |
|---|---|---|
| Prejuizo recorrente | Lucro Liquido negativo por 2+ trimestres | CVM ITR |
| Endividamento perigoso | Divida Liquida / EBITDA > 3x | CVM DFP |
| Margem em queda | Margem Liquida trimestral decrescente | CVM ITR |
| Queimando caixa | Fluxo de Caixa Operacional negativo | CVM DFC |
| Receita estagnada | Receita sem crescimento real (descontada inflacao) | CVM + BCB (IPCA) |

**Alerta gerado:** "Empresa X apresenta prejuizo no ultimo trimestre, endividamento de 4.2x EBITDA e queima de caixa de R$ 500M."

---

### Cruzamento 2: Divergencia Lucro vs Caixa
**Fontes:** CVM (DRE + DFC)

Uma empresa pode ter lucro contabil positivo mas fluxo de caixa negativo (ou vice-versa). Isso pode indicar:
- Manipulacao contabil
- Investimentos pesados (positivo se bem direcionados)
- Problemas de recebimento

**Logica:**
```
SE lucro_liquido > 0 E fluxo_caixa_operacional < 0
   ENTAO alerta("Divergencia: lucro positivo mas caixa negativo")

SE lucro_liquido < 0 E fluxo_caixa_operacional > 0
   ENTAO alerta("Empresa operacionalmente saudavel apesar do prejuizo contabil")
```

---

### Cruzamento 3: Valuation vs Pares do Setor
**Fontes:** brapi/Fundamentus (indicadores) + CVM (setor) + B3 (cotacoes)

Comparar indicadores de uma empresa com a mediana do seu setor:

| Indicador | Empresa | Mediana Setor | Situacao |
|---|---|---|---|
| P/L | 5.2 | 12.8 | Subvalorizada? |
| P/VP | 0.7 | 1.5 | Abaixo do patrimonio |
| EV/EBITDA | 3.1 | 8.5 | Muito barata |
| DY | 12% | 4% | Alto dividendo |
| ROE | 25% | 15% | Eficiente |

**Score gerado:** Calcular um score de atratividade relativa ao setor.

---

### Cruzamento 4: Impacto Macro nos Setores
**Fontes:** BCB (SELIC, IPCA, Cambio) + CVM (resultados por setor) + IBGE (indicadores setoriais)

| Cenario Macro | Setor Beneficiado | Setor Prejudicado |
|---|---|---|
| SELIC subindo | Bancos, Seguradoras | Varejo, Construcao |
| Dolar subindo | Exportadoras (Papel, Mineracao, Agro) | Importadoras, Aereas |
| IPCA alto | Empresas com receita indexada | Consumo discricionario |
| PIB caindo | Utilities, Saude | Ciclicos, Luxo |

**Logica:**
```
SE selic_subindo E empresa.setor == "Varejo"
   ENTAO alerta("Pressao: SELIC em alta impacta custo de credito do setor")

SE dolar_subindo E empresa.receita_exterior > 50%
   ENTAO alerta("Potencial beneficio: receita em dolar com dolar valorizado")
```

---

### Cruzamento 5: Consistencia de Dividendos
**Fontes:** B3 (proventos) + CVM (lucro) + BCB (SELIC)

- Historico de pagamento (quantos anos consecutivos)
- Payout ratio (% do lucro distribuido)
- Dividend yield vs SELIC (atratividade relativa)
- Sustentabilidade (dividendo > lucro = insustentavel)

**Logica:**
```
SE dividend_yield > selic_atual E payout < 80% E lucro_crescente
   ENTAO classificar("Dividendo atrativo e sustentavel")

SE dividendo_pago > lucro_liquido
   ENTAO alerta("Dividendo insustentavel: paga mais do que lucra")
```

---

### Cruzamento 6: Sinais Tecnicos + Fundamentos
**Fontes:** Alpha Vantage/B3 (preco, volume) + CVM/brapi (fundamentos)

Combinar analise tecnica com fundamentalista:

- Acao barata (P/L baixo, P/VP < 1) + sinal tecnico de compra (RSI < 30, cruzamento de medias)
- Acao cara (P/L muito alto) + sinal tecnico de venda (RSI > 70, volume decrescente)
- Volume anomalo + fato relevante recente = possivel insider trading

---

### Cruzamento 7: Governanca e Risco
**Fontes:** CVM (Formulario de Referencia + Fatos Relevantes)

- Frequencia de fatos relevantes negativos
- Mudancas frequentes na diretoria
- Processos judiciais relevantes
- Transacoes com partes relacionadas
- Nivel de governanca corporativa (Novo Mercado, N1, N2, Tradicional)

---

### Cruzamento 8: Composicao de Fundos
**Fontes:** ANBIMA/CVM (carteiras de fundos) + B3 (cotacoes)

- Quais acoes os grandes fundos estao comprando/vendendo
- Concentracao: muitos fundos na mesma acao = risco de venda em massa
- Smart money: acompanhar movimentacoes de gestores renomados

---

## Indicadores e Metricas Calculaveis

### Indicadores de Rentabilidade
- **ROE** (Return on Equity) = Lucro Liquido / Patrimonio Liquido
- **ROA** (Return on Assets) = Lucro Liquido / Ativo Total
- **ROIC** (Return on Invested Capital) = NOPAT / Capital Investido
- **Margem Bruta** = Lucro Bruto / Receita Liquida
- **Margem EBITDA** = EBITDA / Receita Liquida
- **Margem Liquida** = Lucro Liquido / Receita Liquida

### Indicadores de Valuation
- **P/L** (Preco/Lucro) = Preco da Acao / LPA
- **P/VP** (Preco/Valor Patrimonial) = Preco / VPA
- **EV/EBITDA** = Enterprise Value / EBITDA
- **P/Receita (PSR)** = Market Cap / Receita Liquida
- **Earnings Yield** = LPA / Preco (inverso do P/L)

### Indicadores de Endividamento
- **Divida Liquida / EBITDA** - capacidade de pagar divida
- **Divida Liquida / Patrimonio Liquido** - alavancagem
- **Indice de Cobertura de Juros** = EBIT / Despesas Financeiras
- **Passivo Circulante / Ativo Circulante** - liquidez

### Indicadores de Dividendos
- **Dividend Yield** = Dividendos 12M / Preco
- **Payout** = Dividendos / Lucro Liquido
- **Dividend Yield vs SELIC** - atratividade relativa

### Indicadores de Crescimento
- **CAGR Receita** (3 e 5 anos)
- **CAGR Lucro** (3 e 5 anos)
- **CAGR Dividendos** (3 e 5 anos)

### Scores Compostos (calculados pelo sistema)
- **Score de Saude Financeira** (0-100) - baseado em margem, endividamento, caixa
- **Score de Valuation** (0-100) - quao barata/cara vs setor
- **Score de Dividendos** (0-100) - consistencia, yield, sustentabilidade
- **Score de Crescimento** (0-100) - evolucao de receita e lucro
- **Score de Risco** (0-100) - volatilidade, endividamento, governanca
- **Score Geral** (0-100) - media ponderada dos scores acima

---

## Arquitetura Sugerida

### Stack Tecnologica

```
Backend/Core:    Python 3.11+
Banco de Dados:  PostgreSQL (dados estruturados) + Redis (cache)
Coleta:          requests, aiohttp, beautifulsoup4, selenium
Processamento:   pandas, numpy, scipy
Visualizacao:    Streamlit ou Dash (dashboard web)
Agendamento:     APScheduler ou Celery
Testes:          pytest
```

### Dependencias Python Principais
```
pip install requests pandas numpy yfinance python-bcb fundamentus beautifulsoup4
pip install sqlalchemy psycopg2 redis aiohttp
pip install streamlit plotly scipy
pip install apscheduler python-dotenv
```

### Estrutura de Pastas Sugerida
```
mercado-financeiro/
|-- CLAUDE.md
|-- PROJETO.md
|-- README.md
|-- requirements.txt
|-- .env                          # API keys (brapi, alpha vantage, etc.)
|-- config/
|   |-- settings.py               # Configuracoes gerais
|   |-- api_config.py             # URLs e tokens das APIs
|-- src/
|   |-- collectors/               # Modulos de coleta de dados
|   |   |-- cvm_collector.py      # Coleta dados da CVM
|   |   |-- bcb_collector.py      # Coleta dados do Banco Central
|   |   |-- b3_collector.py       # Coleta dados da B3
|   |   |-- brapi_collector.py    # Coleta dados da brapi
|   |   |-- yahoo_collector.py    # Coleta dados do Yahoo Finance
|   |   |-- anbima_collector.py   # Coleta dados da ANBIMA
|   |   |-- ibge_collector.py     # Coleta dados do IBGE
|   |   |-- fundamentus_collector.py
|   |-- processors/               # Processamento e calculo
|   |   |-- financial_processor.py    # Calculos financeiros
|   |   |-- indicator_calculator.py   # Calcula indicadores
|   |   |-- cross_analyzer.py         # Cruzamentos de dados
|   |   |-- score_calculator.py       # Calcula scores compostos
|   |   |-- sector_analyzer.py        # Analise setorial
|   |-- models/                   # Modelos de dados
|   |   |-- company.py
|   |   |-- financial_statement.py
|   |   |-- indicator.py
|   |   |-- alert.py
|   |-- alerts/                   # Sistema de alertas
|   |   |-- alert_engine.py       # Motor de regras
|   |   |-- alert_rules.py        # Regras de alerta
|   |-- database/
|   |   |-- connection.py
|   |   |-- migrations/
|   |-- api/                      # API interna (opcional)
|   |   |-- routes.py
|-- dashboard/
|   |-- app.py                    # Streamlit app principal
|   |-- pages/
|   |   |-- overview.py           # Visao geral do mercado
|   |   |-- company_detail.py     # Detalhe de uma empresa
|   |   |-- sector_comparison.py  # Comparacao setorial
|   |   |-- alerts.py             # Painel de alertas
|   |   |-- screening.py          # Filtro/screening de acoes
|   |   |-- macro.py              # Indicadores macroeconomicos
|-- scripts/
|   |-- seed_database.py          # Popular banco inicial
|   |-- update_daily.py           # Atualizacao diaria
|   |-- update_quarterly.py       # Atualizacao trimestral (DFP/ITR)
|-- tests/
|   |-- test_collectors/
|   |-- test_processors/
|   |-- test_analyzers/
```

---

## Fases de Desenvolvimento

### Fase 1 - Fundacao (MVP)
**Objetivo:** Coletar dados basicos e exibir indicadores de uma empresa.

- [ ] Configurar projeto Python + banco PostgreSQL
- [ ] Implementar coletor da CVM (DFP e ITR)
- [ ] Implementar coletor da brapi (cotacoes + indicadores)
- [ ] Calcular indicadores basicos (P/L, P/VP, ROE, DY, Margem)
- [ ] Criar dashboard simples com Streamlit mostrando dados de 1 empresa
- [ ] Testes unitarios para coletores

### Fase 2 - Dados Macro + Multiplas Empresas
**Objetivo:** Contexto macroeconomico e comparacao entre empresas.

- [ ] Implementar coletor do BCB (SELIC, IPCA, PTAX)
- [ ] Implementar coletor do IBGE (PIB, producao)
- [ ] Coletar dados de todas as empresas do Ibovespa
- [ ] Classificar empresas por setor
- [ ] Criar pagina de comparacao setorial no dashboard
- [ ] Implementar cache com Redis

### Fase 3 - Cruzamentos e Alertas
**Objetivo:** Gerar insights automaticos a partir do cruzamento de dados.

- [ ] Implementar Cruzamento 1: Saude Financeira
- [ ] Implementar Cruzamento 2: Divergencia Lucro vs Caixa
- [ ] Implementar Cruzamento 3: Valuation vs Pares
- [ ] Implementar Cruzamento 4: Impacto Macro
- [ ] Implementar Cruzamento 5: Consistencia de Dividendos
- [ ] Criar motor de alertas com regras configuraveis
- [ ] Painel de alertas no dashboard

### Fase 4 - Analise Tecnica + Scoring
**Objetivo:** Combinar fundamentos com dados tecnicos e gerar scores.

- [ ] Implementar coletor de Alpha Vantage (indicadores tecnicos)
- [ ] Implementar Cruzamento 6: Tecnico + Fundamentalista
- [ ] Calcular scores compostos (Saude, Valuation, Dividendos, etc.)
- [ ] Criar ranking geral de acoes
- [ ] Criar pagina de screening com filtros avancados

### Fase 5 - Fundos + Governanca
**Objetivo:** Camada avancada de analise.

- [ ] Implementar coletor da ANBIMA (composicao de fundos)
- [ ] Implementar coletor da CVM (Formulario de Referencia)
- [ ] Implementar Cruzamento 7: Governanca e Risco
- [ ] Implementar Cruzamento 8: Composicao de Fundos
- [ ] Detectar movimentacoes atipicas de fundos

### Fase 6 - Automacao e Refinamento
**Objetivo:** Sistema rodando automaticamente com atualizacoes periodicas.

- [ ] Agendamento de coleta diaria (cotacoes, proventos)
- [ ] Agendamento de coleta trimestral (DFP/ITR)
- [ ] Notificacoes de alertas (email, Telegram)
- [ ] Backtest de estrategias baseadas nos scores
- [ ] Otimizacao de performance e qualidade dos dados
- [ ] Documentacao completa

---

## Notas Importantes

1. **Rate Limits:** Todas as APIs gratuitas tem limite de requisicoes. Implementar delays entre chamadas e cache agressivo.

2. **Dados Defasados:** Dados da CVM (DFP/ITR) tem atraso de semanas/meses. O sistema deve considerar a data de referencia dos dados.

3. **Qualidade dos Dados:** Sempre validar dados de multiplas fontes. Se brapi e CVM divergem, investigar.

4. **Nao e Recomendacao:** O sistema e uma ferramenta de analise. Nao constitui recomendacao de investimento.

5. **Armazenamento:** Dados historicos sao volumosos. Planejar estrategia de armazenamento e retencao.

6. **Legalidade:** Web scraping do Fundamentus e Status Invest deve respeitar robots.txt e termos de uso.
