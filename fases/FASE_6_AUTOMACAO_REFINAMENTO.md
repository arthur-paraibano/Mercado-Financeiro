# Fase 6 - Automacao e Refinamento

**Pre-requisito:** Fases 1 a 5 concluidas.

**Objetivo:** Fazer o sistema rodar de forma totalmente automatica, com atualizacoes periodicas, notificacoes de alertas, backtest de estrategias e otimizacao de performance.

**Resultado esperado ao final:** Sistema rodando 24/7 sem intervencao manual, enviando alertas via Telegram quando detecta empresas com problemas, e com historico para backtesting de estrategias.

---

## Checklist de Entregas

- [ ] Agendador de tarefas (APScheduler) configurado
- [ ] Job diario: atualizar cotacoes e indicadores
- [ ] Job semanal: atualizar dados macro (BCB, IBGE)
- [ ] Job trimestral: processar DFP/ITR da CVM
- [ ] Job mensal: processar carteiras de fundos
- [ ] Notificacoes via Telegram Bot
- [ ] Notificacoes via Email
- [ ] Sistema de backtest de estrategias
- [ ] Cache com Redis para performance
- [ ] Metricas de qualidade dos dados
- [ ] Dashboard com logs e status dos jobs

---

## Passo 1 - Agendador de Tarefas

### src/scheduler/jobs.py
```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import sys
sys.path.append(".")

from src.collectors.brapi_collector import BrapiCollector
from src.collectors.bcb_collector import BCBCollector
from src.collectors.b3_collector import B3Collector
from src.collectors.cvm_collector import CVMCollector
from src.collectors.cvm_fundos_collector import CVMFundosCollector
from src.alerts.alert_engine import AlertEngine
from src.notifications.telegram_notifier import TelegramNotifier
from datetime import date


scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
notifier  = TelegramNotifier()


# ============================================================
# JOB DIARIO - Dias uteis, 18h30 (apos fechamento da bolsa)
# ============================================================
@scheduler.scheduled_job(CronTrigger(day_of_week="mon-fri", hour=18, minute=30))
def job_cotacoes_diarias():
    """Atualiza cotacoes e recalcula indicadores de todas as empresas do Ibovespa."""
    logger.info("[JOB DIARIO] Iniciando atualizacao de cotacoes...")

    b3     = B3Collector()
    brapi  = BrapiCollector()
    engine = AlertEngine()

    composicao = b3.get_composicao_ibovespa()
    if composicao.empty:
        logger.error("[JOB DIARIO] Falha ao obter composicao do Ibovespa.")
        return

    tickers = composicao["ticker"].tolist()
    novos_alertas_criticos = []

    for ticker in tickers:
        try:
            alertas = engine.analisar_ticker(ticker)
            criticos = [a for a in alertas if a.severidade == "CRITICO"]
            novos_alertas_criticos.extend(criticos)
        except Exception as e:
            logger.error(f"[JOB DIARIO] Erro ao analisar {ticker}: {e}")

    logger.info(f"[JOB DIARIO] {len(novos_alertas_criticos)} alertas criticos detectados.")

    # Notificar alertas criticos
    if novos_alertas_criticos:
        mensagem = f"*Alertas Criticos Detectados*\n\n"
        for alerta in novos_alertas_criticos[:10]:  # Maximo 10 no resumo
            mensagem += f"🔴 *{alerta.ticker}*: {alerta.titulo}\n"
        if len(novos_alertas_criticos) > 10:
            mensagem += f"\n... e mais {len(novos_alertas_criticos) - 10} alertas."
        notifier.enviar(mensagem)

    logger.info("[JOB DIARIO] Concluido.")


# ============================================================
# JOB SEMANAL - Segunda-feira, 7h00
# ============================================================
@scheduler.scheduled_job(CronTrigger(day_of_week="mon", hour=7, minute=0))
def job_dados_macro():
    """Atualiza indicadores macroeconomicos do BCB e IBGE."""
    logger.info("[JOB SEMANAL] Atualizando dados macro...")

    bcb = BCBCollector()

    try:
        selic  = bcb.get_selic()
        ipca   = bcb.get_ipca()
        cambio = bcb.get_cambio_dolar()
        logger.info(f"[JOB SEMANAL] SELIC atual: {selic['valor'].iloc[-1]:.2f}%")
        logger.info(f"[JOB SEMANAL] PTAX atual: R$ {cambio['valor'].iloc[-1]:.4f}")
    except Exception as e:
        logger.error(f"[JOB SEMANAL] Erro macro: {e}")

    logger.info("[JOB SEMANAL] Concluido.")


# ============================================================
# JOB MENSAL - Dia 20 de cada mes, 6h00
# ============================================================
@scheduler.scheduled_job(CronTrigger(day=20, hour=6, minute=0))
def job_carteiras_fundos():
    """Baixa carteiras mensais dos fundos da CVM."""
    logger.info("[JOB MENSAL] Processando carteiras de fundos...")

    hoje = date.today()
    # Processar mes anterior (CVM tem atraso de ~45 dias)
    ano  = hoje.year if hoje.month > 1 else hoje.year - 1
    mes  = hoje.month - 2 if hoje.month > 2 else 12 + (hoje.month - 2)

    cvm_fundos = CVMFundosCollector()
    try:
        carteira = cvm_fundos.get_carteira_mensal(ano, mes)
        logger.info(f"[JOB MENSAL] Carteira {ano}/{mes:02d}: {len(carteira)} registros")
    except Exception as e:
        logger.error(f"[JOB MENSAL] Erro carteiras: {e}")

    logger.info("[JOB MENSAL] Concluido.")


# ============================================================
# JOB TRIMESTRAL - 15/jan, 15/abr, 15/jul, 15/out - 5h00
# ============================================================
@scheduler.scheduled_job(CronTrigger(month="1,4,7,10", day=15, hour=5, minute=0))
def job_dados_contabeis():
    """Processa DFP/ITR trimestral da CVM."""
    logger.info("[JOB TRIMESTRAL] Processando dados contabeis da CVM...")

    cvm = CVMCollector()
    hoje = date.today()

    try:
        dados = cvm.get_dfp_ano(hoje.year - 1)
        logger.info(f"[JOB TRIMESTRAL] DFP {hoje.year - 1}: {len(dados)} demonstrativos baixados")
    except Exception as e:
        logger.error(f"[JOB TRIMESTRAL] Erro DFP: {e}")

    logger.info("[JOB TRIMESTRAL] Concluido.")


if __name__ == "__main__":
    logger.info("Agendador iniciado. Jobs configurados:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.id}: proximo em {job.next_run_time}")
    scheduler.start()
```

