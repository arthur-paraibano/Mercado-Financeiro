# Fase 5 - Fundos + Governanca

**Pre-requisito:** Fases 1 a 4 concluidas.

**Objetivo:** Adicionar a camada mais avancada de analise: rastrear o que os grandes fundos de investimento estao fazendo e avaliar a qualidade de governanca das empresas.

**Resultado esperado ao final:** Painel mostrando quais fundos mais compram/vendem uma acao, concentracao de fundos por empresa, e score de governanca baseado em dados da CVM.

---

## Checklist de Entregas

- [ ] Coletor CVM para carteiras de fundos (IFCA - Informe de Carteira)
- [ ] Coletor CVM para Formulario de Referencia (governanca)
- [ ] Coletor ANBIMA para dados de fundos
- [ ] Cruzamento 7: Score de Governanca e Risco
- [ ] Cruzamento 8: Movimentacoes de Fundos (Smart Money)
- [ ] Deteccao de volume anomalo vs fatos relevantes
- [ ] Pagina de Fundos no dashboard
- [ ] Pagina de Governanca no dashboard

---

## Passo 1 - Novas Tabelas

```sql
-- Carteiras dos fundos de investimento (dados CVM)
CREATE TABLE IF NOT EXISTS carteiras_fundos (
    id SERIAL PRIMARY KEY,
    cnpj_fundo VARCHAR(20) NOT NULL,
    nome_fundo VARCHAR(200),
    data_competencia DATE NOT NULL,
    ticker VARCHAR(10),
    cnpj_emissor VARCHAR(20),
    tipo_ativo VARCHAR(50),         -- 'Acoes', 'Derivativos', etc.
    quantidade BIGINT,
    valor_mercado NUMERIC(20,2),
    percentual_pl NUMERIC(8,4),     -- % do patrimonio do fundo
    UNIQUE(cnpj_fundo, data_competencia, ticker)
);

-- Dados cadastrais dos fundos
CREATE TABLE IF NOT EXISTS fundos (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(20) UNIQUE,
    nome_fantasia VARCHAR(200),
    classe VARCHAR(100),            -- 'Acoes', 'Multimercado', etc.
    gestor VARCHAR(200),
    administrador VARCHAR(200),
    patrimonio_liquido NUMERIC(20,2),
    cotistas INTEGER,
    situacao VARCHAR(50),
    atualizado_em DATE
);

-- Scores de governanca
CREATE TABLE IF NOT EXISTS governanca (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    ticker VARCHAR(10) NOT NULL,
    data_avaliacao DATE NOT NULL,
    nivel_listagem VARCHAR(20),     -- 'Novo Mercado', 'N2', 'N1', 'Tradicional', 'Bovespa Mais'
    score_governanca NUMERIC(5,2),  -- 0-100
    tag_along NUMERIC(5,2),         -- % de tag along (100 = Novo Mercado)
    free_float NUMERIC(5,2),        -- % de acoes em circulacao
    num_conselheiros INTEGER,
    conselheiros_independentes INTEGER,
    pct_independentes NUMERIC(5,2), -- % de conselheiros independentes
    troca_auditoria_anos INTEGER,   -- a cada quantos anos troca auditoria
    tem_comite_auditoria BOOLEAN,
    tem_politica_dividendos BOOLEAN,
    UNIQUE(ticker, data_avaliacao)
);

-- Fatos relevantes
CREATE TABLE IF NOT EXISTS fatos_relevantes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    ticker VARCHAR(10),
    data_entrega TIMESTAMP,
    assunto VARCHAR(500),
    categoria VARCHAR(100),
    url_documento VARCHAR(500),
    sentimento VARCHAR(10)          -- 'POSITIVO', 'NEGATIVO', 'NEUTRO' (classificar depois)
);
```

---

## Passo 2 - Coletor de Carteiras de Fundos (CVM)

