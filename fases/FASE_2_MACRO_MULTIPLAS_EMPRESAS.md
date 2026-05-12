# Fase 2 - Dados Macro + Multiplas Empresas

**Pre-requisito:** Fase 1 concluida e funcionando.

**Objetivo:** Expandir o sistema para todas as empresas do Ibovespa, adicionar dados macroeconomicos do BCB/IBGE, classificar empresas por setor e criar comparacao setorial no dashboard.

**Resultado esperado ao final:** Painel com todas as ~90 empresas do Ibovespa, grafico de distribuicao setorial, comparacao de indicadores entre empresas do mesmo setor e painel de indicadores macro (SELIC, IPCA, Cambio).

---

## Checklist de Entregas

- [ ] Coletor BCB implementado (SELIC, IPCA, PTAX, Focus)
- [ ] Coletor IBGE implementado (PIB, producao industrial)
- [ ] Coletor B3 implementado (composicao do Ibovespa)
- [ ] Script de carga de todas as empresas do Ibovespa
- [ ] Classificacao setorial no banco de dados
- [ ] Cache com dicionario em memoria (sem Redis por enquanto)
- [ ] Pagina de Visao Geral do mercado no dashboard
- [ ] Pagina de Comparacao Setorial no dashboard
- [ ] Pagina de Indicadores Macro no dashboard

---

## Passo 1 - Adicionar Tabelas no Banco

### Novas tabelas - adicionar em schema.sql
```sql
-- Indicadores macroeconomicos
CREATE TABLE IF NOT EXISTS indicadores_macro (
    id SERIAL PRIMARY KEY,
    indicador VARCHAR(50) NOT NULL,  -- 'SELIC', 'IPCA', 'PTAX', 'PIB', etc.
    data DATE NOT NULL,
    valor NUMERIC(15,6),
    fonte VARCHAR(50),               -- 'BCB', 'IBGE', etc.
    UNIQUE(indicador, data)
);

-- Composicao de indices (Ibovespa, IBrX, etc.)
CREATE TABLE IF NOT EXISTS composicao_indice (
    id SERIAL PRIMARY KEY,
    indice VARCHAR(20) NOT NULL,     -- 'IBOV', 'IBRX100', etc.
    ticker VARCHAR(10) NOT NULL,
    peso NUMERIC(8,4),
    data_referencia DATE NOT NULL,
    UNIQUE(indice, ticker, data_referencia)
);

-- Setores e classificacao
CREATE TABLE IF NOT EXISTS setores (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE,
    setor VARCHAR(100),
    subsetor VARCHAR(100),
    segmento VARCHAR(100)
);

-- Associar empresa ao setor
ALTER TABLE empresas ADD COLUMN IF NOT EXISTS setor_id INTEGER REFERENCES setores(id);
ALTER TABLE empresas ADD COLUMN IF NOT EXISTS tipo_acao VARCHAR(5);  -- ON, PN, UNT, etc.
ALTER TABLE empresas ADD COLUMN IF NOT EXISTS volume_medio_diario NUMERIC(20,2);
```

---

## Passo 2 - Coletor do Banco Central

