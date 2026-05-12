# Tasks: Mercado Financeiro BR - Implementacoes Futuras

**Input**: Design documents from `specs/`
**Prerequisites**: plan.md, spec-001-sistema-analise.md, constitution.md
**Status**: Fases 1-5 completas, tarefas abaixo sao para evolucao futura

---

## Phase 1: Persistencia e Banco de Dados (Prioridade: P1)

**Goal**: Salvar dados no PostgreSQL para nao depender de chamadas a API a cada acesso

**Independent Test**: Dados devem ser salvos e recuperados do banco sem chamar APIs externas

- [ ] T001 [US1] Ativar PostgreSQL e rodar schema.sql em `src/database/schema.sql`
- [ ] T002 [US1] Implementar repositorio de empresas em `src/database/empresa_repo.py`
- [ ] T003 [P] [US1] Implementar repositorio de cotacoes em `src/database/cotacao_repo.py`
- [ ] T004 [P] [US1] Implementar repositorio de indicadores em `src/database/indicador_repo.py`
- [ ] T005 [US1] Implementar repositorio de alertas em `src/database/alerta_repo.py`
- [ ] T006 [US1] Criar script de carga inicial `scripts/seed_database.py` que popula banco com todas as empresas do Ibovespa
- [ ] T007 [US1] Adaptar dashboard para ler do banco quando disponivel (fallback para API)
- [ ] T008 [US1] Testes de integracao com banco em `tests/test_database/`

**Checkpoint**: Dashboard funciona com dados do banco, sem precisar chamar API a cada reload

---

## Phase 2: Automacao e Agendamento (Prioridade: P1)

**Goal**: Sistema roda sozinho, atualizando dados periodicamente

- [ ] T009 [US2] Instalar APScheduler: `pip install apscheduler`
- [ ] T010 [US2] Criar agendador em `src/scheduler/jobs.py`
- [ ] T011 [US2] Job diario (18h30 dias uteis): atualizar cotacoes e indicadores de todas as empresas do Ibovespa
- [ ] T012 [US2] Job semanal (segunda 7h): atualizar dados macro BCB/IBGE
- [ ] T013 [US2] Job mensal (dia 20): baixar carteiras de fundos CVM
- [ ] T014 [US2] Job diario: executar cruzamentos e salvar alertas novos no banco
- [ ] T015 [US2] Criar pagina de Status no dashboard `dashboard/pages/10_Status.py` mostrando jobs e proximas execucoes
- [ ] T016 [US2] Logging estruturado de cada execucao em `logs/`

**Checkpoint**: `python src/scheduler/jobs.py` inicia e executa jobs no horario correto

---

## Phase 3: Notificacoes (Prioridade: P2)

**Goal**: Receber alertas criticos automaticamente sem abrir o dashboard

- [ ] T017 [US3] Criar bot Telegram com @BotFather
- [ ] T018 [US3] Implementar notificador Telegram em `src/notifications/telegram_notifier.py`
- [ ] T019 [P] [US3] Implementar notificador Email em `src/notifications/email_notifier.py`
- [ ] T020 [US3] Integrar notificacoes no job diario: enviar resumo do mercado + alertas criticos
- [ ] T021 [US3] Implementar resumo semanal com top 5 melhores e piores acoes da semana
- [ ] T022 [US3] Configuracao no .env: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `EMAIL_*`
- [ ] T023 [US3] Testes com mock do envio em `tests/test_notifications/`

**Checkpoint**: Mensagem de teste chega no Telegram com resumo do mercado

---

## Phase 4: Historico de Recomendacoes e Backtest (Prioridade: P2)

**Goal**: Rastrear se as recomendacoes anteriores se concretizaram

- [ ] T024 [US4] Criar tabela `recomendacoes_historico` no banco com: ticker, data, sinal, preco_na_data, preco_justo, preco_teto
- [ ] T025 [US4] Job semanal: salvar snapshot das recomendacoes atuais
- [ ] T026 [US4] Criar pagina `dashboard/pages/11_Historico.py` com evolucao das recomendacoes ao longo do tempo
- [ ] T027 [US4] Calcular acuracia: quantas recomendacoes de "COMPRA" realmente subiram em 1/3/6 meses
- [ ] T028 [US4] Implementar backtester em `src/backtest/backtester.py` com 3 estrategias (valor, dividendos, qualidade)
- [ ] T029 [US4] Criar pagina `dashboard/pages/12_Backtest.py` com grafico de evolucao do capital simulado
- [ ] T030 [US4] Comparar performance das estrategias vs Ibovespa (benchmark)

**Checkpoint**: Pagina de Historico mostra evolucao de recomendacoes passadas com taxa de acerto

---

## Phase 5: Novas Fontes de Dados (Prioridade: P2)

**Goal**: Enriquecer analise com mais dados

- [ ] T031 [P] [US5] Coletor Status Invest (scraping) em `src/collectors/statusinvest_collector.py` para dados de dividendos detalhados
- [ ] T032 [P] [US5] Coletor Tesouro Direto em `src/collectors/tesouro_collector.py` para comparar DY vs renda fixa
- [ ] T033 [P] [US5] Coletor de FIIs (Fundos Imobiliarios) via Fundamentus em `src/collectors/fii_collector.py`
- [ ] T034 [US5] Criar pagina `dashboard/pages/13_Renda_Fixa.py` comparando DY das acoes vs Tesouro Direto e CDBs
- [ ] T035 [US5] Criar pagina `dashboard/pages/14_FIIs.py` com analise de fundos imobiliarios
- [ ] T036 [US5] Integrar dados de FIIs nos cruzamentos e scores

