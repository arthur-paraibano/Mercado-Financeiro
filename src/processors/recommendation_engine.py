import time
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
from loguru import logger

from src.collectors.brapi_collector import BrapiCollector
from src.collectors.fundamentus_collector import FundamentusCollector
from src.processors.score_calculator import ScoreCalculator
from src.processors.technical_calculator import TechnicalCalculator


@dataclass
class Recomendacao:
    ticker: str
    empresa: str
    setor: str
    cotacao: float
    score_geral: float
    scores: dict
    sinal: str              # 'COMPRA FORTE', 'COMPRA', 'NEUTRO', 'CAUTELA', 'EVITAR'
    preco_teto: float       # preco maximo sugerido para compra
    preco_justo: float      # estimativa de valor justo
    upside_pct: float       # potencial de valorizacao %
    motivos: List[str]      # razoes da recomendacao
    riscos: List[str]       # riscos identificados
    sinais_tecnicos: dict = field(default_factory=dict)
    indicadores: dict = field(default_factory=dict)


class RecommendationEngine:
    """Gera recomendacoes de compra baseadas em todos os cruzamentos do sistema."""

    def __init__(self):
        self.fund = FundamentusCollector()
        self.brapi = BrapiCollector()
        self.calc = ScoreCalculator()

    def _estimar_preco_justo(self, dados: dict) -> tuple[float, float]:
        """
        Estima preco justo e preco teto usando multiplos metodos.
        Retorna (preco_justo, preco_teto).
        """
        cotacao = dados.get("cotacao") or 0
        lpa = dados.get("lpa") or 0
        vpa = dados.get("vpa") or 0
        roe = dados.get("roe") or 0
        dy = dados.get("dividend_yield") or 0
        pl = dados.get("pl") or 0

        estimativas = []

        # Metodo 1: Graham simplificado -> sqrt(22.5 * LPA * VPA)
        if lpa > 0 and vpa > 0:
            graham = (22.5 * lpa * vpa) ** 0.5
            estimativas.append(graham)

        # Metodo 2: Bazin (para empresas de dividendos) -> DPA / 0.06
        if dy > 3 and cotacao > 0:
            dpa = cotacao * (dy / 100)
            bazin = dpa / 0.06  # 6% como yield minimo desejado
            estimativas.append(bazin)

        # Metodo 3: P/L justo * LPA (P/L justo = 15 para lucro estavel, 10 para ciclicas)
        if lpa > 0:
            pl_justo = 15 if roe > 12 else 12 if roe > 8 else 8
            pl_valor = lpa * pl_justo
            estimativas.append(pl_valor)

        # Metodo 4: VPA * multiplicador ROE
        if vpa > 0 and roe > 0:
            # Se ROE > 15%, empresa merece premio sobre VPA
            mult = min(roe / 10, 3.0)  # cap em 3x VPA
            vpa_valor = vpa * mult
            estimativas.append(vpa_valor)

        if not estimativas:
            return cotacao, cotacao

        preco_justo = sum(estimativas) / len(estimativas)
        # Preco teto = preco justo com margem de seguranca de 20%
        preco_teto = preco_justo * 0.80

        return round(preco_justo, 2), round(preco_teto, 2)

    def _classificar_sinal(
        self, score: float, upside: float, sinais_tec: dict, riscos: list
    ) -> str:
        """Classifica o sinal de recomendacao."""
        sinais_compra = sum(
            1 for s in sinais_tec.values() if s.get("sinal") == "COMPRA"
        )
        sinais_venda = sum(
            1 for s in sinais_tec.values() if s.get("sinal") == "VENDA"
        )
        tem_risco_critico = any("CRITICO" in r or "prejuizo" in r.lower() for r in riscos)

        if tem_risco_critico:
            return "EVITAR"

        if score >= 65 and upside > 20 and sinais_compra >= 2:
            return "COMPRA FORTE"
        elif score >= 55 and upside > 10:
            return "COMPRA"
        elif score >= 40 and upside > 0:
            return "NEUTRO"
        elif sinais_venda >= 2 or upside < -15:
            return "EVITAR"
        else:
            return "CAUTELA"

    def _identificar_motivos(self, dados: dict, scores: dict) -> list[str]:
        """Identifica os motivos positivos da recomendacao."""
        motivos = []

        if scores.get("saude", 0) >= 70:
            motivos.append(f"Saude financeira excelente (score {scores['saude']:.0f})")
        if scores.get("valuation", 0) >= 65:
            motivos.append(f"Valuation atrativo (score {scores['valuation']:.0f})")

        roe = dados.get("roe") or 0
        if roe >= 20:
            motivos.append(f"ROE alto: {roe:.1f}%")

        dy = dados.get("dividend_yield") or 0
        if dy >= 6:
            motivos.append(f"Dividend Yield elevado: {dy:.1f}%")

        margem = dados.get("margem_liquida") or 0
        if margem >= 15:
            motivos.append(f"Margem liquida saudavel: {margem:.1f}%")

        divida_liq = dados.get("divida_liquida") or 0
        if divida_liq < 0:
            motivos.append("Empresa com caixa liquido (sem divida)")

        cres = dados.get("cres_rec_5a") or 0
        if cres >= 10:
            motivos.append(f"Crescimento de receita: {cres:.1f}% em 5 anos")

        pl = dados.get("pl") or 0
        if 0 < pl <= 10:
            motivos.append(f"P/L atrativo: {pl:.1f}x")

        roic = dados.get("roic") or 0
        if roic >= 15:
            motivos.append(f"ROIC alto: {roic:.1f}%")

        return motivos[:5]

    def _identificar_riscos(self, dados: dict, scores: dict) -> list[str]:
        """Identifica riscos da acao."""
        riscos = []

        lucro = dados.get("lucro_liquido_12m") or 0
        if lucro < 0:
            riscos.append(f"CRITICO: Empresa com prejuizo de R$ {abs(lucro)/1e6:.0f}M")

        roe = dados.get("roe") or 0
        if roe < 0:
            riscos.append(f"ROE negativo: {roe:.1f}%")

        margem = dados.get("margem_liquida") or 0
        if margem < 0:
            riscos.append(f"Margem liquida negativa: {margem:.1f}%")

        liq = dados.get("liquidez_corrente") or 0
        if 0 < liq < 0.8:
            riscos.append(f"Liquidez corrente baixa: {liq:.2f}")

        divida_liq = dados.get("divida_liquida") or 0
        ebit = dados.get("ebit_12m") or 0
        if ebit > 0 and divida_liq > 0:
            ratio = divida_liq / (ebit * 1.15)
            if ratio > 4:
                riscos.append(f"Endividamento alto: Div.Liq/EBITDA ~{ratio:.1f}x")

        pl = dados.get("pl") or 0
        if pl > 30:
            riscos.append(f"P/L elevado: {pl:.1f}x - valuation esticado")

        if scores.get("saude", 100) < 30:
            riscos.append("Score de saude financeira baixo")

        lucro_3m = dados.get("lucro_liquido_3m") or 0
        if lucro > 0 and lucro_3m < 0:
            riscos.append("Ultimo trimestre com prejuizo")

        return riscos[:5]

    def analisar_ticker(self, ticker: str) -> Optional[Recomendacao]:
        """Gera recomendacao completa para um ticker."""
        try:
            dados = self.fund.get_papel(ticker)
        except Exception as e:
            logger.error(f"[{ticker}] Fundamentus: {e}")
            return None

        cotacao = dados.get("cotacao") or 0
        if cotacao <= 0:
            return None

        # Scores
        s_saude, _ = self.calc.score_saude(dados)
        s_val, _ = self.calc.score_valuation(dados)
        s_div, _ = self.calc.score_dividendos(dados)
        s_cres, _ = self.calc.score_crescimento(dados)

        # Indicadores tecnicos
        sinais_tec = {}
        try:
            hist = self.brapi.get_historico(ticker, "3mo", "1d")
            if hist and len(hist) > 30:
                df_h = pd.DataFrame(hist)
                df_h["date"] = pd.to_datetime(df_h["date"], unit="s")
                df_tech = TechnicalCalculator.calcular_todos(df_h)
                sinais_tec = TechnicalCalculator.gerar_sinais(df_tech)
        except Exception:
            pass

        s_tec, _ = self.calc.score_tecnico(sinais_tec)

        scores = {
            "saude": s_saude, "valuation": s_val,
            "dividendos": s_div, "crescimento": s_cres, "tecnico": s_tec,
        }
        score_geral = self.calc.score_geral(scores)

        # Preco justo e teto
        preco_justo, preco_teto = self._estimar_preco_justo(dados)
        upside = ((preco_justo / cotacao) - 1) * 100 if cotacao > 0 else 0

        # Motivos e riscos
        motivos = self._identificar_motivos(dados, scores)
        riscos = self._identificar_riscos(dados, scores)

        # Sinal final
        sinal = self._classificar_sinal(score_geral, upside, sinais_tec, riscos)

        return Recomendacao(
            ticker=ticker,
            empresa=(dados.get("empresa") or ticker)[:30],
            setor=dados.get("setor") or "N/A",
            cotacao=cotacao,
            score_geral=score_geral,
            scores=scores,
            sinal=sinal,
            preco_teto=preco_teto,
            preco_justo=preco_justo,
            upside_pct=round(upside, 1),
            motivos=motivos,
            riscos=riscos,
            sinais_tecnicos=sinais_tec,
            indicadores=dados,
        )

    def gerar_recomendacoes(self, tickers: list[str]) -> list[Recomendacao]:
        """Gera recomendacoes para multiplos tickers, ordenadas por score."""
        recs = []
        for ticker in tickers:
            rec = self.analisar_ticker(ticker)
            if rec:
                recs.append(rec)
            time.sleep(0.3)

        # Ordenar: COMPRA FORTE primeiro, depois por score
        ordem_sinal = {
            "COMPRA FORTE": 0, "COMPRA": 1, "NEUTRO": 2, "CAUTELA": 3, "EVITAR": 4
        }
        recs.sort(key=lambda r: (ordem_sinal.get(r.sinal, 9), -r.score_geral))
        return recs