### src/collectors/cvm_fundos_collector.py
```python
import io
import zipfile
import requests
import pandas as pd
from datetime import date
from loguru import logger


class CVMFundosCollector:
    """
    Coleta carteiras mensais dos fundos de investimento via CVM.
    Fonte: https://dados.cvm.gov.br/dataset/fi-doc-inf_diario
    Carteiras: https://dados.cvm.gov.br/dataset/fi-doc-cda
    """

    BASE_CDA = "https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS"
    BASE_CADASTRO = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"

    def get_cadastro_fundos(self) -> pd.DataFrame:
        """Retorna cadastro de todos os fundos registrados na CVM."""
        try:
            df = pd.read_csv(
                self.BASE_CADASTRO,
                sep=";", encoding="latin-1", dtype=str
            )
            logger.info(f"Cadastro de fundos: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Erro ao baixar cadastro de fundos: {e}")
            return pd.DataFrame()

    def get_carteira_mensal(self, ano: int, mes: int) -> pd.DataFrame:
        """
        Baixa carteiras de todos os fundos para um mes especifico.
        Retorna DataFrame com: CNPJ_FUNDO, DT_COMPTC, CD_ISIN, NM_ATIVO, VL_MERC_POS_FINAL, etc.
        """
        mes_str = f"{mes:02d}"
        url = f"{self.BASE_CDA}/cda_fi_BDR_{ano}{mes_str}.zip"

        # A CVM tem varios arquivos por tipo de ativo; acoes estao em BDR e ACOES
        urls = {
            "acoes": f"{self.BASE_CDA}/cda_fi_ACOES_{ano}{mes_str}.zip",
            "bdr":   f"{self.BASE_CDA}/cda_fi_BDR_{ano}{mes_str}.zip",
        }

        dfs = []
        for tipo, url in urls.items():
            try:
                resp = requests.get(url, timeout=120)
                if resp.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        for nome_arq in z.namelist():
                            if nome_arq.endswith(".csv"):
                                with z.open(nome_arq) as f:
                                    df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
                                    df["tipo_ativo"] = tipo
                                    dfs.append(df)
                    logger.info(f"Carteira {tipo} {ano}/{mes_str}: OK")
            except Exception as e:
                logger.warning(f"Erro carteira {tipo} {ano}/{mes_str}: {e}")

        if not dfs:
            return pd.DataFrame()

        df_total = pd.concat(dfs, ignore_index=True)
        df_total["VL_MERC_POS_FINAL"] = pd.to_numeric(df_total["VL_MERC_POS_FINAL"], errors="coerce")
        df_total["QT_POS_FINAL"]       = pd.to_numeric(df_total["QT_POS_FINAL"], errors="coerce")

        return df_total

    def filtrar_por_ticker(self, df_carteira: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Filtra carteira para mostrar apenas os fundos que tem o ticker.
        O ticker no arquivo CVM nao segue o padrao B3 direto - buscar por CD_ATIVO.
        """
        # Remover sufixo .SA e buscar parcialmente
        ticker_base = ticker.replace(".SA", "").upper()
        mask = df_carteira["CD_ATIVO"].fillna("").str.contains(ticker_base, na=False)
        return df_carteira[mask].copy()

    def ranking_fundos_por_acao(self, df_carteira: pd.DataFrame, ticker: str, top_n: int = 20) -> pd.DataFrame:
        """Retorna os N fundos com maior posicao em uma acao."""
        df_filtrado = self.filtrar_por_ticker(df_carteira, ticker)

        if df_filtrado.empty:
            return pd.DataFrame()

        df_agg = (
            df_filtrado
            .groupby("CNPJ_FUNDO")
            .agg(
                valor_total=("VL_MERC_POS_FINAL", "sum"),
                quantidade_total=("QT_POS_FINAL", "sum"),
            )
            .reset_index()
            .sort_values("valor_total", ascending=False)
            .head(top_n)
        )

        return df_agg

    def detectar_movimentacoes(
        self,
        carteira_atual: pd.DataFrame,
        carteira_anterior: pd.DataFrame,
        ticker: str,
    ) -> pd.DataFrame:
        """
        Compara dois meses de carteira para detectar fundos que compraram/venderam.
        Retorna DataFrame com: fundo, movimento, variacao_valor.
        """
        atual = self.filtrar_por_ticker(carteira_atual, ticker).set_index("CNPJ_FUNDO")["VL_MERC_POS_FINAL"]
        anterior = self.filtrar_por_ticker(carteira_anterior, ticker).set_index("CNPJ_FUNDO")["VL_MERC_POS_FINAL"]

        todos_fundos = atual.index.union(anterior.index)
        movimentos = []

        for cnpj in todos_fundos:
            val_atual = atual.get(cnpj, 0) or 0
            val_ant   = anterior.get(cnpj, 0) or 0
            variacao  = val_atual - val_ant

            if abs(variacao) > 1_000_000:  # Ignorar movimentos < R$ 1M
                movimentos.append({
                    "cnpj_fundo":    cnpj,
                    "valor_anterior": val_ant,
                    "valor_atual":    val_atual,
                    "variacao":       variacao,
                    "tipo": "COMPRA" if variacao > 0 else "VENDA",
                })

        return pd.DataFrame(movimentos).sort_values("variacao", key=abs, ascending=False)
```