---

## Passo 2 - Notificador Telegram

### src/notifications/telegram_notifier.py
```python
import requests
from loguru import logger
from config.settings import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


class TelegramNotifier:
    """Envia mensagens via Telegram Bot."""

    def __init__(self):
        self.token   = TELEGRAM_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def enviar(self, mensagem: str, parse_mode: str = "Markdown") -> bool:
        """
        Envia mensagem de texto para o chat configurado.
        Suporta Markdown: *negrito*, _italico_, `codigo`
        """
        if not self.token or not self.chat_id:
            logger.warning("Telegram nao configurado. Pulando notificacao.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id":    self.chat_id,
            "text":       mensagem,
            "parse_mode": parse_mode,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Notificacao Telegram enviada.")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram: {e}")
            return False

    def enviar_alerta(self, ticker: str, tipo: str, severidade: str, titulo: str, descricao: str):
        """Formata e envia um alerta especifico."""
        icones = {"CRITICO": "🔴", "ALTO": "🟠", "MEDIO": "🟡", "INFO": "🔵"}
        icone  = icones.get(severidade, "⚪")

        mensagem = (
            f"{icone} *{severidade} | {ticker}*\n"
            f"📋 {titulo}\n\n"
            f"_{descricao}_"
        )
        self.enviar(mensagem)

    def enviar_resumo_diario(self, resumo: dict):
        """
        Envia resumo diario do mercado.
        resumo: {ibovespa_variacao, dolar, selic, num_alertas, melhores, piores}
        """
        ibov = resumo.get("ibovespa_variacao", 0)
        sinal = "📈" if ibov >= 0 else "📉"

        mensagem = (
            f"*Resumo do Mercado - {resumo.get('data', 'Hoje')}*\n\n"
            f"{sinal} Ibovespa: {ibov:+.2f}%\n"
            f"💵 Dolar: R$ {resumo.get('dolar', 0):.4f}\n"
            f"🏦 SELIC: {resumo.get('selic', 0):.2f}% a.a.\n\n"
            f"🚨 Alertas detectados: {resumo.get('num_alertas', 0)}\n"
        )

        melhores = resumo.get("melhores", [])
        piores   = resumo.get("piores", [])

        if melhores:
            mensagem += f"\n*Top Altas:*\n"
            for t in melhores[:3]:
                mensagem += f"  {t['ticker']}: {t['variacao']:+.2f}%\n"

        if piores:
            mensagem += f"\n*Top Baixas:*\n"
            for t in piores[:3]:
                mensagem += f"  {t['ticker']}: {t['variacao']:+.2f}%\n"

        self.enviar(mensagem)
```

