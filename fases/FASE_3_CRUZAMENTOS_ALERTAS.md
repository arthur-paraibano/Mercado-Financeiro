# Fase 3 - Cruzamentos e Alertas

**Pre-requisito:** Fases 1 e 2 concluidas.

**Objetivo:** Implementar o motor de cruzamento de dados que gera insights automaticos. O sistema deve detectar empresas com prejuizo, endividamento perigoso, dividendos insustentaveis e setores pressionados pelo cenario macro.

**Resultado esperado ao final:** Painel de alertas mostrando automaticamente quais empresas tem sinais de alerta com descricao do problema encontrado.

---

## Checklist de Entregas

- [ ] Cruzamento 1: Saude Financeira (prejuizo, caixa, endividamento)
- [ ] Cruzamento 2: Divergencia Lucro vs Caixa
- [ ] Cruzamento 3: Valuation vs Pares do Setor
- [ ] Cruzamento 4: Impacto Macro nos Setores
- [ ] Cruzamento 5: Consistencia e Sustentabilidade de Dividendos
- [ ] Motor de alertas com niveis de severidade
- [ ] Tabela de alertas no banco de dados
- [ ] Pagina de Alertas no dashboard

---

## Passo 1 - Tabela de Alertas no Banco

```sql
CREATE TABLE IF NOT EXISTS alertas (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    ticker VARCHAR(10),
    tipo VARCHAR(50) NOT NULL,           -- 'SAUDE_FINANCEIRA', 'DIVIDENDO_INSUSTENTAVEL', etc.
    severidade VARCHAR(10) NOT NULL,     -- 'CRITICO', 'ALTO', 'MEDIO', 'INFO'
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    valor_detectado NUMERIC(15,4),
    threshold_usado NUMERIC(15,4),
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT NOW(),
    resolvido_em TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alertas_ticker ON alertas(ticker);
CREATE INDEX IF NOT EXISTS idx_alertas_tipo ON alertas(tipo);
CREATE INDEX IF NOT EXISTS idx_alertas_severidade ON alertas(severidade, ativo);
```

---

## Passo 2 - Modelos de Dados

### src/models/alert.py
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Alerta:
    ticker: str
    tipo: str
    severidade: str       # 'CRITICO', 'ALTO', 'MEDIO', 'INFO'
    titulo: str
    descricao: str
    valor_detectado: Optional[float] = None
    threshold_usado: Optional[float] = None
    criado_em: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"[{self.severidade}] {self.ticker} - {self.titulo}"
```

---

## Passo 3 - Cruzamento 1: Saude Financeira

### src/processors/cross_analyzer.py
```python
from typing import List, Optional
from src.models.alert import Alerta


