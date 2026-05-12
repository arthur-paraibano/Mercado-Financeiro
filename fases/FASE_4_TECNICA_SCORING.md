# Fase 4 - Analise Tecnica + Scoring

**Pre-requisito:** Fases 1, 2 e 3 concluidas.

**Objetivo:** Combinar analise fundamentalista com indicadores tecnicos e criar um sistema de scores (0-100) para cada acao, gerando um ranking geral e uma tela de screening avancado.

**Resultado esperado ao final:** Pagina de ranking mostrando as melhores acoes por score composto, e pagina de screening com filtros por qualquer indicador (P/L < X, ROE > Y, DY > Z, etc.).

---

## Checklist de Entregas

- [ ] Coletor Alpha Vantage para indicadores tecnicos
- [ ] Calculo de RSI, MACD, Medias Moveis com pandas
- [ ] Cruzamento 6: Tecnico + Fundamentalista
- [ ] Score de Saude Financeira (0-100)
- [ ] Score de Valuation (0-100)
- [ ] Score de Dividendos (0-100)
- [ ] Score de Crescimento (0-100)
- [ ] Score de Risco (0-100)
- [ ] Score Geral (media ponderada)
- [ ] Tabela de scores no banco
- [ ] Pagina de Ranking no dashboard
- [ ] Pagina de Screening com filtros avancados

---

## Passo 1 - Tabela de Scores

```sql
CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    ticker VARCHAR(10) NOT NULL,
    data_calculo DATE NOT NULL,
    score_saude NUMERIC(5,2),       -- 0-100
    score_valuation NUMERIC(5,2),   -- 0-100
    score_dividendos NUMERIC(5,2),  -- 0-100
    score_crescimento NUMERIC(5,2), -- 0-100
    score_risco NUMERIC(5,2),       -- 0-100
    score_tecnico NUMERIC(5,2),     -- 0-100
    score_geral NUMERIC(5,2),       -- 0-100 (media ponderada)
    detalhes JSONB,                 -- detalhes dos sub-scores
    UNIQUE(ticker, data_calculo)
);

CREATE TABLE IF NOT EXISTS indicadores_tecnicos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    data DATE NOT NULL,
    rsi_14 NUMERIC(8,4),
    macd NUMERIC(15,4),
    macd_signal NUMERIC(15,4),
    sma_20 NUMERIC(15,4),
    sma_50 NUMERIC(15,4),
    sma_200 NUMERIC(15,4),
    ema_9 NUMERIC(15,4),
    bollinger_upper NUMERIC(15,4),
    bollinger_lower NUMERIC(15,4),
    volume_sma_20 BIGINT,
    UNIQUE(empresa_id, data)
);
```

---

## Passo 2 - Calculo de Indicadores Tecnicos com Pandas

