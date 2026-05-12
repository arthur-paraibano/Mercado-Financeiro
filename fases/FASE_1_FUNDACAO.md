# Fase 1 - Fundacao (MVP)

**Objetivo:** Ter um sistema funcionando que coleta dados de uma empresa, calcula indicadores basicos e exibe em um dashboard simples.

**Resultado esperado ao final:** Digitar `PETR4` e ver cotacao atual, P/L, P/VP, ROE, DY, balanco e DRE resumida em uma pagina web local.

---

## Checklist de Entregas

- [ ] Ambiente Python configurado com dependencias
- [ ] Banco de dados PostgreSQL criado com schema inicial
- [ ] Coletor da CVM funcionando (DFP e ITR)
- [ ] Coletor da brapi funcionando (cotacoes + indicadores)
- [ ] Calculos de indicadores basicos implementados
- [ ] Dashboard Streamlit exibindo dados de 1 empresa
- [ ] Testes unitarios cobrindo os coletores

---

## Passo 1 - Configurar o Ambiente

### 1.1 Criar estrutura de pastas
```
mercado-financeiro/
|-- fases/
|-- config/
|-- src/
|   |-- collectors/
|   |-- processors/
|   |-- models/
|   |-- database/
|-- dashboard/
|   |-- pages/
|-- tests/
|   |-- test_collectors/
|   |-- test_processors/
|-- scripts/
|-- data/
|   |-- raw/          # Arquivos baixados das APIs
|   |-- processed/    # Dados tratados
```

### 1.2 Criar requirements.txt
```
# Coleta de dados
requests==2.31.0
aiohttp==3.9.0
python-bcb==0.3.0
yfinance==0.2.36
fundamentus==1.1.0

# Processamento
pandas==2.1.0
numpy==1.26.0

# Banco de dados
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# Dashboard
streamlit==1.29.0
plotly==5.18.0

# Utilitarios
python-dotenv==1.0.0
loguru==0.7.2
```

### 1.3 Criar arquivo .env
```
# brapi.dev - obter em https://brapi.dev/dashboard
BRAPI_TOKEN=seu_token_aqui

# Banco de dados
DATABASE_URL=postgresql://postgres:senha@localhost:5432/mercado_financeiro

# Ambiente
LOG_LEVEL=INFO
```

### 1.4 Criar config/settings.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

# APIs
BRAPI_TOKEN = os.getenv("BRAPI_TOKEN")
BRAPI_BASE_URL = "https://brapi.dev/api"

# CVM
CVM_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
CVM_DFP_URL = f"{CVM_BASE_URL}/DOC/DFP/DADOS"
CVM_ITR_URL = f"{CVM_BASE_URL}/DOC/ITR/DADOS"

# Banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")

# Rate limits (segundos entre requisicoes)
BRAPI_DELAY = 0.5
CVM_DELAY = 1.0

# Cache
CACHE_TTL_COTACAO = 300        # 5 minutos
CACHE_TTL_INDICADORES = 3600   # 1 hora
CACHE_TTL_DFP = 86400          # 24 horas
```

---

## Passo 2 - Banco de Dados

### 2.1 Criar banco PostgreSQL
```sql
CREATE DATABASE mercado_financeiro;
```

### 2.2 Schema inicial - src/database/schema.sql
```sql
-- Empresas cadastradas
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    nome VARCHAR(200),
    cnpj VARCHAR(20),
    setor VARCHAR(100),
    subsetor VARCHAR(100),
    segmento VARCHAR(100),
    situacao VARCHAR(50),
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Cotacoes diarias
CREATE TABLE IF NOT EXISTS cotacoes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    data DATE NOT NULL,
    abertura NUMERIC(15,2),
    maxima NUMERIC(15,2),
    minima NUMERIC(15,2),
    fechamento NUMERIC(15,2),
    volume BIGINT,
    variacao_pct NUMERIC(8,4),
    UNIQUE(empresa_id, data)
);