---

## Passo 3 - Coletor de Governanca (CVM + B3)

### src/collectors/cvm_governanca_collector.py
```python
import requests
import pandas as pd
from loguru import logger


# Nivel de listagem da B3 implica em direitos minimos
NIVEL_LISTAGEM = {
    "NM":  {"nome": "Novo Mercado", "tag_along": 100, "free_float_min": 25, "score_base": 90},
    "N2":  {"nome": "Nivel 2",      "tag_along": 100, "free_float_min": 25, "score_base": 80},
    "N1":  {"nome": "Nivel 1",      "tag_along": 80,  "free_float_min": 25, "score_base": 65},
    "MA":  {"nome": "Bovespa Mais", "tag_along": 100, "free_float_min": 25, "score_base": 75},
    "MB":  {"nome": "Bovespa Mais 2","tag_along": 100,"free_float_min": 10, "score_base": 70},
    "DR1": {"nome": "Nivel DR1",    "tag_along": 80,  "free_float_min": 0,  "score_base": 50},
    "TR":  {"nome": "Tradicional",  "tag_along": 80,  "free_float_min": 0,  "score_base": 40},
}


class CVMGovernancaCollector:
    """Coleta informacoes de governanca corporativa."""

    BASE_CVM = "https://dados.cvm.gov.br/dados/CIA_ABERTA"

    def get_fatos_relevantes(self, cnpj: str, ano: int) -> pd.DataFrame:
        """
        Baixa fatos relevantes de uma empresa para um ano.
        """
        url = f"{self.BASE_CVM}/DOC/FRE/DADOS/fre_cia_aberta_{ano}.zip"
        try:
            import io, zipfile
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                # Arquivo de fatos relevantes dentro do ZIP
                arquivos = [f for f in z.namelist() if "fatos_relevantes" in f.lower() or "comunicado" in f.lower()]
                dfs = []
                for arq in arquivos:
                    with z.open(arq) as f:
                        df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
                        dfs.append(df)

            if not dfs:
                return pd.DataFrame()

            df_total = pd.concat(dfs, ignore_index=True)
            return df_total[df_total["CNPJ_CIA"] == cnpj] if "CNPJ_CIA" in df_total.columns else df_total

        except Exception as e:
            logger.error(f"Erro ao buscar fatos relevantes {cnpj}/{ano}: {e}")
            return pd.DataFrame()

    def calcular_score_governanca(self, ticker: str, nivel_listagem: str, free_float: float, dados_adicionais: dict = None) -> dict:
        """
        Calcula score de governanca baseado em nivel de listagem e outros fatores.
        """
        nivel = nivel_listagem.upper().strip()
        config = NIVEL_LISTAGEM.get(nivel, NIVEL_LISTAGEM["TR"])

        score = config["score_base"]
        detalhes = {
            "nivel": config["nome"],
            "tag_along": config["tag_along"],
            "score_base": score,
            "ajustes": []
        }

        # Ajuste por free float
        if free_float >= 50:
            score += 5
            detalhes["ajustes"].append(f"+5 free float alto ({free_float:.0f}%)")
        elif free_float < 15:
            score -= 5
            detalhes["ajustes"].append(f"-5 free float baixo ({free_float:.0f}%)")

        if dados_adicionais:
            # Conselho de administracao independente
            pct_indep = dados_adicionais.get("pct_independentes", 0)
            if pct_indep >= 50:
                score += 5
                detalhes["ajustes"].append(f"+5 conselho majoritariamente independente ({pct_indep:.0f}%)")
            elif pct_indep < 20:
                score -= 5
                detalhes["ajustes"].append(f"-5 poucos conselheiros independentes ({pct_indep:.0f}%)")

            # Auditoria
            anos_auditoria = dados_adicionais.get("troca_auditoria_anos", 0)
            if anos_auditoria and anos_auditoria <= 5:
                score += 3
                detalhes["ajustes"].append(f"+3 rotatividade de auditoria ({anos_auditoria} anos)")

            # Comite de auditoria
            if dados_adicionais.get("tem_comite_auditoria"):
                score += 3
                detalhes["ajustes"].append("+3 possui comite de auditoria")

            # Politica de dividendos
            if dados_adicionais.get("tem_politica_dividendos"):
                score += 2
                detalhes["ajustes"].append("+2 politica de dividendos formalizada")

        score = max(0, min(100, score))
        detalhes["score_final"] = score

        return detalhes
```