### src/collectors/bcb_collector.py
```python
import time
import requests
import pandas as pd
from datetime import date, timedelta
from loguru import logger
from config.settings import CVM_DELAY  # reutiliza delay configuravel


# Codigos das series no SGS do BCB
SERIES_SGS = {
    "SELIC_META":      432,
    "SELIC_EFETIVA":   11,
    "IPCA_MENSAL":     433,
    "IPCA_ACUM_12M":   13522,
    "IGPM_MENSAL":     189,
    "PTAX_DOLAR":      1,
    "CDI":             4389,
    "PIB_MENSAL":      4380,
    "DESEMPREGO":      24369,
    "PRODUCAO_IND":    21859,
}


class BCBCollector:
    """Coleta dados macroeconomicos do Banco Central do Brasil."""

    BASE_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
    BASE_PTAX = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"
    BASE_EXPECTATIVAS = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata"

    def _get_sgs(self, codigo: int, inicio: str, fim: str = None) -> pd.DataFrame:
        """Busca serie temporal do SGS."""
        if fim is None:
            fim = date.today().strftime("%d/%m/%Y")

        url = self.BASE_SGS.format(codigo=codigo)
        params = {
            "formato": "json",
            "dataInicial": inicio,
            "dataFinal": fim,
        }
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            time.sleep(CVM_DELAY)
            data = resp.json()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)
            df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
            return df
        except Exception as e:
            logger.error(f"Erro SGS serie {codigo}: {e}")
            return pd.DataFrame()

    def get_selic(self, inicio: str = "01/01/2010") -> pd.DataFrame:
        """Retorna serie historica da SELIC meta."""
        return self._get_sgs(SERIES_SGS["SELIC_META"], inicio)

    def get_ipca(self, inicio: str = "01/01/2010") -> pd.DataFrame:
        """Retorna IPCA mensal."""
        return self._get_sgs(SERIES_SGS["IPCA_MENSAL"], inicio)

    def get_ipca_acumulado_12m(self, inicio: str = "01/01/2010") -> pd.DataFrame:
        return self._get_sgs(SERIES_SGS["IPCA_ACUM_12M"], inicio)

    def get_cambio_dolar(self, inicio: str = "01/01/2020") -> pd.DataFrame:
        """Retorna cotacao do dolar (PTAX venda)."""
        return self._get_sgs(SERIES_SGS["PTAX_DOLAR"], inicio)

    def get_cdi(self, inicio: str = "01/01/2010") -> pd.DataFrame:
        return self._get_sgs(SERIES_SGS["CDI"], inicio)

    def get_multiplas_series(self, nomes: list, inicio: str = "01/01/2020") -> dict:
        """
        Baixa multiplas series de uma vez.
        nomes: lista de chaves de SERIES_SGS, ex: ["SELIC_META", "IPCA_MENSAL"]
        """
        resultado = {}
        for nome in nomes:
            if nome not in SERIES_SGS:
                logger.warning(f"Serie desconhecida: {nome}")
                continue
            resultado[nome] = self._get_sgs(SERIES_SGS[nome], inicio)
        return resultado

    def get_expectativas_focus(self, indicador: str = "IPCA", limite: int = 12) -> pd.DataFrame:
        """
        Retorna expectativas de mercado do Boletin Focus.
        indicador: 'IPCA', 'IGP-M', 'Selic', 'PIB Total', 'Cambio'
        """
        url = f"{self.BASE_EXPECTATIVAS}/ExpectativasMercadoAnuais"
        params = {
            "$filter": f"Indicador eq '{indicador}'",
            "$top": limite,
            "$orderby": "Data desc",
            "$format": "json",
            "$select": "Indicador,Data,Ano,Mediana,Media,Minimo,Maximo",
        }
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json().get("value", [])
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Erro Focus {indicador}: {e}")
            return pd.DataFrame()
```

---

## Passo 3 - Coletor do IBGE

### src/collectors/ibge_collector.py
```python
import requests
import pandas as pd
from loguru import logger


class IBGECollector:
    """Coleta dados economicos setoriais do IBGE."""

    BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

    # Codigos dos agregados IBGE
    AGREGADOS = {
        "IPCA_GRUPOS":        7060,   # IPCA por grupo de despesa
        "PIB_TRIMESTRAL":     5932,   # PIB trimestral
        "PRODUCAO_INDUSTRIA": 3653,   # Producao industrial mensal
        "COMERCIO_VAREJO":    8880,   # Pesquisa Mensal do Comercio
        "SERVICOS":           6442,   # Pesquisa Mensal de Servicos
    }

    def _get(self, agregado: int, periodos: str, variavel: int, localidade: str = "N1[all]") -> pd.DataFrame:
        url = f"{self.BASE}/{agregado}/periodos/{periodos}/variaveis/{variavel}"
        params = {"localidades": localidade}
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return pd.DataFrame()

            rows = []
            for serie in data:
                for periodo, valor in serie.get("resultados", [{}])[0].get("series", [{}])[0].get("serie", {}).items():
                    rows.append({"periodo": periodo, "valor": valor, "variavel": serie.get("variavel")})
            return pd.DataFrame(rows)
        except Exception as e:
            logger.error(f"Erro IBGE agregado {agregado}: {e}")
            return pd.DataFrame()

    def get_pib_trimestral(self, ultimos: int = 20) -> pd.DataFrame:
        """PIB trimestral - variacao percentual."""
        return self._get(self.AGREGADOS["PIB_TRIMESTRAL"], f"-{ultimos}", 6561)

    def get_producao_industrial(self, ultimos: int = 24) -> pd.DataFrame:
        """Indice de producao industrial mensal."""
        return self._get(self.AGREGADOS["PRODUCAO_INDUSTRIA"], f"-{ultimos}", 3135)

    def get_comercio_varejo(self, ultimos: int = 24) -> pd.DataFrame:
        """Volume de vendas no comercio varejista."""
        return self._get(self.AGREGADOS["COMERCIO_VAREJO"], f"-{ultimos}", 7168)
```