-- DRE - Demonstracao de Resultado
CREATE TABLE IF NOT EXISTS dre (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    periodo VARCHAR(10) NOT NULL,  -- '2023-T1', '2023-A' (anual)
    tipo VARCHAR(3) NOT NULL,       -- 'ITR' ou 'DFP'
    receita_liquida NUMERIC(20,2),
    custo_produtos NUMERIC(20,2),
    lucro_bruto NUMERIC(20,2),
    despesas_operacionais NUMERIC(20,2),
    ebit NUMERIC(20,2),
    ebitda NUMERIC(20,2),
    resultado_financeiro NUMERIC(20,2),
    lucro_antes_ir NUMERIC(20,2),
    lucro_liquido NUMERIC(20,2),
    UNIQUE(empresa_id, periodo, tipo)
);

-- Balanco Patrimonial
CREATE TABLE IF NOT EXISTS balanco (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    periodo VARCHAR(10) NOT NULL,
    tipo VARCHAR(3) NOT NULL,
    ativo_total NUMERIC(20,2),
    ativo_circulante NUMERIC(20,2),
    ativo_nao_circulante NUMERIC(20,2),
    caixa_equivalentes NUMERIC(20,2),
    passivo_total NUMERIC(20,2),
    passivo_circulante NUMERIC(20,2),
    divida_bruta NUMERIC(20,2),
    divida_liquida NUMERIC(20,2),
    patrimonio_liquido NUMERIC(20,2),
    UNIQUE(empresa_id, periodo, tipo)
);

-- Fluxo de Caixa
CREATE TABLE IF NOT EXISTS fluxo_caixa (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    periodo VARCHAR(10) NOT NULL,
    tipo VARCHAR(3) NOT NULL,
    fcf_operacional NUMERIC(20,2),
    fcf_investimento NUMERIC(20,2),
    fcf_financiamento NUMERIC(20,2),
    capex NUMERIC(20,2),
    fcf_livre NUMERIC(20,2),
    UNIQUE(empresa_id, periodo, tipo)
);