---

## Passo 4 - Analisador de Smart Money

### src/processors/smart_money_analyzer.py
```python
import pandas as pd
from typing import Dict, List
from loguru import logger
from src.collectors.cvm_fundos_collector import CVMFundosCollector


class SmartMoneyAnalyzer:
    """
    Analisa movimentacoes de grandes fundos para identificar tendencias.
    Conceito de 'smart money': seguir o que gestores experientes estao fazendo.
    """

    # Gestoras consideradas 'smart money' (adicionar conforme necessario)
    GESTORAS_REFERENCIA = [
        "DYNAMO", "SPX", "VERDE", "GAP", "KAPITALO",
        "CONSTELLATION", "MOAT", "SQUADRA", "GUEPARDO",
    ]

    def __init__(self):
        self.cvm_fundos = CVMFundosCollector()

    def analisar_concentracao(self, df_carteira: pd.DataFrame, ticker: str) -> dict:
        """
        Analisa concentracao de fundos em uma acao.
        Alta concentracao = risco de venda em cascata.
        """
        df_ticker = self.cvm_fundos.filtrar_por_ticker(df_carteira, ticker)

        if df_ticker.empty:
            return {"ticker": ticker, "num_fundos": 0, "risco_concentracao": "DESCONHECIDO"}

        num_fundos       = df_ticker["CNPJ_FUNDO"].nunique()
        valor_total      = df_ticker["VL_MERC_POS_FINAL"].sum()
        top5_valor       = df_ticker.nlargest(5, "VL_MERC_POS_FINAL")["VL_MERC_POS_FINAL"].sum()
        concentracao_top5 = (top5_valor / valor_total * 100) if valor_total > 0 else 0

        # Nivel de risco por concentracao
        if concentracao_top5 > 70:
            risco = "ALTO"     # 5 fundos dominam >70% da posicao
        elif concentracao_top5 > 50:
            risco = "MEDIO"
        else:
            risco = "BAIXO"

        return {
            "ticker":              ticker,
            "num_fundos":          num_fundos,
            "valor_total_fundos":  valor_total,
            "concentracao_top5_pct": round(concentracao_top5, 2),
            "risco_concentracao":  risco,
        }

    def detectar_smart_money_entrando(
        self,
        carteira_atual: pd.DataFrame,
        carteira_anterior: pd.DataFrame,
        tickers: List[str],
        cadastro_fundos: pd.DataFrame = None,
    ) -> pd.DataFrame:
        """
        Para cada ticker, detecta se gestoras de referencia aumentaram posicao.
        Retorna DataFrame com tickers onde smart money esta comprando.
        """
        resultados = []

        for ticker in tickers:
            movimentos = self.cvm_fundos.detectar_movimentacoes(
                carteira_atual, carteira_anterior, ticker
            )

            if movimentos.empty:
                continue

            compras = movimentos[movimentos["tipo"] == "COMPRA"]
            vendas  = movimentos[movimentos["tipo"] == "VENDA"]

            # Enriquecer com nome da gestora se tiver cadastro
            if cadastro_fundos is not None and not compras.empty:
                compras = compras.merge(
                    cadastro_fundos[["CNPJ_FUNDO", "DENOM_SOCIAL", "NM_GESTOR"]].drop_duplicates(),
                    left_on="cnpj_fundo", right_on="CNPJ_FUNDO", how="left"
                )

                # Verificar se alguma gestora de referencia esta comprando
                smart_comprando = []
                for gestora in self.GESTORAS_REFERENCIA:
                    mask = compras["NM_GESTOR"].fillna("").str.upper().str.contains(gestora)
                    if mask.any():
                        smart_comprando.append(gestora)

                if smart_comprando:
                    resultados.append({
                        "ticker":         ticker,
                        "smart_money":    ", ".join(smart_comprando),
                        "valor_compras":  compras["variacao"].sum(),
                        "num_compradores": len(compras),
                        "num_vendedores":  len(vendas),
                        "saldo":          compras["variacao"].sum() + vendas["variacao"].sum(),
                    })

        return pd.DataFrame(resultados).sort_values("valor_compras", ascending=False) if resultados else pd.DataFrame()
```