### Adicionar ao .env
```
TELEGRAM_TOKEN=seu_token_do_bot_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

**Como criar um bot Telegram:**
1. Abrir Telegram e buscar @BotFather
2. Enviar `/newbot` e seguir instrucoes
3. Copiar o token gerado para `.env`
4. Para obter chat_id: acessar `https://api.telegram.org/bot{TOKEN}/getUpdates` apos enviar mensagem ao bot

---

## Passo 3 - Notificador Email

### src/notifications/email_notifier.py
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
from config.settings import EMAIL_REMETENTE, EMAIL_SENHA, EMAIL_DESTINATARIO


class EmailNotifier:
    """Envia emails de notificacao via SMTP."""

    def enviar(self, assunto: str, corpo_html: str) -> bool:
        if not EMAIL_REMETENTE or not EMAIL_SENHA:
            logger.warning("Email nao configurado. Pulando.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = EMAIL_REMETENTE
        msg["To"]      = EMAIL_DESTINATARIO

        msg.attach(MIMEText(corpo_html, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_REMETENTE, EMAIL_SENHA)
                smtp.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
            logger.info(f"Email enviado: {assunto}")
            return True
        except Exception as e:
            logger.error(f"Erro email: {e}")
            return False

    def enviar_relatorio_semanal(self, html_relatorio: str):
        self.enviar("Relatorio Semanal - Mercado Financeiro BR", html_relatorio)
```

---

## Passo 4 - Sistema de Backtest

### src/backtest/backtester.py
```python
import pandas as pd
import numpy as np
from typing import Callable, List, Dict
from loguru import logger


class Backtester:
    """
    Testa estrategias de investimento usando dados historicos.
    Uma estrategia e uma funcao que recebe indicadores e retorna True/False (compra/nao compra).
    """

    def __init__(self, cotacoes_historicas: pd.DataFrame, indicadores_historicos: pd.DataFrame):
        """
        cotacoes_historicas: DataFrame com colunas [ticker, data, fechamento]
        indicadores_historicos: DataFrame com colunas [ticker, data, pl, pvp, roe, dy, ...]
        """
        self.cotacoes    = cotacoes_historicas
        self.indicadores = indicadores_historicos

    def executar(
        self,
        estrategia: Callable[[dict], bool],
        capital_inicial: float = 100_000.0,
        rebalancear_meses: int = 3,
        max_posicoes: int = 10,
        nome: str = "Estrategia"
    ) -> dict:
        """
        Executa backtest da estrategia.

        estrategia: funcao que recebe dict de indicadores e retorna True se deve comprar.
        rebalancear_meses: a cada quantos meses rebalancear a carteira.
        max_posicoes: numero maximo de acoes na carteira.

        Retorna: dict com metricas de performance.
        """
        datas = sorted(self.indicadores["data"].unique())
        datas_rebalancear = [d for i, d in enumerate(datas) if i % (rebalancear_meses * 21) == 0]

        carteira = {}       # ticker -> quantidade
        capital  = capital_inicial
        historico_valor = []

        for data in datas:
            # Rebalancear
            if data in datas_rebalancear:
                ind_data = self.indicadores[self.indicadores["data"] == data]
                selecionadas = []

                for _, row in ind_data.iterrows():
                    if estrategia(row.to_dict()):
                        selecionadas.append(row["ticker"])

                selecionadas = selecionadas[:max_posicoes]

                # Calcular valor atual da carteira
                valor_atual = capital
                for ticker, qtd in carteira.items():
                    preco = self._get_preco(ticker, data)
                    if preco:
                        valor_atual += qtd * preco

                # Redistribuir igualmente entre selecionadas
                if selecionadas:
                    valor_por_acao = valor_atual / len(selecionadas)
                    nova_carteira = {}
                    capital = 0

                    for ticker in selecionadas:
                        preco = self._get_preco(ticker, data)
                        if preco and preco > 0:
                            nova_carteira[ticker] = int(valor_por_acao / preco)
                            capital += valor_por_acao - nova_carteira[ticker] * preco

                    carteira = nova_carteira

            # Calcular valor total do portfolio nesta data
            valor_portfolio = capital
            for ticker, qtd in carteira.items():
                preco = self._get_preco(ticker, data)
                if preco:
                    valor_portfolio += qtd * preco

            historico_valor.append({"data": data, "valor": valor_portfolio})

        df_historico = pd.DataFrame(historico_valor)
        return self._calcular_metricas(df_historico, capital_inicial, nome)

    def _get_preco(self, ticker: str, data) -> float:
        row = self.cotacoes[
            (self.cotacoes["ticker"] == ticker) &
            (self.cotacoes["data"] <= data)
        ].tail(1)
        return float(row["fechamento"].values[0]) if len(row) > 0 else None

    def _calcular_metricas(self, df: pd.DataFrame, capital_inicial: float, nome: str) -> dict:
        if df.empty:
            return {}

        retorno_total = (df["valor"].iloc[-1] / capital_inicial - 1) * 100
        anos = (df["data"].iloc[-1] - df["data"].iloc[0]).days / 365.25
        cagr = ((df["valor"].iloc[-1] / capital_inicial) ** (1 / anos) - 1) * 100 if anos > 0 else 0

        retornos_diarios = df["valor"].pct_change().dropna()
        volatilidade = retornos_diarios.std() * np.sqrt(252) * 100
        sharpe = (cagr - 13.75) / volatilidade if volatilidade > 0 else 0  # SELIC como risk-free

        # Drawdown maximo
        pico = df["valor"].cummax()
        drawdown = (df["valor"] - pico) / pico * 100
        max_drawdown = drawdown.min()

        return {
            "estrategia":      nome,
            "capital_inicial": capital_inicial,
            "capital_final":   df["valor"].iloc[-1],
            "retorno_total_pct": round(retorno_total, 2),
            "cagr_pct":        round(cagr, 2),
            "volatilidade_pct":round(volatilidade, 2),
            "sharpe":          round(sharpe, 2),
            "max_drawdown_pct":round(max_drawdown, 2),
            "historico":       df,
        }

    def comparar_estrategias(self, estrategias: Dict[str, Callable], **kwargs) -> pd.DataFrame:
        """Executa e compara multiplas estrategias."""
        resultados = []
        for nome, func in estrategias.items():
            res = self.executar(func, nome=nome, **kwargs)
            resultados.append({k: v for k, v in res.items() if k != "historico"})
        return pd.DataFrame(resultados)


# -------------------------------------------------------
# Estrategias exemplo para backtest
# -------------------------------------------------------
def estrategia_valor(ind: dict) -> bool:
    """Compra acoes baratas com boa rentabilidade (value investing)."""
    pl   = ind.get("pl")
    pvp  = ind.get("pvp")
    roe  = ind.get("roe", 0)
    return (pl and 0 < pl < 12) and (pvp and pvp < 1.5) and (roe > 10)


def estrategia_dividendos(ind: dict) -> bool:
    """Compra acoes com alto dividend yield e payout sustentavel."""
    dy     = ind.get("dividend_yield", 0)
    payout = ind.get("payout", 101)
    roe    = ind.get("roe", 0)
    return dy > 6 and payout < 80 and roe > 8


def estrategia_qualidade(ind: dict) -> bool:
    """Compra empresas de alta qualidade (ROE alto, pouca divida)."""
    roe           = ind.get("roe", 0)
    margem        = ind.get("margem_liquida", 0)
    divida_ebitda = ind.get("divida_liq_ebitda", 99)
    return roe > 20 and margem > 10 and (divida_ebitda is None or divida_ebitda < 2)
```

---

## Passo 5 - Cache Redis

### src/cache/redis_cache.py
```python
import json
import redis
from typing import Any, Optional
from loguru import logger
from config.settings import REDIS_URL


class RedisCache:
    """Cache de dados usando Redis para evitar requisicoes repetidas a APIs."""

    def __init__(self):
        try:
            self.client = redis.from_url(REDIS_URL, decode_responses=True)
            self.client.ping()
            self.disponivel = True
        except Exception:
            logger.warning("Redis indisponivel. Cache desativado.")
            self.client = None
            self.disponivel = False

    def get(self, chave: str) -> Optional[Any]:
        if not self.disponivel:
            return None
        try:
            valor = self.client.get(chave)
            return json.loads(valor) if valor else None
        except Exception:
            return None

    def set(self, chave: str, valor: Any, ttl_segundos: int = 3600):
        if not self.disponivel:
            return
        try:
            self.client.setex(chave, ttl_segundos, json.dumps(valor))
        except Exception as e:
            logger.warning(f"Erro ao salvar cache: {e}")

    def delete(self, chave: str):
        if not self.disponivel:
            return
        try:
            self.client.delete(chave)
        except Exception:
            pass

    def chave_cotacao(self, ticker: str) -> str:
        return f"cotacao:{ticker}"

    def chave_historico(self, ticker: str, periodo: str) -> str:
        return f"historico:{ticker}:{periodo}"

    def chave_macro(self, indicador: str) -> str:
        return f"macro:{indicador}"
```

---

## Passo 6 - Pagina de Status e Logs

### dashboard/pages/10_Status.py
```python
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
sys.path.append(".")

st.set_page_config(page_title="Status do Sistema", layout="wide")
st.title("Status do Sistema")

# Status dos jobs (em producao, ler do banco ou arquivo de log)
st.subheader("Proximas Execucoes dos Jobs")

jobs = [
    {"Job": "Cotacoes Diarias",   "Frequencia": "Dias uteis 18h30", "Ultima": "Hoje 18:30", "Status": "✅ OK"},
    {"Job": "Dados Macro",        "Frequencia": "Segunda 7h",       "Ultima": "Esta semana", "Status": "✅ OK"},
    {"Job": "Carteiras Fundos",   "Frequencia": "Dia 20 do mes",    "Ultima": "Mes passado", "Status": "✅ OK"},
    {"Job": "DFP/ITR CVM",        "Frequencia": "Trimestral",       "Ultima": "Ultimo trimestre", "Status": "✅ OK"},
]
st.dataframe(pd.DataFrame(jobs), use_container_width=True)

st.divider()

# Metricas de qualidade dos dados
st.subheader("Qualidade dos Dados")
col1, col2, col3 = st.columns(3)
col1.metric("Empresas com cotacao atualizada", "87 / 90", delta="-3")
col2.metric("Empresas com dados CVM (DFP)", "82 / 90", delta="+2")
col3.metric("Alertas ativos", "23", delta="+5")

st.divider()

# Log de execucoes recentes (ler de arquivo de log)
st.subheader("Log de Execucoes Recentes")
st.code("""
[18:30:01] JOB DIARIO: Iniciando atualizacao de cotacoes...
[18:30:45] JOB DIARIO: 90 tickers processados. 3 erros.
[18:31:02] JOB DIARIO: 12 alertas criticos detectados.
[18:31:03] JOB DIARIO: Notificacao Telegram enviada.
[18:31:03] JOB DIARIO: Concluido em 62 segundos.
""", language="text")
```

---

## Passo 7 - Backtest no Dashboard

### dashboard/pages/11_Backtest.py
```python
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
sys.path.append(".")

from src.backtest.backtester import Backtester, estrategia_valor, estrategia_dividendos, estrategia_qualidade

st.set_page_config(page_title="Backtest de Estrategias", layout="wide")
st.title("Backtest de Estrategias")

st.info("""
Backtesting simula como uma estrategia de selecao de acoes teria se saido no passado.
**Importante:** Performance passada nao garante resultados futuros.
""")

st.subheader("Configuracoes")
col1, col2, col3 = st.columns(3)
capital = col1.number_input("Capital inicial (R$)", value=100_000, step=10_000)
meses_rebalancear = col2.selectbox("Rebalancear a cada:", [1, 3, 6, 12], index=1)
max_posicoes = col3.slider("Max. posicoes na carteira", 5, 20, 10)

estrategias_selecionadas = st.multiselect(
    "Estrategias para comparar:",
    ["Valor (Value Investing)", "Dividendos", "Qualidade"],
    default=["Valor (Value Investing)", "Dividendos", "Qualidade"]
)

st.caption("*Para um backtest real, os dados historicos de indicadores precisam estar no banco de dados (populados pelas fases anteriores).*")

# Demonstracao com dados simulados
if st.button("Executar Backtest (demonstracao)"):
    import numpy as np
    from datetime import date, timedelta

    # Dados simulados para demonstracao
    datas = pd.date_range(start="2019-01-01", end="2024-12-31", freq="B")
    np.random.seed(42)

    resultados_demo = {
        "Valor":      {"cagr": 18.5, "sharpe": 0.82, "max_drawdown": -38.2, "retorno_total": 147.3},
        "Dividendos": {"cagr": 14.2, "sharpe": 1.15, "max_drawdown": -22.5, "retorno_total": 98.6},
        "Qualidade":  {"cagr": 22.1, "sharpe": 1.02, "max_drawdown": -29.8, "retorno_total": 192.4},
        "Ibovespa":   {"cagr": 10.8, "sharpe": 0.45, "max_drawdown": -46.7, "retorno_total": 63.2},
    }

    # Grafico de evolucao do capital
    fig = go.Figure()
    for nome, res in resultados_demo.items():
        capital_serie = [capital]
        retorno_diario_medio = (1 + res["cagr"] / 100) ** (1/252) - 1
        for i in range(len(datas) - 1):
            ruido = np.random.normal(0, 0.01)
            capital_serie.append(capital_serie[-1] * (1 + retorno_diario_medio + ruido))
        fig.add_trace(go.Scatter(x=datas, y=capital_serie, name=nome, mode="lines"))

    fig.update_layout(
        title="Evolucao do Capital (Simulado)",
        yaxis_title="Valor do Portfolio (R$)",
        xaxis_title="Data",
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabela comparativa
    df_comp = pd.DataFrame(resultados_demo).T.reset_index()
    df_comp.columns = ["Estrategia", "CAGR %", "Sharpe", "Max Drawdown %", "Retorno Total %"]
    st.dataframe(df_comp, use_container_width=True)
```

---

## Passo 8 - Adicionar ao .env

```
# Notificacoes
TELEGRAM_TOKEN=token_do_bot
TELEGRAM_CHAT_ID=seu_chat_id

EMAIL_REMETENTE=seuemail@gmail.com
EMAIL_SENHA=sua_senha_de_app_gmail  # senha de app, nao a senha normal
EMAIL_DESTINATARIO=destino@email.com

# Redis (opcional - melhora performance)
REDIS_URL=redis://localhost:6379/0
```

---

## Como Iniciar o Agendador em Producao

```bash
# Opcao 1 - Rodar direto (bloqueia o terminal)
python src/scheduler/jobs.py

# Opcao 2 - Rodar em background com nohup
nohup python src/scheduler/jobs.py > logs/scheduler.log 2>&1 &

# Opcao 3 - Criar servico systemd (Linux)
# Criar arquivo /etc/systemd/system/mercado-financeiro.service
# [Unit]
# Description=Sistema Mercado Financeiro
# [Service]
# ExecStart=/usr/bin/python3 /caminho/src/scheduler/jobs.py
# Restart=always
# [Install]
# WantedBy=multi-user.target

# Verificar logs
tail -f logs/scheduler.log
```

---

## Criterio de Conclusao da Fase 6

A fase esta concluida quando:
1. `python src/scheduler/jobs.py` inicia sem erros e lista os jobs agendados
2. Uma mensagem de teste chega no Telegram
3. O backtest de demonstracao exibe o grafico de evolucao do capital
4. A pagina de Status mostra os jobs e suas proximas execucoes
5. O sistema roda por 24h sem crashes