### src/processors/technical_calculator.py
```python
import pandas as pd
import numpy as np
from loguru import logger


class TechnicalCalculator:
    """Calcula indicadores tecnicos a partir de serie OHLCV."""

    @staticmethod
    def calcular_todos(df: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe DataFrame com colunas: date, open, high, low, close, volume
        Retorna DataFrame com indicadores tecnicos adicionados.
        """
        df = df.copy().sort_values("date").reset_index(drop=True)
        close = df["close"]
        volume = df["volume"]

        # --- Medias Moveis ---
        df["sma_20"]  = close.rolling(window=20).mean()
        df["sma_50"]  = close.rolling(window=50).mean()
        df["sma_200"] = close.rolling(window=200).mean()
        df["ema_9"]   = close.ewm(span=9, adjust=False).mean()
        df["ema_21"]  = close.ewm(span=21, adjust=False).mean()

        # --- RSI (14 periodos) ---
        delta = close.diff()
        gain  = delta.where(delta > 0, 0)
        loss  = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # --- MACD (12, 26, 9) ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"]        = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"]   = df["macd"] - df["macd_signal"]

        # --- Bollinger Bands (20, 2) ---
        sma20  = close.rolling(window=20).mean()
        std20  = close.rolling(window=20).std()
        df["bollinger_upper"] = sma20 + (2 * std20)
        df["bollinger_lower"] = sma20 - (2 * std20)
        df["bollinger_mid"]   = sma20

        # --- Volume ---
        df["volume_sma_20"] = volume.rolling(window=20).mean()
        df["volume_ratio"]  = volume / df["volume_sma_20"]  # > 2 = volume anomalo

        # --- ATR (Average True Range) ---
        high, low = df["high"], df["low"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs()
        ], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=14).mean()

        return df

    @staticmethod
    def gerar_sinais(df: pd.DataFrame) -> dict:
        """
        Analisa a ultima linha do DataFrame e retorna sinais de compra/venda.
        """
        if df.empty or len(df) < 200:
            return {}

        ultima = df.iloc[-1]
        penultima = df.iloc[-2]

        sinais = {}

        # RSI
        rsi = ultima.get("rsi_14")
        if rsi:
            if rsi < 30:
                sinais["RSI"] = {"sinal": "COMPRA", "valor": round(rsi, 2), "desc": "Sobrevenda (RSI < 30)"}
            elif rsi > 70:
                sinais["RSI"] = {"sinal": "VENDA", "valor": round(rsi, 2), "desc": "Sobrecompra (RSI > 70)"}
            else:
                sinais["RSI"] = {"sinal": "NEUTRO", "valor": round(rsi, 2), "desc": f"RSI neutro em {rsi:.1f}"}

        # MACD cruzamento
        macd_atual = ultima.get("macd")
        macd_sinal_atual = ultima.get("macd_signal")
        macd_ant = penultima.get("macd")
        macd_sinal_ant = penultima.get("macd_signal")

        if all(v is not None for v in [macd_atual, macd_sinal_atual, macd_ant, macd_sinal_ant]):
            cruzou_acima = macd_ant < macd_sinal_ant and macd_atual > macd_sinal_atual
            cruzou_abaixo = macd_ant > macd_sinal_ant and macd_atual < macd_sinal_atual
            if cruzou_acima:
                sinais["MACD"] = {"sinal": "COMPRA", "valor": round(macd_atual, 4), "desc": "MACD cruzou acima da linha de sinal"}
            elif cruzou_abaixo:
                sinais["MACD"] = {"sinal": "VENDA", "valor": round(macd_atual, 4), "desc": "MACD cruzou abaixo da linha de sinal"}

        # Cruzamento de medias
        close = ultima.get("close")
        sma50 = ultima.get("sma_50")
        sma200 = ultima.get("sma_200")

        if close and sma50 and sma200:
            if close > sma200 and sma50 > sma200:
                sinais["MEDIAS"] = {"sinal": "COMPRA", "valor": round(close, 2), "desc": "Preco e SMA50 acima da SMA200 (tendencia de alta)"}
            elif close < sma200:
                sinais["MEDIAS"] = {"sinal": "VENDA", "valor": round(close, 2), "desc": "Preco abaixo da SMA200 (tendencia de baixa)"}

        # Bollinger Bands
        boll_lower = ultima.get("bollinger_lower")
        boll_upper = ultima.get("bollinger_upper")
        if close and boll_lower and boll_upper:
            if close <= boll_lower:
                sinais["BOLLINGER"] = {"sinal": "COMPRA", "valor": round(close, 2), "desc": "Preco na banda inferior de Bollinger"}
            elif close >= boll_upper:
                sinais["BOLLINGER"] = {"sinal": "VENDA", "valor": round(close, 2), "desc": "Preco na banda superior de Bollinger"}

        # Volume anomalo
        vol_ratio = ultima.get("volume_ratio")
        if vol_ratio and vol_ratio > 2.5:
            sinais["VOLUME"] = {"sinal": "ATENCAO", "valor": round(vol_ratio, 2), "desc": f"Volume {vol_ratio:.1f}x acima da media (anomalo)"}

        return sinais
```

---

## Passo 3 - Calculadora de Scores