class CrossAnalyzer:
    """Motor de cruzamento de dados para gerar alertas e insights."""

    # --- Thresholds configuráveis ---
    DIVIDA_EBITDA_CRITICO  = 5.0
    DIVIDA_EBITDA_ALTO     = 3.5
    DIVIDA_EBITDA_MEDIO    = 2.5
    MARGEM_LIQUIDA_MINIMA  = -5.0   # % - abaixo disso é alerta critico
    COBERTURA_JUROS_MINIMA = 1.5    # EBIT / Despesa financeira
    PAYOUT_MAXIMO          = 90.0   # % - acima disso dividendo e risco
    DY_MINIMO_ATRATIVO     = 1.0    # DY deve ser pelo menos 1x a SELIC p/ ser atrativo

    def analisar_saude_financeira(self, ticker: str, dre: dict, balanco: dict, fluxo: dict) -> List[Alerta]:
        """
        Cruzamento 1: Detecta problemas de saude financeira.
        Entradas:
          dre:     {lucro_liquido, receita_liquida, ebitda, ebit, resultado_financeiro}
          balanco: {patrimonio_liquido, divida_bruta, caixa_equivalentes, ativo_total}
          fluxo:   {fcf_operacional, fcf_livre, capex}
        """
        alertas = []

        lucro    = dre.get("lucro_liquido") or 0
        receita  = dre.get("receita_liquida") or 1
        ebitda   = dre.get("ebitda") or 0
        ebit     = dre.get("ebit") or 0
        desp_fin = abs(dre.get("resultado_financeiro") or 0)

        divida_bruta = balanco.get("divida_bruta") or 0
        caixa        = balanco.get("caixa_equivalentes") or 0
        divida_liq   = divida_bruta - caixa
        pl           = balanco.get("patrimonio_liquido") or 1

        fcf_op  = fluxo.get("fcf_operacional") or 0
        fcf_liv = fluxo.get("fcf_livre") or 0

        margem_liq = (lucro / receita) * 100

        # 1.1 Prejuizo liquido
        if lucro < 0:
            severidade = "CRITICO" if margem_liq < self.MARGEM_LIQUIDA_MINIMA else "ALTO"
            alertas.append(Alerta(
                ticker=ticker,
                tipo="PREJUIZO_LIQUIDO",
                severidade=severidade,
                titulo=f"Prejuizo liquido de R$ {abs(lucro)/1e6:.1f}M",
                descricao=f"Margem liquida de {margem_liq:.1f}%. Empresa esta consumindo patrimonio.",
                valor_detectado=lucro,
            ))

        # 1.2 Endividamento excessivo
        if ebitda and ebitda > 0:
            dliq_ebitda = divida_liq / ebitda
            if dliq_ebitda > self.DIVIDA_EBITDA_CRITICO:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="ENDIVIDAMENTO_CRITICO",
                    severidade="CRITICO",
                    titulo=f"Divida Liq/EBITDA: {dliq_ebitda:.1f}x (critico > {self.DIVIDA_EBITDA_CRITICO}x)",
                    descricao="Nivel de endividamento muito elevado. Risco de insolvencia se EBITDA cair.",
                    valor_detectado=dliq_ebitda,
                    threshold_usado=self.DIVIDA_EBITDA_CRITICO,
                ))
            elif dliq_ebitda > self.DIVIDA_EBITDA_ALTO:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="ENDIVIDAMENTO_ALTO",
                    severidade="ALTO",
                    titulo=f"Divida Liq/EBITDA: {dliq_ebitda:.1f}x (alto > {self.DIVIDA_EBITDA_ALTO}x)",
                    descricao="Endividamento elevado. Monitorar evolucao e capacidade de refinanciamento.",
                    valor_detectado=dliq_ebitda,
                    threshold_usado=self.DIVIDA_EBITDA_ALTO,
                ))

        # 1.3 Baixa cobertura de juros
        if desp_fin > 0 and ebit:
            cobertura = ebit / desp_fin
            if cobertura < self.COBERTURA_JUROS_MINIMA:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="COBERTURA_JUROS_BAIXA",
                    severidade="ALTO",
                    titulo=f"Cobertura de juros: {cobertura:.2f}x (minimo: {self.COBERTURA_JUROS_MINIMA}x)",
                    descricao="EBIT insuficiente para cobrir despesas financeiras com folga.",
                    valor_detectado=cobertura,
                    threshold_usado=self.COBERTURA_JUROS_MINIMA,
                ))

        # 1.4 Queima de caixa operacional
        if fcf_op < 0:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="QUEIMA_CAIXA",
                severidade="ALTO",
                titulo=f"Fluxo de caixa operacional negativo: R$ {fcf_op/1e6:.1f}M",
                descricao="Operacoes nao geram caixa. Empresa depende de financiamentos para sobreviver.",
                valor_detectado=fcf_op,
            ))

        return alertas

    def analisar_divergencia_lucro_caixa(self, ticker: str, dre: dict, fluxo: dict) -> List[Alerta]:
        """
        Cruzamento 2: Detecta divergencias entre lucro contabil e fluxo de caixa.
        """
        alertas = []

        lucro   = dre.get("lucro_liquido") or 0
        fcf_op  = fluxo.get("fcf_operacional") or 0

        # Lucro positivo mas caixa negativo (possivel manipulacao ou problemas de recebimento)
        if lucro > 0 and fcf_op < 0:
            ratio = lucro / abs(fcf_op) if fcf_op != 0 else None
            alertas.append(Alerta(
                ticker=ticker,
                tipo="DIVERGENCIA_LUCRO_CAIXA",
                severidade="MEDIO",
                titulo=f"Lucro positivo (R$ {lucro/1e6:.1f}M) mas caixa operacional negativo (R$ {fcf_op/1e6:.1f}M)",
                descricao=(
                    "Divergencia entre lucro contabil e geracao de caixa. "
                    "Possiveis causas: reconhecimento de receita sem recebimento, "
                    "aumento de estoques ou problemas de capital de giro."
                ),
                valor_detectado=ratio,
            ))

        # Caixa muito superior ao lucro (positivo - empresa muito conservadora ou com amortizacoes altas)
        if fcf_op > 0 and lucro < 0 and abs(lucro) < fcf_op:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="CAIXA_MELHOR_QUE_LUCRO",
                severidade="INFO",
                titulo=f"Caixa operacional positivo (R$ {fcf_op/1e6:.1f}M) apesar de prejuizo contabil",
                descricao=(
                    "Empresa gera caixa mesmo com resultado negativo. "
                    "Pode indicar alto nivel de depreciacao/amortizacao ou ajustes nao-caixa. "
                    "Analisar EBITDA e composicao do resultado."
                ),
                valor_detectado=fcf_op,
            ))

        return alertas

    def analisar_valuation_vs_setor(
        self,
        ticker: str,
        indicadores: dict,
        mediana_setor: dict,
        nome_setor: str,
    ) -> List[Alerta]:
        """
        Cruzamento 3: Compara indicadores da empresa com mediana do setor.
        indicadores e mediana_setor: dicts com {pl, pvp, ev_ebitda, roe, dy}
        """
        alertas = []

        def comparar(campo, nome, quanto_mais_alto_e_caro=True, fator_alerta=2.0, fator_info=1.5):
            val = indicadores.get(campo)
            med = mediana_setor.get(campo)
            if not val or not med or med == 0:
                return

            ratio = val / med
            if quanto_mais_alto_e_caro:
                if ratio > fator_alerta:
                    alertas.append(Alerta(
                        ticker=ticker,
                        tipo="VALUATION_CARO",
                        severidade="MEDIO",
                        titulo=f"{nome} ({val:.1f}x) e {ratio:.1f}x a mediana do setor ({med:.1f}x)",
                        descricao=f"Empresa negociada a premio significativo vs setor {nome_setor}.",
                        valor_detectado=val,
                        threshold_usado=med,
                    ))
                elif ratio < (1 / fator_info):
                    alertas.append(Alerta(
                        ticker=ticker,
                        tipo="VALUATION_BARATO",
                        severidade="INFO",
                        titulo=f"{nome} ({val:.1f}x) abaixo da mediana do setor ({med:.1f}x)",
                        descricao=f"Empresa pode estar subvalorizada vs peers no setor {nome_setor}.",
                        valor_detectado=val,
                        threshold_usado=med,
                    ))

        comparar("pl", "P/L")
        comparar("pvp", "P/VP")
        comparar("ev_ebitda", "EV/EBITDA")
        comparar("roe", "ROE", quanto_mais_alto_e_caro=False, fator_alerta=1.5, fator_info=2.0)

        return alertas

    def analisar_impacto_macro(
        self,
        ticker: str,
        setor: str,
        empresa: dict,
        macro: dict,
    ) -> List[Alerta]:
        """
        Cruzamento 4: Avalia impacto do cenario macro no setor da empresa.
        macro: {selic_atual, selic_6m_atras, ipca_atual, cambio_atual, cambio_6m_atras}
        empresa: {receita_exterior_pct, divida_dolar_pct}
        """
        alertas = []

        selic         = macro.get("selic_atual", 0)
        selic_antiga  = macro.get("selic_6m_atras", selic)
        cambio        = macro.get("cambio_atual", 0)
        cambio_antigo = macro.get("cambio_6m_atras", cambio)

        selic_subindo  = selic > selic_antiga * 1.05
        selic_alto     = selic > 12.0
        cambio_subindo = cambio > cambio_antigo * 1.05

        # Setores sensiveis a SELIC alta
        SETORES_SELIC_NEGATIVO = ["Varejo", "Construcao", "Consumo", "Locacao"]
        SETORES_SELIC_POSITIVO = ["Bancario", "Seguros", "Financeiro"]
        SETORES_DOLAR_POSITIVO = ["Mineracao", "Papel e Celulose", "Petroleo", "Agronegocio", "Siderurgia"]
        SETORES_DOLAR_NEGATIVO = ["Aviacao", "Importadores", "Varejo Eletronico"]

        if selic_alto and any(s in setor for s in SETORES_SELIC_NEGATIVO):
            alertas.append(Alerta(
                ticker=ticker,
                tipo="MACRO_SELIC_PRESSAO",
                severidade="MEDIO",
                titulo=f"SELIC em {selic:.1f}% pressiona setor: {setor}",
                descricao=(
                    f"Juros altos encarecem credito, reduzem consumo e aumentam custo da divida. "
                    f"Setor {setor} historicamente sofre com SELIC elevada."
                ),
                valor_detectado=selic,
            ))

        if selic_alto and any(s in setor for s in SETORES_SELIC_POSITIVO):
            alertas.append(Alerta(
                ticker=ticker,
                tipo="MACRO_SELIC_BENEFICIO",
                severidade="INFO",
                titulo=f"SELIC em {selic:.1f}% beneficia setor: {setor}",
                descricao=f"Setor {setor} tende a se beneficiar de juros elevados.",
                valor_detectado=selic,
            ))

        # Impacto cambio
        receita_ext = empresa.get("receita_exterior_pct", 0)
        if cambio_subindo and receita_ext > 30:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="MACRO_CAMBIO_BENEFICIO",
                severidade="INFO",
                titulo=f"Dolar subindo beneficia empresa com {receita_ext:.0f}% da receita no exterior",
                descricao="Valorização do dolar aumenta receita convertida para reais.",
                valor_detectado=cambio,
            ))

        return alertas

    def analisar_dividendos(
        self,
        ticker: str,
        dividendos_12m: float,
        preco: float,
        lucro_12m: float,
        market_cap: float,
        selic_atual: float,
        anos_consecutivos: int = 0,
    ) -> List[Alerta]:
        """
        Cruzamento 5: Avalia sustentabilidade e consistencia dos dividendos.
        """
        alertas = []

        if not preco or preco == 0:
            return alertas

        dy = (dividendos_12m / preco) * 100
        payout = (dividendos_12m * (market_cap / preco) / lucro_12m * 100) if lucro_12m and lucro_12m > 0 else None

        # Dividendo insustentavel (paga mais do que lucra)
        if payout and payout > 100:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="DIVIDENDO_INSUSTENTAVEL",
                severidade="ALTO",
                titulo=f"Payout de {payout:.0f}% - distribui mais do que lucra",
                descricao=(
                    f"A empresa pagou R$ {dividendos_12m:.2f}/acao em dividendos mas o LPA nao suporta. "
                    "Dividendo deve ser reduzido nos proximos periodos."
                ),
                valor_detectado=payout,
                threshold_usado=100.0,
            ))

        # DY atrativo vs SELIC
        if selic_atual > 0:
            ratio_dy_selic = dy / selic_atual
            if ratio_dy_selic < self.DY_MINIMO_ATRATIVO and dy > 0:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="DY_ABAIXO_SELIC",
                    severidade="INFO",
                    titulo=f"DY ({dy:.1f}%) abaixo da SELIC ({selic_atual:.1f}%)",
                    descricao="Renda fixa oferece retorno superior ao dividend yield desta acao.",
                    valor_detectado=dy,
                    threshold_usado=selic_atual,
                ))

        # Consistencia de pagamento
        if anos_consecutivos >= 5:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="DIVIDENDO_CONSISTENTE",
                severidade="INFO",
                titulo=f"Pagamento consistente: {anos_consecutivos} anos seguidos",
                descricao="Empresa demonstra historico solido de distribuicao de proventos.",
                valor_detectado=float(anos_consecutivos),
            ))

        return alertas