---

## Passo 5 - Paginas do Dashboard

### dashboard/pages/8_Fundos.py
```python
import streamlit as st
import plotly.express as px
import pandas as pd
import sys
sys.path.append(".")

from src.collectors.cvm_fundos_collector import CVMFundosCollector
from src.processors.smart_money_analyzer import SmartMoneyAnalyzer
from datetime import date

st.set_page_config(page_title="Analise de Fundos", layout="wide")
st.title("Fundos de Investimento - Smart Money")

ticker = st.text_input("Ticker para analisar:", "WEGE3").upper()

col1, col2 = st.columns(2)
with col1:
    ano = st.number_input("Ano:", min_value=2020, max_value=date.today().year, value=date.today().year)
with col2:
    mes = st.number_input("Mes:", min_value=1, max_value=12, value=max(1, date.today().month - 1))

if st.button("Analisar Fundos"):
    cvm = CVMFundosCollector()
    analyzer = SmartMoneyAnalyzer()

    with st.spinner("Baixando carteiras da CVM (pode demorar alguns minutos)..."):
        carteira = cvm.get_carteira_mensal(ano, mes)
        cadastro = cvm.get_cadastro_fundos()

    if not carteira.empty:
        # Concentracao
        concentracao = analyzer.analisar_concentracao(carteira, ticker)

        col1, col2, col3 = st.columns(3)
        col1.metric("Fundos com posicao", concentracao.get("num_fundos", 0))
        col2.metric("Concentracao Top 5", f"{concentracao.get('concentracao_top5_pct', 0):.1f}%")
        col3.metric("Risco Concentracao", concentracao.get("risco_concentracao", "N/A"))

        st.divider()

        # Top 20 fundos por posicao
        top_fundos = cvm.ranking_fundos_por_acao(carteira, ticker, top_n=20)
        if not top_fundos.empty:
            # Enriquecer com nomes
            if not cadastro.empty and "CNPJ_FUNDO" in cadastro.columns:
                top_fundos = top_fundos.merge(
                    cadastro[["CNPJ_FUNDO", "DENOM_SOCIAL"]].drop_duplicates(),
                    on="CNPJ_FUNDO", how="left"
                )

            st.subheader(f"Top 20 Fundos com maior posicao em {ticker}")
            top_fundos["valor_total_MM"] = top_fundos["valor_total"] / 1_000_000
            fig = px.bar(
                top_fundos.head(15),
                x="DENOM_SOCIAL" if "DENOM_SOCIAL" in top_fundos.columns else "CNPJ_FUNDO",
                y="valor_total_MM",
                title=f"Posicao em {ticker} por Fundo (R$ Milhoes)",
                labels={"valor_total_MM": "R$ Milhoes"}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Nao foi possivel baixar os dados das carteiras.")


### dashboard/pages/9_Governanca.py
```