---

## Passo 4 - Coletor B3 (Composicao do Ibovespa)

### src/collectors/b3_collector.py
```python
import requests
import pandas as pd
from loguru import logger


class B3Collector:
    """Coleta dados publicos da B3."""

    def get_composicao_ibovespa(self) -> pd.DataFrame:
        """
        Retorna composicao atual do Ibovespa via API da B3.
        Retorna DataFrame com colunas: ticker, nome, tipo, qtd_teorica, peso
        """
        url = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQk9WIiwic2VnbWVudCI6IjEifQ=="
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            acoes = data.get("results", [])
            df = pd.DataFrame(acoes)

            # Renomear colunas
            rename = {
                "cod": "ticker",
                "asset": "nome",
                "type": "tipo",
                "theoricalQty": "qtd_teorica",
                "part": "peso",
            }
            df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
            return df
        except Exception as e:
            logger.error(f"Erro ao buscar composicao do Ibovespa: {e}")
            return pd.DataFrame()

    def get_cotacoes_historicas_arquivo(self, ano: int) -> pd.DataFrame:
        """
        Baixa arquivo anual de cotacoes historicas da B3.
        Retorna DataFrame com todas as cotacoes do ano.
        """
        import io, zipfile
        url = f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{ano}.ZIP"
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                nome = z.namelist()[0]
                with z.open(nome) as f:
                    conteudo = f.read().decode("latin-1")

            # Layout fixo do arquivo COTAHIST
            colunas = {
                "tipo_registro":   (0, 2),
                "data_pregao":     (2, 10),
                "cod_bdi":         (10, 12),
                "ticker":          (12, 24),
                "tipo_mercado":    (24, 27),
                "nome_empresa":    (27, 39),
                "especificacao":   (39, 49),
                "preco_abertura":  (56, 69),
                "preco_maximo":    (69, 82),
                "preco_minimo":    (82, 95),
                "preco_medio":     (95, 108),
                "preco_fechamento":(108, 121),
                "volume":          (170, 188),
                "num_negocios":    (152, 170),
            }

            rows = []
            for linha in conteudo.split("\n"):
                if linha.startswith("01"):  # tipo 01 = mercado a vista
                    row = {col: linha[ini:fim].strip() for col, (ini, fim) in colunas.items()}
                    rows.append(row)

            df = pd.DataFrame(rows)
            df["data_pregao"] = pd.to_datetime(df["data_pregao"], format="%Y%m%d")

            # Converter precos (divisor de 100 pois vem sem casas decimais)
            for col in ["preco_abertura", "preco_maximo", "preco_minimo", "preco_medio", "preco_fechamento"]:
                df[col] = pd.to_numeric(df[col], errors="coerce") / 100

            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
            df["ticker"] = df["ticker"].str.strip()

            return df
        except Exception as e:
            logger.error(f"Erro ao baixar cotacoes historicas {ano}: {e}")
            return pd.DataFrame()
```

---

## Passo 5 - Script de Carga de Empresas

### scripts/carregar_ibovespa.py
```python
"""Carrega todas as empresas do Ibovespa no banco."""
import sys
sys.path.append(".")

import time
from loguru import logger
from src.collectors.b3_collector import B3Collector
from src.collectors.brapi_collector import BrapiCollector
from src.database.connection import SessionLocal

def carregar_empresas_ibovespa():
    b3 = B3Collector()
    brapi = BrapiCollector()
    db = SessionLocal()

    logger.info("Buscando composicao do Ibovespa...")
    composicao = b3.get_composicao_ibovespa()

    if composicao.empty:
        logger.error("Nao foi possivel obter composicao do Ibovespa.")
        return

    tickers = composicao["ticker"].tolist()
    logger.info(f"{len(tickers)} tickers encontrados no Ibovespa.")

    sucessos, erros = 0, 0
    for ticker in tickers:
        try:
            dados = brapi.get_cotacao(ticker)
            logger.info(f"[{ticker}] {dados.get('longName', 'N/A')} - R$ {dados.get('regularMarketPrice', 'N/A')}")
            sucessos += 1
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"[{ticker}] Erro: {e}")
            erros += 1

    logger.info(f"Concluido: {sucessos} ok, {erros} erros.")

if __name__ == "__main__":
    carregar_empresas_ibovespa()
```

