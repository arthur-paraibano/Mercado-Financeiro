import numpy as np
import pandas as pd


class TechnicalCalculator:
    """Calcula indicadores tecnicos a partir de serie OHLCV."""

    @staticmethod
    def calcular_todos(df: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe DataFrame com colunas: date, open, high, low, close, volume.
        Retorna DataFrame com indicadores tecnicos adicionados.
        """
        df = df.copy().sort_values("date").reset_index(drop=True)
        close = df["close"]
        volume = df["volume"]

        # --- Medias Moveis ---
        df["sma_20"] = close.rolling(window=20).mean()
        df["sma_50"] = close.rolling(window=50).mean()
        df["sma_200"] = close.rolling(window=200).mean()
        df["ema_9"] = close.ewm(span=9, adjust=False).mean()
        df["ema_21"] = close.ewm(span=21, adjust=False).mean()

        # --- RSI (14 periodos) ---
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # --- MACD (12, 26, 9) ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # --- Bollinger Bands (20, 2) ---
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        df["bollinger_upper"] = sma20 + (2 * std20)
        df["bollinger_lower"] = sma20 - (2 * std20)
        df["bollinger_mid"] = sma20

        # --- Volume ---
        df["volume_sma_20"] = volume.rolling(window=20).mean()
        df["volume_ratio"] = volume / df["volume_sma_20"]

        # --- ATR (Average True Range) ---
        high, low = df["high"], df["low"]
        tr = pd.concat(
            [
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs(),
            ],
            axis=1,
        ).max(axis=1)
        df["atr_14"] = tr.rolling(window=14).mean()

        return df

    @staticmethod
    def gerar_sinais(df: pd.DataFrame) -> dict:
        """Analisa a ultima linha do DataFrame e retorna sinais."""
        if df.empty or len(df) < 30:
            return {}

        ultima = df.iloc[-1]
        penultima = df.iloc[-2]
        sinais = {}

        # RSI
        rsi = ultima.get("rsi_14")
        if pd.notna(rsi):
            if rsi < 30:
                sinais["RSI"] = {"sinal": "COMPRA", "valor": round(rsi, 2), "desc": "Sobrevenda (RSI < 30)"}
            elif rsi > 70:
                sinais["RSI"] = {"sinal": "VENDA", "valor": round(rsi, 2), "desc": "Sobrecompra (RSI > 70)"}
            else:
                sinais["RSI"] = {"sinal": "NEUTRO", "valor": round(rsi, 2), "desc": f"RSI neutro em {rsi:.1f}"}

        # MACD cruzamento
        macd_a = ultima.get("macd")
        macd_s_a = ultima.get("macd_signal")
        macd_p = penultima.get("macd")
        macd_s_p = penultima.get("macd_signal")

        if all(pd.notna(v) for v in [macd_a, macd_s_a, macd_p, macd_s_p]):
            if macd_p < macd_s_p and macd_a > macd_s_a:
                sinais["MACD"] = {"sinal": "COMPRA", "valor": round(macd_a, 4), "desc": "MACD cruzou acima do sinal"}
            elif macd_p > macd_s_p and macd_a < macd_s_a:
                sinais["MACD"] = {"sinal": "VENDA", "valor": round(macd_a, 4), "desc": "MACD cruzou abaixo do sinal"}
            else:
                direcao = "positivo" if macd_a > macd_s_a else "negativo"
                sinais["MACD"] = {"sinal": "NEUTRO", "valor": round(macd_a, 4), "desc": f"MACD {direcao}"}

        # Cruzamento de medias
        close = ultima.get("close")
        sma50 = ultima.get("sma_50")
        sma200 = ultima.get("sma_200")

        if all(pd.notna(v) for v in [close, sma50]):
            if pd.notna(sma200) and close > sma200 and sma50 > sma200:
                sinais["MEDIAS"] = {"sinal": "COMPRA", "valor": round(close, 2), "desc": "Preco e SMA50 acima da SMA200 (tendencia de alta)"}
            elif pd.notna(sma200) and close < sma200:
                sinais["MEDIAS"] = {"sinal": "VENDA", "valor": round(close, 2), "desc": "Preco abaixo da SMA200 (tendencia de baixa)"}
            elif close > sma50:
                sinais["MEDIAS"] = {"sinal": "COMPRA", "valor": round(close, 2), "desc": "Preco acima da SMA50"}
            else:
                sinais["MEDIAS"] = {"sinal": "VENDA", "valor": round(close, 2), "desc": "Preco abaixo da SMA50"}

        # Bollinger Bands
        boll_lower = ultima.get("bollinger_lower")
        boll_upper = ultima.get("bollinger_upper")
        if all(pd.notna(v) for v in [close, boll_lower, boll_upper]):
            if close <= boll_lower:
                sinais["BOLLINGER"] = {"sinal": "COMPRA", "valor": round(close, 2), "desc": "Preco na banda inferior de Bollinger"}
            elif close >= boll_upper:
                sinais["BOLLINGER"] = {"sinal": "VENDA", "valor": round(close, 2), "desc": "Preco na banda superior de Bollinger"}
            else:
                sinais["BOLLINGER"] = {"sinal": "NEUTRO", "valor": round(close, 2), "desc": "Preco dentro das bandas"}

        # Volume anomalo
        vol_ratio = ultima.get("volume_ratio")
        if pd.notna(vol_ratio) and vol_ratio > 2.5:
            sinais["VOLUME"] = {"sinal": "ATENCAO", "valor": round(vol_ratio, 2), "desc": f"Volume {vol_ratio:.1f}x acima da media"}

        return sinais
