import time
from typing import List

import pandas as pd
from loguru import logger

from src.collectors.cvm_fundos_collector import CVMFundosCollector


# Gestoras consideradas 'smart money'
GESTORAS_REFERENCIA = [
    "DYNAMO", "SPX", "VERDE", "GAP", "KAPITALO",
    "CONSTELLATION", "MOAT", "SQUADRA", "GUEPARDO",
    "ATMOS", "BRASIL CAPITAL", "OPPORTUNITY", "VINCI",
    "BTG", "ITAU", "BRADESCO", "XP", "SAFRA",
]


class SmartMoneyAnalyzer:
    """Analisa movimentacoes de grandes fundos para identificar tendencias."""

    def __init__(self):
        self.cvm = CVMFundosCollector()

    def analisar_concentracao(self, df_carteira: pd.DataFrame, ticker: str) -> dict:
        """Analisa concentracao de fundos em uma acao."""
        df_ticker = self.cvm.filtrar_por_ticker(df_carteira, ticker)

        col_fundo = "CNPJ_FUNDO"
        col_valor = "VL_MERC_POS_FINAL"

        if df_ticker.empty or col_fundo not in df_ticker.columns:
            return {
                "ticker": ticker, "num_fundos": 0,
                "valor_total": 0, "concentracao_top5_pct": 0,
                "risco_concentracao": "DESCONHECIDO",
            }

        num_fundos = df_ticker[col_fundo].nunique()
        valor_total = df_ticker[col_valor].sum() if col_valor in df_ticker.columns else 0
        top5_valor = (
            df_ticker.groupby(col_fundo)[col_valor].sum()
            .nlargest(5).sum()
            if col_valor in df_ticker.columns else 0
        )
        concentracao = (top5_valor / valor_total * 100) if valor_total > 0 else 0

        if concentracao > 70:
            risco = "ALTO"
        elif concentracao > 50:
            risco = "MEDIO"
        else:
            risco = "BAIXO"

        return {
            "ticker": ticker,
            "num_fundos": num_fundos,
            "valor_total": valor_total,
            "concentracao_top5_pct": round(concentracao, 2),
            "risco_concentracao": risco,
        }

    def identificar_smart_money(
        self,
        df_carteira: pd.DataFrame,
        cadastro: pd.DataFrame,
        ticker: str,
    ) -> pd.DataFrame:
        """Identifica gestoras de referencia com posicao no ticker."""
        df_ticker = self.cvm.filtrar_por_ticker(df_carteira, ticker)

        if df_ticker.empty or cadastro.empty:
            return pd.DataFrame()

        col_fundo = "CNPJ_FUNDO"
        if col_fundo not in df_ticker.columns or col_fundo not in cadastro.columns:
            return pd.DataFrame()

        # Juntar com cadastro para obter nome da gestora
        col_gestor = None
        for col in ["GESTOR", "NM_GESTOR", "ADMIN"]:
            if col in cadastro.columns:
                col_gestor = col
                break

        col_nome = None
        for col in ["DENOM_SOCIAL", "NM_FANTASIA", "NOME_FUNDO"]:
            if col in cadastro.columns:
                col_nome = col
                break

        if not col_gestor and not col_nome:
            return pd.DataFrame()

        cols_merge = [col_fundo]
        if col_gestor:
            cols_merge.append(col_gestor)
        if col_nome:
            cols_merge.append(col_nome)

        df_merged = df_ticker.merge(
            cadastro[cols_merge].drop_duplicates(subset=[col_fundo]),
            on=col_fundo, how="left",
        )

        # Filtrar gestoras de referencia
        resultados = []
        for gestora in GESTORAS_REFERENCIA:
            mask = pd.Series([False] * len(df_merged))
            if col_gestor and col_gestor in df_merged.columns:
                mask = mask | df_merged[col_gestor].fillna("").str.upper().str.contains(gestora)
            if col_nome and col_nome in df_merged.columns:
                mask = mask | df_merged[col_nome].fillna("").str.upper().str.contains(gestora)

            matches = df_merged[mask]
            if not matches.empty:
                valor = matches["VL_MERC_POS_FINAL"].sum() if "VL_MERC_POS_FINAL" in matches.columns else 0
                resultados.append({
                    "gestora": gestora,
                    "num_fundos": matches[col_fundo].nunique(),
                    "valor_total": valor,
                    "fundos": matches[col_nome].unique().tolist()[:3] if col_nome in matches.columns else [],
                })

        df_result = pd.DataFrame(resultados)
        if not df_result.empty:
            df_result = df_result.sort_values("valor_total", ascending=False)
        return df_result