---

## Passo 6 - Paginas do Dashboard

### dashboard/pages/2_Visao_Geral.py
```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
sys.path.append(".")

from src.collectors.brapi_collector import BrapiCollector
from src.collectors.b3_collector import B3Collector

st.set_page_config(page_title="Visao Geral do Mercado", layout="wide")
st.title("Visao Geral - Mercado Brasileiro")

@st.cache_data(ttl=300)
def carregar_dados_ibovespa():
    b3 = B3Collector()
    return b3.get_composicao_ibovespa()

composicao = carregar_dados_ibovespa()

if not composicao.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Composicao por Tipo")
        if "tipo" in composicao.columns:
            fig = px.pie(composicao, names="tipo", title="Distribuicao por Tipo de Acao")
            st.plotly_chart(fig)

    with col2:
        st.subheader("Top 20 Maiores Pesos")
        top20 = composicao.nlargest(20, "peso") if "peso" in composicao.columns else composicao.head(20)
        if "ticker" in top20.columns and "peso" in top20.columns:
            fig = px.bar(top20, x="ticker", y="peso", title="Top 20 Ibovespa por Peso")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Todas as Empresas do Ibovespa")
    st.dataframe(composicao, use_container_width=True)
```

### dashboard/pages/3_Macro.py
```python
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
sys.path.append(".")

from src.collectors.bcb_collector import BCBCollector

st.set_page_config(page_title="Indicadores Macro", layout="wide")
st.title("Indicadores Macroeconomicos")

bcb = BCBCollector()

@st.cache_data(ttl=3600)
def carregar_macro():
    return {
        "selic":   bcb.get_selic("01/01/2015"),
        "ipca":    bcb.get_ipca("01/01/2015"),
        "cambio":  bcb.get_cambio_dolar("01/01/2020"),
        "ipca12m": bcb.get_ipca_acumulado_12m("01/01/2015"),
    }

with st.spinner("Carregando dados do Banco Central..."):
    macro = carregar_macro()

# Metricas atuais
selic_atual = macro["selic"]["valor"].iloc[-1] if not macro["selic"].empty else None
ipca_atual  = macro["ipca12m"]["valor"].iloc[-1] if not macro["ipca12m"].empty else None
cambio_atual = macro["cambio"]["valor"].iloc[-1] if not macro["cambio"].empty else None

col1, col2, col3 = st.columns(3)
col1.metric("SELIC (meta)", f"{selic_atual:.2f}% a.a." if selic_atual else "N/A")
col2.metric("IPCA Acum. 12M", f"{ipca_atual:.2f}%" if ipca_atual else "N/A")
col3.metric("Dolar (PTAX)", f"R$ {cambio_atual:.4f}" if cambio_atual else "N/A")

st.divider()

# Graficos
col1, col2 = st.columns(2)

with col1:
    if not macro["selic"].empty:
        fig = px.line(macro["selic"], x="data", y="valor", title="SELIC Meta (% a.a.)")
        fig.update_traces(line_color="#1f77b4")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if not macro["ipca"].empty:
        fig = px.bar(macro["ipca"].tail(24), x="data", y="valor", title="IPCA Mensal (% m.m.)")
        st.plotly_chart(fig, use_container_width=True)

if not macro["cambio"].empty:
    fig = px.line(macro["cambio"], x="data", y="valor", title="Cotacao do Dolar (R$)")
    fig.update_traces(line_color="#2ca02c")
    st.plotly_chart(fig, use_container_width=True)

# Expectativas Focus
st.subheader("Expectativas Focus (mercado)")
col1, col2 = st.columns(2)

with col1:
    focus_ipca = bcb.get_expectativas_focus("IPCA")
    if not focus_ipca.empty:
        st.dataframe(focus_ipca[["Ano", "Mediana", "Minimo", "Maximo"]].head(5))
        st.caption("Projecoes de IPCA pelo mercado (Focus/BCB)")

with col2:
    focus_selic = bcb.get_expectativas_focus("Selic")
    if not focus_selic.empty:
        st.dataframe(focus_selic[["Ano", "Mediana", "Minimo", "Maximo"]].head(5))
        st.caption("Projecoes de SELIC pelo mercado (Focus/BCB)")
```