### dashboard/pages/9_Governanca.py
```python
import streamlit as st
import pandas as pd
import sys
sys.path.append(".")

from src.collectors.cvm_governanca_collector import CVMGovernancaCollector

st.set_page_config(page_title="Governanca Corporativa", layout="wide")
st.title("Governanca Corporativa")

# Mapeamento simplificado de niveis de listagem
EMPRESAS_NIVEL = {
    "WEGE3":  "NM", "RDOR3":  "NM", "TOTS3":  "NM",
    "ITUB4":  "NM", "BBAS3":  "NM", "VALE3":  "NM",
    "PETR4":  "TR", "BBDC4":  "N1", "GGBR4":  "N1",
    "CMIG4":  "N1", "USIM5":  "N1", "CSNA3":  "TR",
}

tickers = st.multiselect(
    "Selecione empresas para comparar:",
    list(EMPRESAS_NIVEL.keys()),
    default=["WEGE3", "ITUB4", "PETR4", "CMIG4"]
)

if tickers:
    cvm = CVMGovernancaCollector()
    resultados = []

    for ticker in tickers:
        nivel = EMPRESAS_NIVEL.get(ticker, "TR")
        detalhe = cvm.calcular_score_governanca(
            ticker=ticker,
            nivel_listagem=nivel,
            free_float=30.0,  # placeholder - idealmente buscar da CVM
        )
        resultados.append({
            "Ticker":        ticker,
            "Nivel":         detalhe["nivel"],
            "Tag Along":     f"{detalhe['tag_along']}%",
            "Score":         detalhe["score_final"],
            "Ajustes":       " | ".join(detalhe["ajustes"]) if detalhe["ajustes"] else "-",
        })

    df = pd.DataFrame(resultados).sort_values("Score", ascending=False)

    import plotly.express as px
    fig = px.bar(df, x="Ticker", y="Score", color="Score",
                 color_continuous_scale="RdYlGn", range_color=[0, 100],
                 title="Score de Governanca por Empresa")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df, use_container_width=True)

    st.caption("""
    **Legenda de Niveis:**
    - **Novo Mercado (NM):** Mais alto nivel. 100% tag along, 1 acao = 1 voto.
    - **Nivel 2 (N2):** Tag along 100%, acoes preferenciais com direitos especiais.
    - **Nivel 1 (N1):** Obrigacoes adicionais de divulgacao. Tag along 80%.
    - **Tradicional (TR):** Regras minimas legais. Tag along 80% para ON.
    """)
```

---

## Criterio de Conclusao da Fase 5

A fase esta concluida quando:
1. `CVMFundosCollector.get_carteira_mensal()` baixa dados sem erros
2. Pagina de Fundos exibe top 20 fundos de uma acao
3. Score de governanca e calculado corretamente (Novo Mercado > Tradicional)
4. `SmartMoneyAnalyzer.detectar_smart_money_entrando()` retorna resultados quando ha movimentacoes
