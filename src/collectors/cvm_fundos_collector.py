import io
import zipfile

import pandas as pd
import requests
from loguru import logger


class CVMFundosCollector:
    """
    Coleta carteiras mensais dos fundos de investimento via CVM.
    Fonte: https://dados.cvm.gov.br/dataset/fi-doc-cda
    """

    BASE_CDA = "https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS"
    BASE_CADASTRO = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"

    def get_cadastro_fundos(self) -> pd.DataFrame:
        """Retorna cadastro de todos os fundos registrados na CVM."""
        try:
            logger.info("Baixando cadastro de fundos da CVM...")
            df = pd.read_csv(
                self.BASE_CADASTRO,
                sep=";", encoding="latin-1", dtype=str,
                on_bad_lines="skip",
            )
            logger.info(f"Cadastro de fundos: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Erro ao baixar cadastro de fundos: {e}")
            return pd.DataFrame()

    def get_carteira_mensal(self, ano: int, mes: int) -> pd.DataFrame:
        """
        Baixa carteiras de acoes de todos os fundos para um mes.
        Retorna DataFrame com posicoes em acoes.
        """
        mes_str = f"{mes:02d}"
        url = f"{self.BASE_CDA}/cda_fi_{ano}{mes_str}.zip"

        try:
            logger.info(f"Baixando carteiras {ano}/{mes_str}...")
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()

            dfs = []
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                for nome_arq in z.namelist():
                    if nome_arq.endswith(".csv"):
                        with z.open(nome_arq) as f:
                            try:
                                df = pd.read_csv(
                                    f, sep=";", encoding="latin-1",
                                    dtype=str, on_bad_lines="skip",
                                )
                                dfs.append(df)
                            except Exception:
                                continue

            if not dfs:
                return pd.DataFrame()

            df_total = pd.concat(dfs, ignore_index=True)

            # Converter valores numericos
            for col in ["VL_MERC_POS_FINAL", "QT_POS_FINAL", "VL_CUSTO_POS_FINAL"]:
                if col in df_total.columns:
                    df_total[col] = pd.to_numeric(
                        df_total[col].str.replace(",", "."), errors="coerce"
                    )

            logger.info(f"Carteiras {ano}/{mes_str}: {len(df_total)} posicoes")
            return df_total
        except requests.HTTPError as e:
            logger.error(f"Erro HTTP carteiras {ano}/{mes_str}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Erro carteiras {ano}/{mes_str}: {e}")
            return pd.DataFrame()

    def filtrar_acoes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra apenas posicoes em acoes (TP_APLIC ou TP_ATIVO)."""
        if df.empty:
            return df

        # Identificar coluna de tipo de ativo
        if "TP_APLIC" in df.columns:
            mask = df["TP_APLIC"].fillna("").str.contains("Ações|acao|ACAO", case=False, na=False)
            return df[mask].copy()
        elif "TP_ATIVO" in df.columns:
            mask = df["TP_ATIVO"].fillna("").str.contains("Ações|acao|ACAO", case=False, na=False)
            return df[mask].copy()

        return df

    def filtrar_por_ticker(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Filtra posicoes que contem o ticker (busca parcial em CD_ATIVO ou DS_ATIVO)."""
        ticker_base = ticker.replace(".SA", "").upper().strip()

        mask = pd.Series([False] * len(df))
        for col in ["CD_ATIVO", "DS_ATIVO", "NM_FUNDO_COTA"]:
            if col in df.columns:
                mask = mask | df[col].fillna("").str.upper().str.contains(ticker_base, na=False)

        return df[mask].copy()

    def ranking_fundos_por_acao(
        self, df: pd.DataFrame, ticker: str, top_n: int = 20
    ) -> pd.DataFrame:
        """Retorna os N fundos com maior posicao em uma acao."""
        df_filtrado = self.filtrar_por_ticker(df, ticker)

        if df_filtrado.empty:
            return pd.DataFrame()

        col_valor = "VL_MERC_POS_FINAL" if "VL_MERC_POS_FINAL" in df_filtrado.columns else None
        col_fundo = "CNPJ_FUNDO" if "CNPJ_FUNDO" in df_filtrado.columns else None

        if not col_valor or not col_fundo:
            return pd.DataFrame()

        df_agg = (
            df_filtrado
            .groupby(col_fundo)
            .agg(valor_total=(col_valor, "sum"))
            .reset_index()
            .sort_values("valor_total", ascending=False)
            .head(top_n)
        )

        return df_agg

    def detectar_movimentacoes(
        self,
        carteira_atual: pd.DataFrame,
        carteira_anterior: pd.DataFrame,
        ticker: str,
    ) -> pd.DataFrame:
        """Compara dois meses para detectar fundos que compraram/venderam."""
        col_fundo = "CNPJ_FUNDO"
        col_valor = "VL_MERC_POS_FINAL"

        atual = self.filtrar_por_ticker(carteira_atual, ticker)
        anterior = self.filtrar_por_ticker(carteira_anterior, ticker)

        if col_fundo not in atual.columns or col_valor not in atual.columns:
            return pd.DataFrame()

        val_atual = atual.groupby(col_fundo)[col_valor].sum()
        val_anterior = anterior.groupby(col_fundo)[col_valor].sum() if not anterior.empty else pd.Series(dtype=float)

        todos_fundos = val_atual.index.union(val_anterior.index)
        movimentos = []

        for cnpj in todos_fundos:
            v_atual = val_atual.get(cnpj, 0) or 0
            v_ant = val_anterior.get(cnpj, 0) or 0
            variacao = v_atual - v_ant

            if abs(variacao) > 500_000:
                movimentos.append({
                    "cnpj_fundo": cnpj,
                    "valor_anterior": v_ant,
                    "valor_atual": v_atual,
                    "variacao": variacao,
                    "tipo": "COMPRA" if variacao > 0 else "VENDA",
                })

        df = pd.DataFrame(movimentos)
        if not df.empty:
            df = df.sort_values("variacao", key=abs, ascending=False)
        return df
