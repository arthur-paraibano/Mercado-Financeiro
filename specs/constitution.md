# Mercado Financeiro BR - Constitution

## Core Principles

### I. Dados em Primeiro Lugar
Toda funcionalidade comeca pela coleta de dados confiaveis. Sempre que possivel, usar fontes oficiais (CVM, BCB, B3, IBGE). APIs de terceiros (brapi, Fundamentus) sao complementares e servem para validacao cruzada. Dados devem ser normalizados antes do uso.

### II. Multiplas Fontes, Uma Verdade
Nenhum indicador depende de uma unica fonte. O sistema cruza dados de diferentes APIs para validar informacoes. Divergencias entre fontes devem ser sinalizadas, nao ignoradas.

### III. Falhas Graciosamente
APIs externas sao instáveis. Todo coletor deve tratar timeouts, erros HTTP e dados ausentes sem crashar. Usar valores padrao razoaveis como fallback e informar o usuario quando dados estao indisponiveis.

### IV. Calculo Transparente
Todo score, indicador ou recomendacao deve ter sua formula documentada e rastreavel. O usuario deve poder entender como cada numero foi calculado. Nao existe "caixa preta".

### V. Nao e Recomendacao de Investimento
O sistema e uma ferramenta de analise. Toda tela de recomendacao deve conter aviso claro de que nao constitui aconselhamento financeiro profissional. Decisoes de investimento sao responsabilidade exclusiva do usuario.

### VI. Simplicidade e Iteracao
Preferir implementacoes simples que funcionam a arquiteturas complexas. Cada fase deve entregar valor independente. O sistema deve ser util desde a Fase 1.

### VII. Testes Obrigatorios
Todo processador de dados e calculadora deve ter testes unitarios. Coletores devem ter testes com mocks. Nenhuma logica de negocio entra sem cobertura de teste.

## Technical Standards

### Stack
- **Linguagem:** Python 3.12+
- **Dashboard:** Streamlit
- **Dados:** pandas, numpy
- **Graficos:** plotly
- **Testes:** pytest
- **Banco:** PostgreSQL (quando necessario)

### Convencoes
- Nomes de variaveis e funcoes em snake_case
- Docstrings em todas as classes e metodos publicos
- Logs com loguru
- Configuracoes via .env e config/settings.py
- Sem acentos em nomes de arquivos e variaveis

### Fontes de Dados
| Fonte | Tipo | Dados |
|---|---|---|
| CVM | Oficial | DFP, ITR, Fundos, Governanca |
| BCB | Oficial | SELIC, IPCA, PTAX, Focus |
| B3 | Oficial | Cotacoes, Ibovespa, Proventos |
| IBGE | Oficial | PIB, Producao, Comercio |
| brapi.dev | API | Cotacoes, Indicadores |
| Fundamentus | Scraping | Indicadores fundamentalistas |
| Yahoo Finance | API | Dividendos historicos |