### src/processors/score_calculator.py
```python
import math
from typing import Optional
from loguru import logger


class ScoreCalculator:
    """
    Calcula scores 0-100 para cada dimensao de analise.
    100 = excelente, 0 = pessimo.
    """

    # Pesos do score geral (somam 100)
    PESOS = {
        "saude":      30,
        "valuation":  25,
        "dividendos": 20,
        "crescimento":15,
        "tecnico":    10,
    }

    # --- SCORE DE SAUDE FINANCEIRA ---
    def score_saude(self, indicadores: dict) -> tuple[float, dict]:
        """
        Avalia: ROE, margem, endividamento, cobertura de juros, fluxo de caixa.
        """
        pontos = {}

        # ROE (peso 25)
        roe = indicadores.get("roe") or 0
        if roe >= 20:     pontos["roe"] = 25
        elif roe >= 15:   pontos["roe"] = 20
        elif roe >= 10:   pontos["roe"] = 15
        elif roe >= 5:    pontos["roe"] = 8
        elif roe >= 0:    pontos["roe"] = 3
        else:             pontos["roe"] = 0  # ROE negativo

        # Margem Liquida (peso 20)
        margem = indicadores.get("margem_liquida") or 0
        if margem >= 20:  pontos["margem"] = 20
        elif margem >= 15:pontos["margem"] = 16
        elif margem >= 10:pontos["margem"] = 12
        elif margem >= 5: pontos["margem"] = 7
        elif margem >= 0: pontos["margem"] = 2
        else:             pontos["margem"] = 0

        # Divida Liq / EBITDA (peso 25) - quanto menor, melhor
        dliq_ebitda = indicadores.get("divida_liq_ebitda")
        if dliq_ebitda is None:
            pontos["divida"] = 12  # neutro se nao temos dado
        elif dliq_ebitda < 0:     pontos["divida"] = 25  # caixa liquido (otimo)
        elif dliq_ebitda <= 1:    pontos["divida"] = 22
        elif dliq_ebitda <= 2:    pontos["divida"] = 17
        elif dliq_ebitda <= 3:    pontos["divida"] = 10
        elif dliq_ebitda <= 4:    pontos["divida"] = 4
        else:                     pontos["divida"] = 0

        # Margem EBITDA (peso 15)
        m_ebitda = indicadores.get("margem_ebitda") or 0
        if m_ebitda >= 30:    pontos["m_ebitda"] = 15
        elif m_ebitda >= 20:  pontos["m_ebitda"] = 12
        elif m_ebitda >= 10:  pontos["m_ebitda"] = 8
        elif m_ebitda >= 0:   pontos["m_ebitda"] = 3
        else:                 pontos["m_ebitda"] = 0

        # ROA (peso 15)
        roa = indicadores.get("roa") or 0
        if roa >= 10:     pontos["roa"] = 15
        elif roa >= 7:    pontos["roa"] = 12
        elif roa >= 4:    pontos["roa"] = 8
        elif roa >= 1:    pontos["roa"] = 4
        elif roa >= 0:    pontos["roa"] = 1
        else:             pontos["roa"] = 0

        total = sum(pontos.values())
        return round(total, 2), pontos

    # --- SCORE DE VALUATION ---
    def score_valuation(self, indicadores: dict, mediana_setor: dict = None) -> tuple[float, dict]:
        """
        Avalia se a empresa esta barata ou cara.
        Usa valores absolutos e, se disponivel, compara com mediana do setor.
        """
        pontos = {}

        # P/L (peso 30) - quanto menor (e positivo), melhor
        pl = indicadores.get("pl")
        if pl is None or pl <= 0:   pontos["pl"] = 0
        elif pl <= 8:               pontos["pl"] = 30
        elif pl <= 12:              pontos["pl"] = 24
        elif pl <= 18:              pontos["pl"] = 18
        elif pl <= 25:              pontos["pl"] = 10
        elif pl <= 40:              pontos["pl"] = 4
        else:                       pontos["pl"] = 0

        # P/VP (peso 25)
        pvp = indicadores.get("pvp")
        if pvp is None or pvp <= 0: pontos["pvp"] = 10  # neutro
        elif pvp < 0.5:             pontos["pvp"] = 20  # muito barata (mas checar se eh armadilha)
        elif pvp <= 1.0:            pontos["pvp"] = 25
        elif pvp <= 1.5:            pontos["pvp"] = 20
        elif pvp <= 2.5:            pontos["pvp"] = 12
        elif pvp <= 4.0:            pontos["pvp"] = 5
        else:                       pontos["pvp"] = 0

        # EV/EBITDA (peso 25)
        ev_ebitda = indicadores.get("ev_ebitda")
        if ev_ebitda is None or ev_ebitda <= 0: pontos["ev_ebitda"] = 10
        elif ev_ebitda <= 6:        pontos["ev_ebitda"] = 25
        elif ev_ebitda <= 9:        pontos["ev_ebitda"] = 20
        elif ev_ebitda <= 12:       pontos["ev_ebitda"] = 14
        elif ev_ebitda <= 18:       pontos["ev_ebitda"] = 7
        else:                       pontos["ev_ebitda"] = 0

        # PSR (peso 20) - menor = mais barata por receita
        psr = indicadores.get("psr")
        if psr is None or psr <= 0: pontos["psr"] = 8
        elif psr <= 0.5:            pontos["psr"] = 20
        elif psr <= 1.5:            pontos["psr"] = 16
        elif psr <= 3.0:            pontos["psr"] = 10
        elif psr <= 5.0:            pontos["psr"] = 4
        else:                       pontos["psr"] = 0

        total = sum(pontos.values())
        return round(total, 2), pontos

    # --- SCORE DE DIVIDENDOS ---
    def score_dividendos(self, indicadores: dict, selic: float = 13.75, anos_consecutivos: int = 0) -> tuple[float, dict]:
        pontos = {}

        dy = indicadores.get("dividend_yield") or 0
        payout = indicadores.get("payout") or 0

        # Dividend Yield (peso 40) - compara com SELIC
        if selic > 0:
            dy_relativo = dy / selic  # 1.0 = igual a SELIC
            if dy_relativo >= 1.2:    pontos["dy"] = 40
            elif dy_relativo >= 0.9:  pontos["dy"] = 32
            elif dy_relativo >= 0.6:  pontos["dy"] = 20
            elif dy_relativo >= 0.3:  pontos["dy"] = 10
            elif dy > 0:              pontos["dy"] = 4
            else:                     pontos["dy"] = 0
        else:
            pontos["dy"] = 15 if dy > 4 else 5 if dy > 0 else 0

        # Sustentabilidade - payout (peso 30)
        if payout <= 0:               pontos["payout"] = 0  # nao paga
        elif payout <= 40:            pontos["payout"] = 30  # conservador e sustentavel
        elif payout <= 60:            pontos["payout"] = 25
        elif payout <= 80:            pontos["payout"] = 18
        elif payout <= 100:           pontos["payout"] = 8
        else:                         pontos["payout"] = 0  # paga mais que lucra

        # Consistencia (peso 30)
        if anos_consecutivos >= 10:   pontos["consistencia"] = 30
        elif anos_consecutivos >= 7:  pontos["consistencia"] = 24
        elif anos_consecutivos >= 5:  pontos["consistencia"] = 18
        elif anos_consecutivos >= 3:  pontos["consistencia"] = 10
        elif anos_consecutivos >= 1:  pontos["consistencia"] = 4
        else:                         pontos["consistencia"] = 0

        total = sum(pontos.values())
        return round(total, 2), pontos

    # --- SCORE DE CRESCIMENTO ---
    def score_crescimento(self, cagr_receita_3a: Optional[float], cagr_lucro_3a: Optional[float], cagr_receita_5a: Optional[float] = None) -> tuple[float, dict]:
        pontos = {}

        # CAGR Receita 3 anos (peso 40)
        if cagr_receita_3a is None:
            pontos["cagr_rec"] = 15  # neutro
        elif cagr_receita_3a >= 20:  pontos["cagr_rec"] = 40
        elif cagr_receita_3a >= 12:  pontos["cagr_rec"] = 32
        elif cagr_receita_3a >= 7:   pontos["cagr_rec"] = 22
        elif cagr_receita_3a >= 3:   pontos["cagr_rec"] = 12
        elif cagr_receita_3a >= 0:   pontos["cagr_rec"] = 4
        else:                        pontos["cagr_rec"] = 0

        # CAGR Lucro 3 anos (peso 40)
        if cagr_lucro_3a is None:
            pontos["cagr_luc"] = 15
        elif cagr_lucro_3a >= 20:    pontos["cagr_luc"] = 40
        elif cagr_lucro_3a >= 12:    pontos["cagr_luc"] = 32
        elif cagr_lucro_3a >= 5:     pontos["cagr_luc"] = 20
        elif cagr_lucro_3a >= 0:     pontos["cagr_luc"] = 8
        else:                        pontos["cagr_luc"] = 0

        # CAGR Receita 5 anos (peso 20)
        if cagr_receita_5a is None:
            pontos["cagr_5a"] = 8
        elif cagr_receita_5a >= 15:  pontos["cagr_5a"] = 20
        elif cagr_receita_5a >= 8:   pontos["cagr_5a"] = 15
        elif cagr_receita_5a >= 3:   pontos["cagr_5a"] = 10
        elif cagr_receita_5a >= 0:   pontos["cagr_5a"] = 4
        else:                        pontos["cagr_5a"] = 0

        total = sum(pontos.values())
        return round(min(total, 100), 2), pontos

    # --- SCORE TECNICO ---
    def score_tecnico(self, sinais: dict) -> tuple[float, dict]:
        """
        Converte sinais tecnicos em score.
        sinais: dict de TechnicalCalculator.gerar_sinais()
        """
        pontos_base = 50  # comecar neutro
        detalhes = {}

        pesos_sinal = {"RSI": 25, "MACD": 25, "MEDIAS": 30, "BOLLINGER": 15, "VOLUME": 5}

        for nome, info in sinais.items():
            sinal = info.get("sinal", "NEUTRO")
            peso = pesos_sinal.get(nome, 10)

            if sinal == "COMPRA":
                pontos_base += peso * 0.5
                detalhes[nome] = f"+{peso*0.5:.0f} ({info['desc']})"
            elif sinal == "VENDA":
                pontos_base -= peso * 0.5
                detalhes[nome] = f"-{peso*0.5:.0f} ({info['desc']})"
            elif sinal == "ATENCAO":
                detalhes[nome] = f"ATENCAO: {info['desc']}"

        return round(max(0, min(100, pontos_base)), 2), detalhes

    # --- SCORE GERAL ---
    def score_geral(self, scores: dict) -> float:
        """
        Calcula score geral como media ponderada.
        scores: {saude, valuation, dividendos, crescimento, tecnico}
        """
        total_peso = 0
        total_ponderado = 0

        for dim, peso in self.PESOS.items():
            val = scores.get(dim)
            if val is not None:
                total_ponderado += val * peso
                total_peso += peso

        if total_peso == 0:
            return 0

        return round(total_ponderado / total_peso, 2)
```