```

---

## Passo 4 - Motor de Alertas

### src/alerts/alert_engine.py
```python
from typing import List, Dict
from loguru import logger
from src.processors.cross_analyzer import CrossAnalyzer
from src.models.alert import Alerta
from src.collectors.brapi_collector import BrapiCollector
from src.collectors.bcb_collector import BCBCollector


class AlertEngine:
    """Orquestra todos os cruzamentos de dados e consolida alertas."""

    def __init__(self):
        self.analyzer = CrossAnalyzer()
        self.brapi    = BrapiCollector()
        self.bcb      = BCBCollector()
        self._macro_cache: Dict = {}

    def _obter_macro_atual(self) -> dict:
        if self._macro_cache:
            return self._macro_cache

        selic_df  = self.bcb.get_selic("01/01/2023")
        cambio_df = self.bcb.get_cambio_dolar("01/01/2023")

        selic_atual  = float(selic_df["valor"].iloc[-1])  if not selic_df.empty  else 0
        selic_6m     = float(selic_df["valor"].iloc[-130]) if len(selic_df) > 130 else selic_atual
        cambio_atual = float(cambio_df["valor"].iloc[-1])  if not cambio_df.empty else 0
        cambio_6m    = float(cambio_df["valor"].iloc[-130])if len(cambio_df) > 130 else cambio_atual

        self._macro_cache = {
            "selic_atual":    selic_atual,
            "selic_6m_atras": selic_6m,
            "cambio_atual":   cambio_atual,
            "cambio_6m_atras":cambio_6m,
            "ipca_atual":     0,  # preencher se necessario
        }
        return self._macro_cache

    def analisar_ticker(self, ticker: str) -> List[Alerta]:
        """
        Executa todos os cruzamentos para um ticker.
        Retorna lista consolidada de alertas.
        """
        todos_alertas = []

        try:
            cotacao = self.brapi.get_cotacao(ticker)
        except Exception as e:
            logger.error(f"[{ticker}] Erro ao buscar cotacao: {e}")
            return []

        # Extrair dados da cotacao (brapi ja traz indicadores pre-calculados)
        preco      = cotacao.get("regularMarketPrice", 0)
        market_cap = cotacao.get("marketCap", 0)
        setor      = cotacao.get("sector", "")

        # Montar dicts de dados (idealmente viriam do banco com dados CVM mais precisos)
        dre = {
            "lucro_liquido":      cotacao.get("netIncomeToCommon"),
            "receita_liquida":    cotacao.get("totalRevenue"),
            "ebitda":             cotacao.get("ebitda"),
            "ebit":               cotacao.get("ebit"),
            "resultado_financeiro": cotacao.get("totalDebt"),  # aproximacao
        }

        balanco = {
            "patrimonio_liquido": cotacao.get("bookValue", 0) * (market_cap / preco if preco else 0),
            "divida_bruta":       cotacao.get("totalDebt", 0),
            "caixa_equivalentes": cotacao.get("totalCash", 0),
            "ativo_total":        cotacao.get("totalAssets", 0),
        }

        fluxo = {
            "fcf_operacional": cotacao.get("operatingCashflow"),
            "fcf_livre":       cotacao.get("freeCashflow"),
            "capex":           None,
        }

        macro = self._obter_macro_atual()

        # Executar cruzamentos
        todos_alertas += self.analyzer.analisar_saude_financeira(ticker, dre, balanco, fluxo)
        todos_alertas += self.analyzer.analisar_divergencia_lucro_caixa(ticker, dre, fluxo)
        todos_alertas += self.analyzer.analisar_impacto_macro(ticker, setor, {}, macro)

        # Cruzamento de dividendos
        dy_raw = cotacao.get("dividendYield", 0) or 0
        dividendos_12m = preco * dy_raw if preco else 0
        lucro_12m = dre.get("lucro_liquido") or 0

        todos_alertas += self.analyzer.analisar_dividendos(
            ticker=ticker,
            dividendos_12m=dividendos_12m,
            preco=preco,
            lucro_12m=lucro_12m,
            market_cap=market_cap,
            selic_atual=macro["selic_atual"],
        )

        # Ordenar por severidade
        ordem = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "INFO": 3}
        todos_alertas.sort(key=lambda a: ordem.get(a.severidade, 9))

        logger.info(f"[{ticker}] {len(todos_alertas)} alertas gerados.")
        return todos_alertas

    def analisar_multiplos(self, tickers: List[str]) -> Dict[str, List[Alerta]]:
        """Analisa multiplos tickers e retorna dicionario ticker -> alertas."""
        resultado = {}
        for ticker in tickers:
            resultado[ticker] = self.analisar_ticker(ticker)
        return resultado
