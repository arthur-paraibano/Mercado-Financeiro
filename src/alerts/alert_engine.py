import time
from typing import Dict, List

from loguru import logger

from src.collectors.b3_collector import SETORES_B3, get_setor_do_ticker
from src.collectors.bcb_collector import BCBCollector
from src.collectors.fundamentus_collector import FundamentusCollector
from src.models.alert import Alerta
from src.processors.cross_analyzer import CrossAnalyzer


class AlertEngine:
    """Orquestra todos os cruzamentos de dados e consolida alertas."""

    def __init__(self):
        self.analyzer = CrossAnalyzer()
        self.fund = FundamentusCollector()
        self.bcb = BCBCollector()
        self._macro_cache: Dict = {}
        self._setor_cache: Dict[str, List[dict]] = {}

    def _obter_macro(self) -> dict:
        """Obtem dados macro atuais. Retorna cache ou valores padrao se BCB offline."""
        if self._macro_cache:
            return self._macro_cache

        try:
            selic_df = self.bcb.get_selic("01/01/2024")
            cambio_df = self.bcb.get_cambio_dolar("01/01/2024")

            selic_atual = float(selic_df["valor"].iloc[-1]) if not selic_df.empty else 0
            selic_6m = (
                float(selic_df["valor"].iloc[-130])
                if len(selic_df) > 130
                else selic_atual
            )
            cambio_atual = float(cambio_df["valor"].iloc[-1]) if not cambio_df.empty else 0
            cambio_6m = (
                float(cambio_df["valor"].iloc[-130])
                if len(cambio_df) > 130
                else cambio_atual
            )
        except Exception:
            logger.warning("BCB indisponivel. Usando valores padrao para macro.")
            selic_atual = 14.25
            selic_6m = 13.25
            cambio_atual = 5.70
            cambio_6m = 5.40

        self._macro_cache = {
            "selic_atual": selic_atual,
            "selic_6m_atras": selic_6m,
            "cambio_atual": cambio_atual,
            "cambio_6m_atras": cambio_6m,
        }
        return self._macro_cache

    def _obter_mediana_setor(self, setor: str) -> dict:
        """Calcula mediana dos indicadores do setor usando cache."""
        if setor in self._setor_cache:
            return self._setor_cache[setor]

        tickers = SETORES_B3.get(setor, [])
        if not tickers:
            return {}

        dados_setor = []
        for t in tickers:
            try:
                d = self.fund.get_papel(t)
                dados_setor.append(d)
                time.sleep(0.3)
            except Exception:
                continue

        if not dados_setor:
            return {}

        import statistics

        mediana = {}
        for campo in ["pl", "pvp", "ev_ebitda", "roe", "dividend_yield", "margem_liquida"]:
            valores = [d[campo] for d in dados_setor if d.get(campo) and d[campo] > 0]
            if valores:
                mediana[campo] = statistics.median(valores)

        self._setor_cache[setor] = mediana
        return mediana

    def analisar_ticker(self, ticker: str) -> List[Alerta]:
        """Executa todos os cruzamentos para um ticker."""
        todos = []

        # Buscar dados do Fundamentus
        try:
            dados = self.fund.get_papel(ticker)
        except Exception as e:
            logger.error(f"[{ticker}] Erro Fundamentus: {e}")
            return []

        macro = self._obter_macro()
        setor = (
            dados.get("setor")
            or get_setor_do_ticker(ticker)
            or ""
        )

        # Cruzamento 1: Saude Financeira
        todos += self.analyzer.analisar_saude_financeira(ticker, dados)

        # Cruzamento 2: Divergencia nos Resultados
        todos += self.analyzer.analisar_divergencia_lucro_resultados(ticker, dados)

        # Cruzamento 3: Valuation vs Setor
        setor_b3 = get_setor_do_ticker(ticker)
        if setor_b3:
            mediana = self._obter_mediana_setor(setor_b3)
            if mediana:
                todos += self.analyzer.analisar_valuation_vs_setor(
                    ticker, dados, mediana, setor_b3
                )

        # Cruzamento 4: Impacto Macro
        setor_para_macro = setor_b3 or setor
        todos += self.analyzer.analisar_impacto_macro(ticker, setor_para_macro, macro)

        # Cruzamento 5: Dividendos
        todos += self.analyzer.analisar_dividendos(
            ticker, dados, macro.get("selic_atual", 14.25)
        )

        # Ordenar por severidade
        ordem = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "INFO": 3}
        todos.sort(key=lambda a: ordem.get(a.severidade, 9))

        logger.info(f"[{ticker}] {len(todos)} alertas gerados.")
        return todos

    def analisar_multiplos(self, tickers: List[str]) -> Dict[str, List[Alerta]]:
        """Analisa multiplos tickers. Retorna dict ticker -> alertas."""
        resultado = {}
        for ticker in tickers:
            resultado[ticker] = self.analisar_ticker(ticker)
            time.sleep(0.3)
        return resultado