---

## Passo 4 - Pagina de Ranking

### dashboard/pages/6_Ranking.py
```python
import streamlit as st
import plotly.express as px
import pandas as pd
import sys
sys.path.append(".")

from src.collectors.brapi_collector import BrapiCollector
from src.processors.score_calculator import ScoreCalculator
from src.processors.technical_calculator import TechnicalCalculator

st.set_page_config(page_title="Ranking de Acoes", layout="wide")
st.title("Ranking de Acoes por Score Composto")

TICKERS_PADRAO = [
    "WEGE3", "ITUB4", "BBAS3", "VALE3", "PETR4",
    "EGIE3", "TAEE11", "CPFE3", "SUZB3", "KLBN11",
    "RDOR3", "FLRY3", "TOTS3", "SLCE3", "BEEF3",
    "BBDC4", "SANB11", "PRIO3", "LREN3", "VIVT3",
]

st.sidebar.subheader("Configuracao")
usar_padrao = st.sidebar.checkbox("Usar lista padrao (20 acoes)", value=True)

if usar_padrao:
    tickers = TICKERS_PADRAO
else:
    lista = st.sidebar.text_area("Tickers (separados por virgula):", "WEGE3,ITUB4,VALE3")
    tickers = [t.strip().upper() for t in lista.split(",") if t.strip()]

if st.button("Calcular Ranking"):
    brapi = BrapiCollector()
    calc  = ScoreCalculator()
    resultados = []

    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"Calculando score de {ticker} ({i+1}/{len(tickers)})...")
        try:
            cotacao = brapi.get_cotacao(ticker)
            preco = cotacao.get("regularMarketPrice", 0)
            market_cap = cotacao.get("marketCap", 0)

            indicadores = {
                "pl":             cotacao.get("priceEarnings"),
                "pvp":            cotacao.get("priceToBook"),
                "ev_ebitda":      cotacao.get("enterpriseValueOverEbitda"),
                "psr":            cotacao.get("priceToSalesTrailing12Months"),
                "roe":            (cotacao.get("returnOnEquity") or 0) * 100,
                "roa":            (cotacao.get("returnOnAssets") or 0) * 100,
                "margem_liquida": (cotacao.get("profitMargins") or 0) * 100,
                "margem_ebitda":  (cotacao.get("ebitdaMargins") or 0) * 100,
                "divida_liq_ebitda": cotacao.get("debtToEquity"),
                "dividend_yield": (cotacao.get("dividendYield") or 0) * 100,
                "payout":         (cotacao.get("payoutRatio") or 0) * 100,
            }

            # Indicadores tecnicos
            historico = brapi.get_historico(ticker, "1y", "1d")
            sinais = {}
            if historico:
                df_h = pd.DataFrame(historico)
                df_h["date"] = pd.to_datetime(df_h["date"], unit="s")
                df_tech = TechnicalCalculator.calcular_todos(df_h)
                sinais = TechnicalCalculator.gerar_sinais(df_tech)

            # Calcular scores
            s_saude,    d_saude     = calc.score_saude(indicadores)
            s_valuation, d_val      = calc.score_valuation(indicadores)
            s_div,      d_div       = calc.score_dividendos(indicadores)
            s_cresc,    d_cresc     = calc.score_crescimento(None, None)
            s_tec,      d_tec       = calc.score_tecnico(sinais)

            scores = {
                "saude": s_saude, "valuation": s_valuation,
                "dividendos": s_div, "crescimento": s_cresc, "tecnico": s_tec
            }
            s_geral = calc.score_geral(scores)

            resultados.append({
                "Ticker":      ticker,
                "Nome":        cotacao.get("shortName", ticker),
                "Preco":       f"R$ {preco:.2f}",
                "Score Geral": s_geral,
                "Saude":       s_saude,
                "Valuation":   s_valuation,
                "Dividendos":  s_div,
                "Crescimento": s_cresc,
                "Tecnico":     s_tec,
                "P/L":         indicadores.get("pl"),
                "DY":          f"{indicadores.get('dividend_yield', 0):.1f}%",
                "ROE":         f"{indicadores.get('roe', 0):.1f}%",
            })
        except Exception as e:
            st.warning(f"{ticker}: {e}")
        progress.progress((i + 1) / len(tickers))

    status.empty()
    progress.empty()

    if resultados:
        df = pd.DataFrame(resultados).sort_values("Score Geral", ascending=False).reset_index(drop=True)
        df.index += 1  # Ranking começa em 1

        st.subheader("Ranking Geral")
        st.dataframe(
            df[["Ticker", "Nome", "Score Geral", "Saude", "Valuation", "Dividendos", "Crescimento", "Tecnico", "P/L", "DY", "ROE", "Preco"]],
            use_container_width=True
        )

        # Grafico de radar para top 5
        st.subheader("Top 5 - Comparacao por Dimensao")
        top5 = df.head(5)
        fig = px.bar(
            top5.melt(id_vars=["Ticker"], value_vars=["Saude", "Valuation", "Dividendos", "Crescimento", "Tecnico"]),
            x="variable", y="value", color="Ticker", barmode="group",
            title="Top 5 Acoes por Score",
            labels={"variable": "Dimensao", "value": "Score (0-100)"}
        )
        st.plotly_chart(fig, use_container_width=True)
```

