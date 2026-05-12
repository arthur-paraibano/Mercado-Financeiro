import yfinance as yf
import pandas as pd
from loguru import logger


class YahooCollector:
    """Coleta dados via Yahoo Finance (yfinance). Tickers BR usam sufixo .SA."""

    @staticmethod
    def _ticker_sa(ticker: str) -> str:
        """Adiciona .SA se nao tiver."""
        t = ticker.upper().strip()
        return t if t.endswith(".SA") else f"{t}.SA"

    def get_dividendos(self, ticker: str) -> pd.DataFrame:
        """
        Retorna historico completo de dividendos.
        Colunas: Data, Valor
        """
        try:
            acao = yf.Ticker(self._ticker_sa(ticker))
            divs = acao.dividends
            if divs.empty:
                return pd.DataFrame()

            df = divs.reset_index()
            df.columns = ["Data", "Valor"]
            df["Data"] = pd.to_datetime(df["Data"]).dt.tz_localize(None)
            df = df.sort_values("Data", ascending=False).reset_index(drop=True)
            return df
        except Exception as e:
            logger.error(f"Erro Yahoo dividendos [{ticker}]: {e}")
            return pd.DataFrame()