```

---

## Passo 5 - Pagina de Alertas no Dashboard

### dashboard/pages/5_Alertas.py
```python
import streamlit as st
import pandas as pd
import sys
sys.path.append(".")

from src.alerts.alert_engine import AlertEngine
from src.collectors.b3_collector import B3Collector

st.set_page_config(page_title="Painel de Alertas", layout="wide")
st.title("Painel de Alertas - Cruzamento de Dados")

CORES_SEVERIDADE = {
    "CRITICO": "🔴",
    "ALTO":    "🟠",
    "MEDIO":   "🟡",
    "INFO":    "🔵",
}

# Opcoes de analise
opcao = st.radio("Analisar:", ["Ticker especifico", "Lista personalizada", "Ibovespa completo"])

tickers_alvo = []

if opcao == "Ticker especifico":
    t = st.text_input("Ticker:", "PETR4").upper()
    tickers_alvo = [t] if t else []

elif opcao == "Lista personalizada":
    lista = st.text_area("Tickers (um por linha ou separados por virgula):", "PETR4\nVALE3\nITUB4")
    tickers_alvo = [t.strip().upper() for t in lista.replace(",", "\n").split("\n") if t.strip()]

elif opcao == "Ibovespa completo":
    st.warning("Analisar o Ibovespa completo faz ~90 requisicoes a API. Pode demorar alguns minutos.")
    if st.button("Confirmar e Analisar Ibovespa"):
        b3 = B3Collector()
        composicao = b3.get_composicao_ibovespa()
        tickers_alvo = composicao["ticker"].tolist() if not composicao.empty else []