---

## Passo 5 - Pagina de Screening

### dashboard/pages/7_Screening.py
```python
import streamlit as st
import pandas as pd
import sys
sys.path.append(".")

from src.collectors.brapi_collector import BrapiCollector

st.set_page_config(page_title="Screening de Acoes", layout="wide")
st.title("Screening - Filtro Avancado de Acoes")

st.sidebar.header("Filtros")

# Filtros
pl_max     = st.sidebar.slider("P/L maximo",        0.0, 50.0, 15.0, 0.5)
pvp_max    = st.sidebar.slider("P/VP maximo",        0.0, 10.0, 2.0,  0.1)
roe_min    = st.sidebar.slider("ROE minimo (%)",     0.0, 50.0, 10.0, 0.5)
dy_min     = st.sidebar.slider("DY minimo (%)",      0.0, 20.0, 3.0,  0.5)
margem_min = st.sidebar.slider("Margem Liq. min (%)", -20.0, 30.0, 0.0, 0.5)
ebitda_max = st.sidebar.slider("EV/EBITDA maximo",   0.0, 30.0, 12.0, 0.5)

TICKERS_UNIVERSO = [
    "ABEV3","AZUL4","B3SA3","BBAS3","BBDC4","BEEF3","BPAC11","BRFS3",
    "CASH3","CCRO3","CIEL3","CMIG4","COGN3","CPFE3","CSAN3","CYRE3",
    "DXCO3","EGIE3","EMBR3","ENEV3","ENGI11","EQTL3","GGBR4","GOAU4",
    "HAPV3","HYPE3","ITSA4","ITUB4","JBSS3","KLBN11","LREN3","LWSA3",
    "MGLU3","MRFG3","MRVE3","MULT3","NTCO3","PETZ3","PETR4","PRIO3",
    "RADL3","RAIZ4","RDOR3","RENT3","SANB11","SLCE3","SMTO3","SUZB3",
    "TAEE11","TIMS3","TOTS3","UGPA3","USIM5","VALE3","VBBR3","VIVT3",
    "WEGE3","YDUQ3",
]

if st.button("Executar Screening"):
    brapi = BrapiCollector()
    resultados = []

    progress = st.progress(0)
    for i, ticker in enumerate(TICKERS_UNIVERSO):
        try:
            cotacao = brapi.get_cotacao(ticker)

            pl    = cotacao.get("priceEarnings")
            pvp   = cotacao.get("priceToBook")
            roe   = (cotacao.get("returnOnEquity") or 0) * 100
            dy    = (cotacao.get("dividendYield") or 0) * 100
            margem = (cotacao.get("profitMargins") or 0) * 100
            ev_ebitda = cotacao.get("enterpriseValueOverEbitda")

            # Aplicar filtros
            passa = True
            if pl is not None and (pl <= 0 or pl > pl_max):     passa = False
            if pvp is not None and pvp > pvp_max:                passa = False
            if roe < roe_min:                                     passa = False
            if dy < dy_min:                                       passa = False
            if margem < margem_min:                               passa = False
            if ev_ebitda is not None and ev_ebitda > ebitda_max: passa = False

            if passa:
                resultados.append({
                    "Ticker": ticker,
                    "Nome":   cotacao.get("shortName", ticker),
                    "Preco":  cotacao.get("regularMarketPrice"),
                    "P/L":    round(pl, 2) if pl else None,
                    "P/VP":   round(pvp, 2) if pvp else None,
                    "ROE %":  round(roe, 2),
                    "DY %":   round(dy, 2),
                    "Margem Liq %": round(margem, 2),
                    "EV/EBITDA": round(ev_ebitda, 2) if ev_ebitda else None,
                })
        except:
            pass
        progress.progress((i + 1) / len(TICKERS_UNIVERSO))

    if resultados:
        df = pd.DataFrame(resultados)
        st.success(f"{len(df)} empresas passaram nos filtros.")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhuma empresa passou em todos os filtros. Tente relaxar os criterios.")
```

---

## Criterio de Conclusao da Fase 4

A fase esta concluida quando:
1. `ScoreCalculator` calcula scores coerentes (empresa saudavel > 60 pts em saude, empresa endividada < 30 pts)
2. `TechnicalCalculator` gera sinais corretos para RSI < 30 (compra) e RSI > 70 (venda)
3. Pagina de Ranking exibe tabela ordenada por score geral
4. Pagina de Screening filtra corretamente por P/L, ROE e DY