### dashboard/pages/4_Comparacao_Setorial.py
```python
import streamlit as st
import plotly.express as px
import pandas as pd
import sys
sys.path.append(".")

from src.collectors.brapi_collector import BrapiCollector

st.set_page_config(page_title="Comparacao Setorial", layout="wide")
st.title("Comparacao Setorial")

# Mapeamento setorial simplificado (tickers do Ibovespa por setor)
SETORES = {
    "Petroleo e Gas":     ["PETR3", "PETR4", "PRIO3", "RECV3"],
    "Mineracao":          ["VALE3", "CSNA3", "GGBR4", "USIM5"],
    "Financeiro":         ["ITUB4", "BBAS3", "BBDC4", "SANB11", "BPAC11"],
    "Energia Eletrica":   ["EGIE3", "ENGI11", "CPFE3", "TAEE11", "CMIG4"],
    "Varejo":             ["MGLU3", "VIIA3", "LREN3", "AMER3"],
    "Agronegocio":        ["SLCE3", "BEEF3", "SMTO3", "AGRO3"],
    "Saude":              ["RDOR3", "HAPV3", "GNDI3", "FLRY3"],
    "Telecomunicacoes":   ["VIVT3", "TIMS3"],
    "Papel e Celulose":   ["SUZB3", "KLBN11"],
    "Tecnologia":         ["TOTVS3", "LWSA3", "INTB3"],
}

setor_selecionado = st.selectbox("Selecione o setor:", list(SETORES.keys()))
tickers = SETORES[setor_selecionado]

indicador = st.selectbox("Indicador para comparar:", [
    "P/L (priceEarnings)",
    "P/VP (priceToBook)",
    "DY (dividendYield)",
    "ROE (returnOnEquity)",
    "Margem Liquida (profitMargins)",
])

campo_map = {
    "P/L (priceEarnings)":          "priceEarnings",
    "P/VP (priceToBook)":           "priceToBook",
    "DY (dividendYield)":           "dividendYield",
    "ROE (returnOnEquity)":         "returnOnEquity",
    "Margem Liquida (profitMargins)": "profitMargins",
}

campo = campo_map[indicador]

if st.button("Comparar"):
    brapi = BrapiCollector()
    dados = []

    progress = st.progress(0)
    for i, ticker in enumerate(tickers):
        try:
            cotacao = brapi.get_cotacao(ticker)
            valor = cotacao.get(campo)
            if valor is not None:
                # ROE e margem vem em decimal, converter para %
                if campo in ["returnOnEquity", "profitMargins", "dividendYield"]:
                    valor = valor * 100
                dados.append({"ticker": ticker, "valor": round(valor, 2)})
        except Exception as e:
            st.warning(f"{ticker}: {e}")
        progress.progress((i + 1) / len(tickers))

    if dados:
        df = pd.DataFrame(dados).sort_values("valor", ascending=False)

        fig = px.bar(
            df, x="ticker", y="valor",
            title=f"{indicador} - {setor_selecionado}",
            color="valor",
            color_continuous_scale="RdYlGn"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Estatisticas do setor
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mediana", f"{df['valor'].median():.2f}")
        col2.metric("Media", f"{df['valor'].mean():.2f}")
        col3.metric("Maximo", f"{df['valor'].max():.2f} ({df.loc[df['valor'].idxmax(), 'ticker']})")
        col4.metric("Minimo", f"{df['valor'].min():.2f} ({df.loc[df['valor'].idxmin(), 'ticker']})")

        st.dataframe(df, use_container_width=True)
```

---

## Criterio de Conclusao da Fase 2

A fase esta concluida quando:
1. Pagina "Visao Geral" exibe lista completa do Ibovespa
2. Pagina "Macro" exibe SELIC, IPCA e Cambio com graficos historicos
3. Pagina "Comparacao Setorial" permite comparar indicadores entre empresas
4. `scripts/carregar_ibovespa.py` roda sem erros criticos