# Filtros de severidade
severidades = st.multiselect(
    "Filtrar por severidade:",
    ["CRITICO", "ALTO", "MEDIO", "INFO"],
    default=["CRITICO", "ALTO", "MEDIO"]
)

if tickers_alvo and st.button("Executar Analise"):
    engine = AlertEngine()
    todos_alertas = []

    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers_alvo):
        status.text(f"Analisando {ticker} ({i+1}/{len(tickers_alvo)})...")
        alertas = engine.analisar_ticker(ticker)
        for a in alertas:
            if a.severidade in severidades:
                todos_alertas.append({
                    "Severidade": f"{CORES_SEVERIDADE.get(a.severidade, '')} {a.severidade}",
                    "Ticker":     a.ticker,
                    "Tipo":       a.tipo,
                    "Alerta":     a.titulo,
                    "Descricao":  a.descricao,
                })
        progress.progress((i + 1) / len(tickers_alvo))

    status.empty()

    if todos_alertas:
        df = pd.DataFrame(todos_alertas)

        # Resumo
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Alertas", len(df))
        col2.metric("Criticos", len(df[df["Severidade"].str.contains("CRITICO")]))
        col3.metric("Altos",    len(df[df["Severidade"].str.contains("ALTO")]))
        col4.metric("Medios",   len(df[df["Severidade"].str.contains("MEDIO")]))

        st.divider()

        # Tabela de alertas
        st.subheader("Alertas Detectados")
        st.dataframe(
            df[["Severidade", "Ticker", "Tipo", "Alerta"]],
            use_container_width=True,
            height=400
        )

        # Detalhe ao selecionar
        st.subheader("Detalhes")
        ticker_sel = st.selectbox("Ver detalhes de:", df["Ticker"].unique())
        if ticker_sel:
            df_sel = df[df["Ticker"] == ticker_sel]
            for _, row in df_sel.iterrows():
                with st.expander(f"{row['Severidade']} | {row['Alerta']}"):
                    st.write(row["Descricao"])
    else:
        st.success("Nenhum alerta detectado para os filtros selecionados.")