-- Indicadores calculados
CREATE TABLE IF NOT EXISTS indicadores (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    data DATE NOT NULL,
    pl NUMERIC(10,2),           -- Preco/Lucro
    pvp NUMERIC(10,2),          -- Preco/Valor Patrimonial
    ev_ebitda NUMERIC(10,2),
    psr NUMERIC(10,2),          -- Preco/Receita
    roe NUMERIC(8,4),           -- %
    roa NUMERIC(8,4),           -- %
    roic NUMERIC(8,4),          -- %
    margem_bruta NUMERIC(8,4),  -- %
    margem_ebitda NUMERIC(8,4), -- %
    margem_liquida NUMERIC(8,4),-- %
    divida_liq_ebitda NUMERIC(10,2),
    dividend_yield NUMERIC(8,4),-- %
    payout NUMERIC(8,4),        -- %
    market_cap NUMERIC(20,2),
    enterprise_value NUMERIC(20,2),
    UNIQUE(empresa_id, data)
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_cotacoes_empresa_data ON cotacoes(empresa_id, data);
CREATE INDEX IF NOT EXISTS idx_indicadores_empresa_data ON indicadores(empresa_id, data);
CREATE INDEX IF NOT EXISTS idx_dre_empresa_periodo ON dre(empresa_id, periodo);
```

### 2.3 src/database/connection.py
```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL
from loguru import logger

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    with open("src/database/schema.sql") as f:
        sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    logger.info("Banco de dados inicializado.")
```

---

## Passo 3 - Coletor da brapi

### src/collectors/brapi_collector.py
```python
import requests
import time
from loguru import logger
from config.settings import BRAPI_TOKEN, BRAPI_BASE_URL, BRAPI_DELAY


class BrapiCollector:
    """Coleta dados de cotacao e indicadores da brapi.dev."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {BRAPI_TOKEN}"})

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{BRAPI_BASE_URL}/{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            time.sleep(BRAPI_DELAY)
            return resp.json()
        except requests.HTTPError as e:
            logger.error(f"Erro HTTP brapi [{url}]: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro brapi [{url}]: {e}")
            raise

    def get_cotacao(self, ticker: str) -> dict:
        """Retorna cotacao atual e indicadores de um ticker."""
        data = self._get(f"quote/{ticker}", params={"fundamental": "true"})
        results = data.get("results", [])
        if not results:
            raise ValueError(f"Ticker {ticker} nao encontrado na brapi.")
        return results[0]

    def get_historico(self, ticker: str, periodo: str = "1y", intervalo: str = "1d") -> list:
        """Retorna historico de cotacoes OHLCV."""
        data = self._get(
            f"quote/{ticker}",
            params={"range": periodo, "interval": intervalo}
        )
        results = data.get("results", [])
        if not results:
            return []
        return results[0].get("historicalDataPrice", [])

    def get_dividendos(self, ticker: str) -> list:
        """Retorna historico de dividendos."""
        data = self._get(f"quote/{ticker}", params={"dividends": "true"})
        results = data.get("results", [])
        if not results:
            return []
        return results[0].get("dividendsData", {}).get("cashDividends", [])

    def get_lista_acoes(self) -> list:
        """Retorna lista de todos os tickers disponiveis."""
        data = self._get("quote/list")
        return data.get("stocks", [])
```

---

## Passo 4 - Coletor da CVM

### src/collectors/cvm_collector.py
```python
import io
import time
import zipfile
import requests
import pandas as pd
from loguru import logger
from config.settings import CVM_DFP_URL, CVM_ITR_URL, CVM_DELAY


# Mapeamento de contas contabeis CVM -> campos do sistema
CONTAS_DRE = {
    "3.01":  "receita_liquida",
    "3.02":  "custo_produtos",
    "3.03":  "lucro_bruto",
    "3.04":  "despesas_operacionais",
    "3.05":  "ebit",
    "3.06":  "resultado_financeiro",
    "3.08":  "lucro_antes_ir",
    "3.11":  "lucro_liquido",
}

CONTAS_BPA = {  # Ativo
    "1":     "ativo_total",
    "1.01":  "ativo_circulante",
    "1.01.01": "caixa_equivalentes",
    "1.02":  "ativo_nao_circulante",
}

CONTAS_BPP = {  # Passivo
    "2":     "passivo_total",
    "2.01":  "passivo_circulante",
    "2.03":  "patrimonio_liquido",
}

CONTAS_DFC = {
    "6.01":  "fcf_operacional",
    "6.02":  "fcf_investimento",
    "6.03":  "fcf_financiamento",
}


class CVMCollector:
    """Coleta e processa dados da CVM (DFP e ITR)."""

    def _download_csv(self, url: str) -> pd.DataFrame:
        logger.info(f"Baixando: {url}")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        time.sleep(CVM_DELAY)

        if url.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                nome_csv = [f for f in z.namelist() if f.endswith(".csv")][0]
                with z.open(nome_csv) as f:
                    return pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
        else:
            return pd.read_csv(
                io.BytesIO(resp.content), sep=";", encoding="latin-1", dtype=str
            )

    def get_dfp_ano(self, ano: int) -> dict:
        """
        Baixa DFP anual da CVM e retorna dict com DataFrames por demonstrativo.
        Retorna: {"dre": df, "bpa": df, "bpp": df, "dfc": df}
        """
        base = f"{CVM_DFP_URL}/dfp_cia_aberta_{ano}.zip"
        resultado = {}

        demos = {
            "dre": f"{CVM_DFP_URL}/dfp_cia_aberta_DRE_con_{ano}.zip",
            "bpa": f"{CVM_DFP_URL}/dfp_cia_aberta_BPA_con_{ano}.zip",
            "bpp": f"{CVM_DFP_URL}/dfp_cia_aberta_BPP_con_{ano}.zip",
            "dfc": f"{CVM_DFP_URL}/dfp_cia_aberta_DFC_MI_con_{ano}.zip",
        }

        for nome, url in demos.items():
            try:
                df = self._download_csv(url)
                resultado[nome] = df
                logger.info(f"DFP {ano} - {nome}: {len(df)} linhas")
            except Exception as e:
                logger.warning(f"Erro ao baixar {nome} {ano}: {e}")

        return resultado

    def get_itr_trimestre(self, ano: int, trimestre: int) -> dict:
        """
        Baixa ITR trimestral. trimestre = 1, 2 ou 3 (4T = DFP anual).
        """
        base_url = f"{CVM_ITR_URL}/itr_cia_aberta"
        resultado = {}

        demos = {
            "dre": f"{base_url}_DRE_con_{ano}.zip",
            "bpa": f"{base_url}_BPA_con_{ano}.zip",
            "bpp": f"{base_url}_BPP_con_{ano}.zip",
            "dfc": f"{base_url}_DFC_MI_con_{ano}.zip",
        }

        for nome, url in demos.items():
            try:
                df = self._download_csv(url)
                # Filtrar trimestre especifico
                df["DT_REFER"] = pd.to_datetime(df["DT_REFER"])
                mes_final = trimestre * 3
                df = df[df["DT_REFER"].dt.month == mes_final]
                df = df[df["DT_REFER"].dt.year == ano]
                resultado[nome] = df
            except Exception as e:
                logger.warning(f"Erro ao baixar ITR {nome} {ano}T{trimestre}: {e}")

        return resultado

    def extrair_dre_empresa(self, df_dre: pd.DataFrame, cnpj: str) -> dict:
        """Extrai linhas da DRE para uma empresa especifica pelo CNPJ."""
        df = df_dre[df_dre["CNPJ_CIA"] == cnpj].copy()
        df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")

        resultado = {}
        for codigo, campo in CONTAS_DRE.items():
            linha = df[df["CD_CONTA"] == codigo]["VL_CONTA"]
            resultado[campo] = float(linha.values[0]) if len(linha) > 0 else None

        return resultado

    def extrair_balanco_empresa(self, df_bpa: pd.DataFrame, df_bpp: pd.DataFrame, cnpj: str) -> dict:
        """Extrai balanco patrimonial para uma empresa."""
        resultado = {}

        df_ativo = df_bpa[df_bpa["CNPJ_CIA"] == cnpj].copy()
        df_ativo["VL_CONTA"] = pd.to_numeric(df_ativo["VL_CONTA"], errors="coerce")

        for codigo, campo in CONTAS_BPA.items():
            linha = df_ativo[df_ativo["CD_CONTA"] == codigo]["VL_CONTA"]
            resultado[campo] = float(linha.values[0]) if len(linha) > 0 else None

        df_passivo = df_bpp[df_bpp["CNPJ_CIA"] == cnpj].copy()
        df_passivo["VL_CONTA"] = pd.to_numeric(df_passivo["VL_CONTA"], errors="coerce")

        for codigo, campo in CONTAS_BPP.items():
            linha = df_passivo[df_passivo["CD_CONTA"] == codigo]["VL_CONTA"]
            resultado[campo] = float(linha.values[0]) if len(linha) > 0 else None

        return resultado
```

---

## Passo 5 - Processador de Indicadores

### src/processors/indicator_calculator.py
```python
from loguru import logger


class IndicatorCalculator:
    """Calcula indicadores fundamentalistas a partir de dados brutos."""

    @staticmethod
    def calcular_indicadores(cotacao: dict, dre: dict, balanco: dict) -> dict:
        """
        Recebe dados brutos e retorna dict com todos os indicadores.
        cotacao: dict com preco, market_cap, etc.
        dre: dict com receita, lucro, ebitda, etc.
        balanco: dict com ativo, passivo, patrimonio_liquido, etc.
        """
        indicadores = {}

        preco = cotacao.get("regularMarketPrice", 0)
        market_cap = cotacao.get("marketCap", 0)
        acoes = market_cap / preco if preco else 0

        lucro_liquido = dre.get("lucro_liquido") or 0
        receita = dre.get("receita_liquida") or 0
        ebitda = dre.get("ebitda") or 0
        ebit = dre.get("ebit") or 0

        pl = balanco.get("patrimonio_liquido") or 0
        ativo = balanco.get("ativo_total") or 0
        divida = balanco.get("divida_bruta") or 0
        caixa = balanco.get("caixa_equivalentes") or 0
        divida_liq = divida - caixa

        # --- Valuation ---
        lpa = lucro_liquido / acoes if acoes else None
        indicadores["pl"] = round(preco / lpa, 2) if lpa and lpa > 0 else None

        vpa = pl / acoes if acoes else None
        indicadores["pvp"] = round(preco / vpa, 2) if vpa and vpa > 0 else None

        ev = market_cap + divida_liq
        indicadores["ev_ebitda"] = round(ev / ebitda, 2) if ebitda and ebitda > 0 else None
        indicadores["psr"] = round(market_cap / receita, 2) if receita and receita > 0 else None
        indicadores["market_cap"] = market_cap
        indicadores["enterprise_value"] = ev

        # --- Rentabilidade ---
        indicadores["roe"] = round(lucro_liquido / pl * 100, 2) if pl else None
        indicadores["roa"] = round(lucro_liquido / ativo * 100, 2) if ativo else None
        indicadores["margem_liquida"] = round(lucro_liquido / receita * 100, 2) if receita else None
        indicadores["margem_ebitda"] = round(ebitda / receita * 100, 2) if receita and ebitda else None

        lucro_bruto = dre.get("lucro_bruto") or 0
        indicadores["margem_bruta"] = round(lucro_bruto / receita * 100, 2) if receita and lucro_bruto else None

        # --- Endividamento ---
        indicadores["divida_liq_ebitda"] = round(divida_liq / ebitda, 2) if ebitda and ebitda > 0 else None

        logger.debug(f"Indicadores calculados: {list(indicadores.keys())}")
        return indicadores
```

---

## Passo 6 - Dashboard Streamlit

### dashboard/app.py
```python
import streamlit as st

st.set_page_config(
    page_title="Mercado Financeiro BR",
    page_icon="📈",
    layout="wide"
)

st.title("Sistema de Analise de Acoes Brasileiras")
st.sidebar.success("Navegue pelas paginas acima.")
```

### dashboard/pages/1_Empresa.py
```python
import streamlit as st
import plotly.graph_objects as go
import sys
sys.path.append(".")

from src.collectors.brapi_collector import BrapiCollector
from src.processors.indicator_calculator import IndicatorCalculator

st.set_page_config(page_title="Analise de Empresa", layout="wide")
st.title("Analise de Empresa")

# Input do ticker
ticker = st.text_input("Digite o ticker (ex: PETR4, VALE3, WEGE3):", "WEGE3").upper()

if st.button("Analisar") or ticker:
    with st.spinner(f"Buscando dados de {ticker}..."):
        try:
            collector = BrapiCollector()
            dados = collector.get_cotacao(ticker)

            # Linha 1: Preco e variacao
            col1, col2, col3, col4 = st.columns(4)
            preco = dados.get("regularMarketPrice", 0)
            variacao = dados.get("regularMarketChangePercent", 0)
            market_cap = dados.get("marketCap", 0)

            col1.metric("Preco", f"R$ {preco:.2f}", f"{variacao:.2f}%")
            col2.metric("Market Cap", f"R$ {market_cap/1e9:.1f}B")
            col3.metric("Nome", dados.get("longName", ticker))
            col4.metric("Setor", dados.get("sector", "N/A"))

            st.divider()

            # Linha 2: Indicadores de valuation
            st.subheader("Valuation")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("P/L", dados.get("priceEarnings", "N/A"))
            col2.metric("P/VP", dados.get("priceToBook", "N/A"))
            col3.metric("EV/EBITDA", dados.get("enterpriseValueOverEbitda", "N/A"))
            col4.metric("PSR", dados.get("priceToSalesTrailing12Months", "N/A"))
            col5.metric("DY", f"{dados.get('dividendYield', 0):.2f}%")

            st.divider()

            # Linha 3: Rentabilidade
            st.subheader("Rentabilidade")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("ROE", f"{(dados.get('returnOnEquity', 0) or 0)*100:.2f}%")
            col2.metric("ROA", f"{(dados.get('returnOnAssets', 0) or 0)*100:.2f}%")
            col3.metric("Margem Liquida", f"{(dados.get('profitMargins', 0) or 0)*100:.2f}%")
            col4.metric("Margem Bruta", f"{(dados.get('grossMargins', 0) or 0)*100:.2f}%")

            st.divider()

            # Grafico de historico
            st.subheader("Historico de Cotacoes (1 ano)")
            historico = collector.get_historico(ticker, "1y", "1d")
            if historico:
                import pandas as pd
                df = pd.DataFrame(historico)
                df["date"] = pd.to_datetime(df["date"], unit="s")

                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df["date"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name=ticker
                ))
                fig.update_layout(
                    xaxis_rangeslider_visible=False,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao buscar dados de {ticker}: {e}")
```

---

## Passo 7 - Testes Unitarios

### tests/test_collectors/test_brapi.py
```python
import pytest
from unittest.mock import patch, MagicMock
from src.collectors.brapi_collector import BrapiCollector


@pytest.fixture
def collector():
    return BrapiCollector()


def test_get_cotacao_retorna_dados(collector):
    mock_response = {
        "results": [{
            "symbol": "PETR4",
            "regularMarketPrice": 38.50,
            "marketCap": 500000000000,
            "priceEarnings": 5.2
        }]
    }
    with patch.object(collector, "_get", return_value=mock_response):
        dados = collector.get_cotacao("PETR4")
        assert dados["symbol"] == "PETR4"
        assert dados["regularMarketPrice"] == 38.50


def test_get_cotacao_ticker_invalido(collector):
    with patch.object(collector, "_get", return_value={"results": []}):
        with pytest.raises(ValueError, match="nao encontrado"):
            collector.get_cotacao("XXXXXX")


def test_get_historico_retorna_lista(collector):
    mock_response = {
        "results": [{
            "historicalDataPrice": [
                {"date": 1700000000, "open": 38.0, "high": 39.0, "low": 37.5, "close": 38.5}
            ]
        }]
    }
    with patch.object(collector, "_get", return_value=mock_response):
        historico = collector.get_historico("PETR4", "1mo")
        assert len(historico) == 1
        assert historico[0]["close"] == 38.5
```

### tests/test_processors/test_indicators.py
```python
from src.processors.indicator_calculator import IndicatorCalculator


def test_calcula_pl():
    cotacao = {"regularMarketPrice": 20.0, "marketCap": 20_000_000_000}
    dre = {"lucro_liquido": 2_000_000_000, "receita_liquida": 10_000_000_000, "ebitda": 3_000_000_000, "ebit": 2_500_000_000, "lucro_bruto": 5_000_000_000}
    balanco = {"patrimonio_liquido": 10_000_000_000, "ativo_total": 30_000_000_000, "divida_bruta": 5_000_000_000, "caixa_equivalentes": 2_000_000_000}

    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)

    assert ind["pl"] == pytest.approx(10.0, rel=0.01)
    assert ind["roe"] == pytest.approx(20.0, rel=0.01)
    assert ind["margem_liquida"] == pytest.approx(20.0, rel=0.01)


def test_pl_nulo_quando_lucro_negativo():
    cotacao = {"regularMarketPrice": 10.0, "marketCap": 1_000_000_000}
    dre = {"lucro_liquido": -500_000_000, "receita_liquida": 5_000_000_000, "ebitda": 200_000_000, "ebit": 100_000_000, "lucro_bruto": 1_000_000_000}
    balanco = {"patrimonio_liquido": 2_000_000_000, "ativo_total": 8_000_000_000, "divida_bruta": 3_000_000_000, "caixa_equivalentes": 500_000_000}

    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)
    assert ind["pl"] is None
```

---

## Passo 8 - Scripts de Inicializacao

### scripts/setup.py
```python
"""Executa setup inicial: cria banco, tabelas e popula dados de uma empresa de teste."""
import sys
sys.path.append(".")

from src.database.connection import init_db
from src.collectors.brapi_collector import BrapiCollector
from loguru import logger

if __name__ == "__main__":
    logger.info("Iniciando setup...")
    init_db()
    logger.info("Banco criado.")

    collector = BrapiCollector()
    tickers_teste = ["WEGE3", "PETR4", "VALE3", "ITUB4", "BBAS3"]

    for ticker in tickers_teste:
        try:
            dados = collector.get_cotacao(ticker)
            logger.info(f"{ticker}: R$ {dados.get('regularMarketPrice', 'N/A')}")
        except Exception as e:
            logger.error(f"Erro em {ticker}: {e}")

    logger.info("Setup concluido. Execute: streamlit run dashboard/app.py")
```

---

## Como Executar a Fase 1

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env com tokens
cp .env.example .env
# Editar .env com seu token brapi e dados do PostgreSQL

# 3. Criar banco e tabelas
python scripts/setup.py

# 4. Rodar testes
pytest tests/ -v

# 5. Iniciar dashboard
streamlit run dashboard/app.py
```

Acesse: http://localhost:8501

---

## Criterio de Conclusao da Fase 1

A fase esta concluida quando:
1. `pytest tests/` passa sem erros
2. `streamlit run dashboard/app.py` abre o dashboard
3. Digitando `WEGE3` aparecem: preco atual, P/L, P/VP, ROE, DY e grafico de cotacoes
4. Digitando um ticker invalido aparece mensagem de erro clara
