import time

import pandas as pd
import requests
from loguru import logger

# Codigos das series no SGS do Banco Central
SERIES_SGS = {
    "SELIC_META":       432,
    "SELIC_EFETIVA":    11,
    "IPCA_MENSAL":      433,
    "IPCA_ACUM_12M":    13522,
    "IGPM_MENSAL":      189,
    "CDI":              4389,
    "PTAX_DOLAR":       1,
    "PIB_MENSAL":       4380,
    "DESEMPREGO":       24369,
    "PRODUCAO_IND":     21859,
}


class BCBCollector:
    """Coleta dados macroeconomicos do Banco Central do Brasil."""

    BASE_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
    BASE_EXPECTATIVAS = (
        "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata"
    )

    def _get_sgs(
        self, codigo: int, inicio: str, fim: str | None = None
    ) -> pd.DataFrame:
        """Busca serie temporal do SGS. Datas no formato dd/mm/aaaa."""
        from datetime import date

        if fim is None:
            fim = date.today().strftime("%d/%m/%Y")

        url = self.BASE_SGS.format(codigo=codigo)
        params = {
            "formato": "json",
            "dataInicial": inicio,
            "dataFinal": fim,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            time.sleep(0.5)
            data = resp.json()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)
            df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
            return df
        except Exception as e:
            logger.error(f"Erro SGS serie {codigo}: {e}")
            return pd.DataFrame()

    # --- Atalhos para series comuns ---

    def get_selic(self, inicio: str = "01/01/2015") -> pd.DataFrame:
        return self._get_sgs(SERIES_SGS["SELIC_META"], inicio)

    def get_ipca(self, inicio: str = "01/01/2015") -> pd.DataFrame:
        return self._get_sgs(SERIES_SGS["IPCA_MENSAL"], inicio)

    def get_ipca_acumulado_12m(self, inicio: str = "01/01/2015") -> pd.DataFrame:
        return self._get_sgs(SERIES_SGS["IPCA_ACUM_12M"], inicio)

    def get_cdi(self, inicio: str = "01/01/2015") -> pd.DataFrame:
        return self._get_sgs(SERIES_SGS["CDI"], inicio)

    def get_cambio_dolar(self, inicio: str = "01/01/2020") -> pd.DataFrame:
        return self._get_sgs(SERIES_SGS["PTAX_DOLAR"], inicio)

    def get_igpm(self, inicio: str = "01/01/2015") -> pd.DataFrame:
        return self._get_sgs(SERIES_SGS["IGPM_MENSAL"], inicio)

    def get_multiplas_series(
        self, nomes: list[str], inicio: str = "01/01/2020"
    ) -> dict[str, pd.DataFrame]:
        """Baixa multiplas series de uma vez. nomes = chaves de SERIES_SGS."""
        resultado = {}
        for nome in nomes:
            if nome not in SERIES_SGS:
                logger.warning(f"Serie desconhecida: {nome}")
                continue
            resultado[nome] = self._get_sgs(SERIES_SGS[nome], inicio)
        return resultado

    def get_expectativas_focus(
        self, indicador: str = "IPCA", limite: int = 100
    ) -> pd.DataFrame:
        """
        Expectativas de mercado do Boletim Focus.
        indicador: 'IPCA', 'IGP-M', 'Selic', 'PIB Total', 'Câmbio'
        """
        url = f"{self.BASE_EXPECTATIVAS}/ExpectativasMercadoAnuais"
        params = {
            "$filter": f"Indicador eq '{indicador}'",
            "$top": limite,
            "$orderby": "Data desc",
            "$format": "json",
            "$select": "Indicador,Data,DataReferencia,Mediana,Media,Minimo,Maximo",
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("value", [])
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Erro Focus {indicador}: {e}")
            return pd.DataFrame()