```

---

## Passo 6 - Testes dos Cruzamentos

### tests/test_processors/test_cross_analyzer.py
```python
import pytest
from src.processors.cross_analyzer import CrossAnalyzer


@pytest.fixture
def analyzer():
    return CrossAnalyzer()


# --- Saude Financeira ---

def test_alerta_prejuizo_critico(analyzer):
    dre     = {"lucro_liquido": -1_000_000_000, "receita_liquida": 5_000_000_000, "ebitda": 500_000_000, "ebit": 200_000_000, "resultado_financeiro": -100_000_000}
    balanco = {"patrimonio_liquido": 3_000_000_000, "divida_bruta": 8_000_000_000, "caixa_equivalentes": 1_000_000_000, "ativo_total": 20_000_000_000}
    fluxo   = {"fcf_operacional": -200_000_000, "fcf_livre": -500_000_000, "capex": None}

    alertas = analyzer.analisar_saude_financeira("XPTO3", dre, balanco, fluxo)
    tipos = [a.tipo for a in alertas]

    assert "PREJUIZO_LIQUIDO" in tipos
    assert "QUEIMA_CAIXA" in tipos


def test_sem_alerta_empresa_saudavel(analyzer):
    dre     = {"lucro_liquido": 2_000_000_000, "receita_liquida": 10_000_000_000, "ebitda": 4_000_000_000, "ebit": 3_000_000_000, "resultado_financeiro": -200_000_000}
    balanco = {"patrimonio_liquido": 15_000_000_000, "divida_bruta": 4_000_000_000, "caixa_equivalentes": 3_000_000_000, "ativo_total": 40_000_000_000}
    fluxo   = {"fcf_operacional": 2_500_000_000, "fcf_livre": 1_500_000_000, "capex": None}

    alertas = analyzer.analisar_saude_financeira("SAUD3", dre, balanco, fluxo)
    tipos = [a.tipo for a in alertas]

    assert "PREJUIZO_LIQUIDO" not in tipos
    assert "QUEIMA_CAIXA" not in tipos