**Checkpoint**: Dashboard mostra comparativo DY acoes vs Tesouro IPCA+

---

## Phase 6: Carteira Personalizada (Prioridade: P3)

**Goal**: Usuario pode montar e acompanhar sua propria carteira

- [ ] T037 [US6] Criar tabela `carteira_usuario` no banco: ticker, quantidade, preco_medio, data_compra
- [ ] T038 [US6] Criar pagina `dashboard/pages/15_Minha_Carteira.py` com:
  - Formulario para adicionar/remover acoes
  - Valor total investido vs valor atual
  - Lucro/prejuizo por acao e total
  - Diversificacao por setor (grafico pizza)
  - Alertas especificos para acoes da carteira
- [ ] T039 [US6] Calcular rentabilidade da carteira vs CDI e Ibovespa
- [ ] T040 [US6] Sugerir rebalanceamento baseado nos scores atuais
- [ ] T041 [US6] Exportar relatorio da carteira em PDF

**Checkpoint**: Usuario adiciona 5 acoes e ve lucro/prejuizo total com grafico de diversificacao

---

## Phase 7: Analise de Fatos Relevantes com IA (Prioridade: P3)

**Goal**: Usar LLM para classificar fatos relevantes da CVM como positivos/negativos

- [ ] T042 [US7] Coletor de fatos relevantes da CVM em `src/collectors/cvm_fatos_collector.py`
- [ ] T043 [US7] Integrar com API Claude/OpenAI para classificar sentimento dos fatos relevantes
- [ ] T044 [US7] Criar pagina `dashboard/pages/16_Fatos_Relevantes.py` com timeline de fatos e sentimento
- [ ] T045 [US7] Correlacionar fatos relevantes com volume anomalo (ja temos volume_ratio no TechnicalCalculator)
- [ ] T046 [US7] Adicionar score de "sentimento de mercado" baseado nos fatos recentes

**Checkpoint**: Fatos relevantes de PETR4 aparecem classificados com sentimento e correlacionados com volume

---

## Phase 8: Performance e Cache (Prioridade: P3)

**Goal**: Dashboard mais rapido, menos chamadas a APIs externas

- [ ] T047 [P] [US8] Implementar cache em memoria com TTL em `src/cache/memory_cache.py`
- [ ] T048 [P] [US8] Opcional: Implementar cache Redis em `src/cache/redis_cache.py`
- [ ] T049 [US8] Cachear chamadas ao Fundamentus (TTL: 1 hora)
- [ ] T050 [US8] Cachear chamadas a brapi (TTL: 5 minutos para cotacoes)
- [ ] T051 [US8] Cachear chamadas ao BCB (TTL: 1 hora)
- [ ] T052 [US8] Pre-calcular dados pesados (scores, recomendacoes) no job diario e salvar no banco
- [ ] T053 [US8] Dashboard le dados pre-calculados do banco ao inves de recalcular a cada acesso

**Checkpoint**: Pagina de Recomendacoes carrega em < 3 segundos com cache ativo

---

## Phase 9: Deploy e Acesso Remoto (Prioridade: P3)

**Goal**: Acessar o dashboard de qualquer lugar

- [ ] T054 [US9] Criar Dockerfile e docker-compose.yml (Python + PostgreSQL + Streamlit)
- [ ] T055 [US9] Configurar deploy no Streamlit Cloud (gratuito) ou Railway
- [ ] T056 [US9] Configurar variaves de ambiente no ambiente de deploy
- [ ] T057 [US9] Configurar dominio customizado (opcional)
- [ ] T058 [US9] Adicionar autenticacao basica no Streamlit (st.secrets)

**Checkpoint**: Dashboard acessivel via URL publica com autenticacao

---

## Dependencies & Execution Order

### Ordem Recomendada

```
Phase 1 (Banco) ──┐
                   ├──> Phase 2 (Automacao) ──> Phase 3 (Notificacoes)
                   │
                   ├──> Phase 4 (Historico/Backtest)
                   │
Phase 5 (Fontes) ──┤    (pode rodar em paralelo)
                   │
Phase 6 (Carteira)─┘

Phase 7 (IA) ── independente, requer API key de LLM
Phase 8 (Cache) ── pode rodar a qualquer momento
Phase 9 (Deploy) ── idealmente apos Phase 1 e 2
```

### Prioridades

| Prioridade | Phases | Impacto |
|---|---|---|
| **P1 - Critica** | 1 (Banco), 2 (Automacao) | Sistema autonomo sem intervencao manual |
| **P2 - Alta** | 3 (Notificacoes), 4 (Historico), 5 (Fontes) | Valor para o usuario final |
| **P3 - Media** | 6 (Carteira), 7 (IA), 8 (Cache), 9 (Deploy) | Melhorias e extras |

---

## Notes

- [P] = pode rodar em paralelo com outras tarefas da mesma phase
- [USx] = user story associada
- Cada phase entrega valor independente
- Priorizar Phase 1 e 2 pois habilitam todas as demais
- Total: 58 tarefas em 9 phases
