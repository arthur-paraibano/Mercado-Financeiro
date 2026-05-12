import time

import requests
from loguru import logger

from config.settings import BRAPI_TOKEN, BRAPI_BASE_URL, BRAPI_DELAY


class BrapiCollector:
    """Coleta dados de cotacao e indicadores da brapi.dev."""

    def __init__(self):
        self.session = requests.Session()
        self.token = BRAPI_TOKEN

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{BRAPI_BASE_URL}/{endpoint}"
        if params is None:
            params = {}
        if self.token:
            params["token"] = self.token
        try:
            resp = self.session.get(url, params=params, timeout=15)
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
        """Retorna cotacao atual e indicadores fundamentalistas de um ticker."""
        data = self._get(f"quote/{ticker}", params={"fundamental": "true"})
        results = data.get("results", [])
        if not results:
            raise ValueError(f"Ticker {ticker} nao encontrado na brapi.")
        return results[0]

    def get_cotacao_lote(self, tickers: list[str]) -> dict[str, dict]:
        """
        Retorna cotacoes de varios tickers numa unica chamada (muito mais rapido).
        Endpoint aceita varios tickers separados por virgula.
        Retorna dict ticker -> dados (sem fundamentos por padrao).
        """
        if not tickers:
            return {}
        resultado: dict[str, dict] = {}
        # Lotes de 20 para evitar URL muito longa
        for i in range(0, len(tickers), 20):
            lote = tickers[i:i + 20]
            try:
                data = self._get("quote/" + ",".join(lote))
                for r in data.get("results", []):
                    sym = r.get("symbol")
                    if sym:
                        resultado[sym] = r
            except Exception as e:
                logger.warning(f"Erro lote {lote}: {e}")
        return resultado

    def get_historico(self, ticker: str, periodo: str = "3mo", intervalo: str = "1d") -> list:
        """Retorna historico de cotacoes OHLCV."""
        data = self._get(
            f"quote/{ticker}",
            params={"range": periodo, "interval": intervalo},
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