# --- Dividendos ---

def test_alerta_dividendo_insustentavel(analyzer):
    alertas = analyzer.analisar_dividendos(
        ticker="DIVX3",
        dividendos_12m=5.0,
        preco=20.0,
        lucro_12m=1_000_000,   # lucro baixo
        market_cap=2_000_000_000,
        selic_atual=13.75,
    )
    tipos = [a.tipo for a in alertas]
    assert "DIVIDENDO_INSUSTENTAVEL" in tipos


def test_alerta_dy_abaixo_selic(analyzer):
    alertas = analyzer.analisar_dividendos(
        ticker="DIVB3",
        dividendos_12m=0.50,
        preco=20.0,          # DY = 2.5%
        lucro_12m=500_000_000,
        market_cap=10_000_000_000,
        selic_atual=13.75,   # SELIC muito acima do DY
    )
    tipos = [a.tipo for a in alertas]
    assert "DY_ABAIXO_SELIC" in tipos
```

---

## Criterio de Conclusao da Fase 3

A fase esta concluida quando:
1. `pytest tests/test_processors/test_cross_analyzer.py` passa
2. Pagina "Alertas" detecta pelo menos 1 alerta real em uma empresa conhecida por dificuldades
3. O motor nao crasha ao analisar uma lista de 10 tickers
4. Alertas aparecem ordenados por severidade no dashboard
