import requests
import pandas as pd
from loguru import logger


# Codigos dos agregados IBGE
AGREGADOS = {
    "IPCA_GRUPOS":        7060,
    "PIB_TRIMESTRAL":     5932,
    "PRODUCAO_INDUSTRIA": 3653,
    "COMERCIO_VAREJO":    8880,
    "SERVICOS":           6442,
}


class IBGECollector:
    """Coleta dados economicos setoriais do IBGE."""

    BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

    def _get(
        self,
        agregado: int,
        periodos: str,
        variavel: int,
        localidade: str = "N1[all]",
    ) -> pd.DataFrame:
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
                nome_var = serie.get("variavel", "")
                resultados = serie.get("resultados", [])
                if not resultados:
                    continue
                for res in resultados:
                    for s in res.get("series", []):
                        for periodo, valor in s.get("serie", {}).items():
                            rows.append({
                                "periodo": periodo,
                                "valor": valor,
                                "variavel": nome_var,
                            })
            df = pd.DataFrame(rows)
            if not df.empty:
                df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
            return df
        except Exception as e:
            logger.error(f"Erro IBGE agregado {agregado}: {e}")
            return pd.DataFrame()

    def get_pib_trimestral(self, ultimos: int = 40) -> pd.DataFrame:
        """PIB trimestral - variacao percentual em relacao ao mesmo trimestre do ano anterior."""
        df = self._get(AGREGADOS["PIB_TRIMESTRAL"], f"-{ultimos}", 6561)
        if not df.empty:
            df = df.dropna(subset=["valor"])
        return df

    def get_producao_industrial(self, ultimos: int = 24) -> pd.DataFrame:
        """Indice de producao industrial mensal."""
        return self._get(AGREGADOS["PRODUCAO_INDUSTRIA"], f"-{ultimos}", 3135)

    def get_comercio_varejo(self, ultimos: int = 24) -> pd.DataFrame:
        """Volume de vendas no comercio varejista."""
        return self._get(AGREGADOS["COMERCIO_VAREJO"], f"-{ultimos}", 7168)

    def get_servicos(self, ultimos: int = 24) -> pd.DataFrame:
        """Indice de volume de servicos."""
        return self._get(AGREGADOS["SERVICOS"], f"-{ultimos}", 7167)
