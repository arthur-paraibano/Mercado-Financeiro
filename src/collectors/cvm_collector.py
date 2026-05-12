import io
import time
import zipfile

import pandas as pd
import requests
from loguru import logger

from config.settings import CVM_DFP_URL, CVM_ITR_URL, CVM_DELAY


# Mapeamento de contas contabeis CVM -> campos do sistema
CONTAS_DRE = {
    "3.01":  "receita_liquida",
    "3.02":  "custo_produtos",
    "3.03":  "lucro_bruto",
    "3.04":  "despesas_operacionais",
    "3.05":  "ebit",
    "3.06":  "resultado_financeiro",
    "3.08":  "lucro_antes_ir",
    "3.11":  "lucro_liquido",
}

CONTAS_BPA = {
    "1":       "ativo_total",
    "1.01":    "ativo_circulante",
    "1.01.01": "caixa_equivalentes",
    "1.02":    "ativo_nao_circulante",
}

CONTAS_BPP = {
    "2":    "passivo_total",
    "2.01": "passivo_circulante",
    "2.03": "patrimonio_liquido",
}

CONTAS_DFC = {
    "6.01": "fcf_operacional",
    "6.02": "fcf_investimento",
    "6.03": "fcf_financiamento",
}


class CVMCollector:
    """Coleta e processa dados da CVM (DFP e ITR)."""

    def _download_csv(self, url: str) -> pd.DataFrame:
        """Baixa CSV (possivelmente zipado) da CVM."""
        logger.info(f"Baixando: {url}")
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        time.sleep(CVM_DELAY)

        if url.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                csvs = [f for f in z.namelist() if f.endswith(".csv")]
                if not csvs:
                    raise ValueError(f"Nenhum CSV encontrado no ZIP: {url}")
                with z.open(csvs[0]) as f:
                    return pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
        else:
            return pd.read_csv(
                io.BytesIO(resp.content), sep=";", encoding="latin-1", dtype=str
            )

    def get_dfp_ano(self, ano: int) -> dict[str, pd.DataFrame]:
        """
        Baixa DFP anual da CVM.
        Retorna: {"dre": df, "bpa": df, "bpp": df, "dfc": df}
        """
        demos = {
            "dre": f"{CVM_DFP_URL}/dfp_cia_aberta_DRE_con_{ano}.zip",
            "bpa": f"{CVM_DFP_URL}/dfp_cia_aberta_BPA_con_{ano}.zip",
            "bpp": f"{CVM_DFP_URL}/dfp_cia_aberta_BPP_con_{ano}.zip",
            "dfc": f"{CVM_DFP_URL}/dfp_cia_aberta_DFC_MI_con_{ano}.zip",
        }

        resultado = {}
        for nome, url in demos.items():
            try:
                df = self._download_csv(url)
                resultado[nome] = df
                logger.info(f"DFP {ano} - {nome}: {len(df)} linhas")
            except Exception as e:
                logger.warning(f"Erro ao baixar DFP {nome} {ano}: {e}")

        return resultado

    def get_itr_ano(self, ano: int) -> dict[str, pd.DataFrame]:
        """Baixa todos os ITR (trimestrais) do ano."""
        demos = {
            "dre": f"{CVM_ITR_URL}/itr_cia_aberta_DRE_con_{ano}.zip",
            "bpa": f"{CVM_ITR_URL}/itr_cia_aberta_BPA_con_{ano}.zip",
            "bpp": f"{CVM_ITR_URL}/itr_cia_aberta_BPP_con_{ano}.zip",
            "dfc": f"{CVM_ITR_URL}/itr_cia_aberta_DFC_MI_con_{ano}.zip",
        }

        resultado = {}
        for nome, url in demos.items():
            try:
                df = self._download_csv(url)
                resultado[nome] = df
                logger.info(f"ITR {ano} - {nome}: {len(df)} linhas")
            except Exception as e:
                logger.warning(f"Erro ao baixar ITR {nome} {ano}: {e}")

        return resultado

    def extrair_dre_empresa(self, df_dre: pd.DataFrame, cnpj: str) -> dict:
        """Extrai campos da DRE para uma empresa pelo CNPJ."""
        df = df_dre[df_dre["CNPJ_CIA"] == cnpj].copy()
        if df.empty:
            return {}

        # Pegar apenas versao mais recente (ORDEM_EXERC == ULTIMO)
        if "ORDEM_EXERC" in df.columns:
            df = df[df["ORDEM_EXERC"] == "ÚLTIMO"]

        df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")

        resultado = {}
        for codigo, campo in CONTAS_DRE.items():
            linhas = df[df["CD_CONTA"] == codigo]["VL_CONTA"]
            resultado[campo] = float(linhas.values[0]) if len(linhas) > 0 else None

        return resultado

    def extrair_balanco_empresa(
        self, df_bpa: pd.DataFrame, df_bpp: pd.DataFrame, cnpj: str
    ) -> dict:
        """Extrai balanco patrimonial para uma empresa."""
        resultado = {}

        for df_raw, mapa in [(df_bpa, CONTAS_BPA), (df_bpp, CONTAS_BPP)]:
            df = df_raw[df_raw["CNPJ_CIA"] == cnpj].copy()
            if df.empty:
                continue
            if "ORDEM_EXERC" in df.columns:
                df = df[df["ORDEM_EXERC"] == "ÚLTIMO"]
            df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")

            for codigo, campo in mapa.items():
                linhas = df[df["CD_CONTA"] == codigo]["VL_CONTA"]
                resultado[campo] = float(linhas.values[0]) if len(linhas) > 0 else None

        return resultado

    def extrair_dfc_empresa(self, df_dfc: pd.DataFrame, cnpj: str) -> dict:
        """Extrai fluxo de caixa para uma empresa."""
        df = df_dfc[df_dfc["CNPJ_CIA"] == cnpj].copy()
        if df.empty:
            return {}
        if "ORDEM_EXERC" in df.columns:
            df = df[df["ORDEM_EXERC"] == "ÚLTIMO"]
        df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")

        resultado = {}
        for codigo, campo in CONTAS_DFC.items():
            linhas = df[df["CD_CONTA"] == codigo]["VL_CONTA"]
            resultado[campo] = float(linhas.values[0]) if len(linhas) > 0 else None

        return resultado
