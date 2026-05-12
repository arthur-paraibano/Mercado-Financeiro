import requests
import pandas as pd
from loguru import logger


# Mapeamento setorial B3 (empresas principais por setor)
SETORES_B3 = {
    "Petroleo e Gas":       ["PETR3", "PETR4", "PRIO3", "RECV3", "RRRP3"],
    "Mineracao e Siderurgia":["VALE3", "CSNA3", "GGBR4", "USIM5", "GOAU4"],
    "Financeiro":           ["ITUB4", "BBAS3", "BBDC4", "SANB11", "BPAC11", "ITSA4"],
    "Energia Eletrica":     ["EGIE3", "ENGI11", "CPFE3", "TAEE11", "CMIG4", "EQTL3", "ENEV3"],
    "Varejo":               ["MGLU3", "LREN3", "PETZ3", "ARZZ3"],
    "Agronegocio":          ["SLCE3", "BEEF3", "SMTO3", "AGRO3", "JBSS3", "BRFS3", "MRFG3"],
    "Saude":                ["RDOR3", "HAPV3", "FLRY3", "HYPE3"],
    "Telecomunicacoes":     ["VIVT3", "TIMS3"],
    "Papel e Celulose":     ["SUZB3", "KLBN11"],
    "Tecnologia":           ["TOTS3", "LWSA3"],
    "Bancos":               ["ITUB4", "BBAS3", "BBDC4", "SANB11"],
    "Seguros":              ["BBSE3", "PSSA3"],
    "Construcao Civil":     ["CYRE3", "MRVE3", "EZTC3"],
    "Transporte e Logistica":["CCRO3", "RENT3", "AZUL4", "EMBR3"],
    "Utilidades Publicas":  ["SBSP3", "SAPR11", "CSMG3"],
    "Shopping e Imobiliario":["MULT3", "IGTI11"],
    "Alimentos e Bebidas":  ["ABEV3", "NTCO3"],
}


def get_setor_do_ticker(ticker: str) -> str | None:
    """Retorna o setor de um ticker com base no mapeamento."""
    for setor, tickers in SETORES_B3.items():
        if ticker.upper() in tickers:
            return setor
    return None


class B3Collector:
    """Coleta dados publicos da B3."""

    def get_composicao_ibovespa(self) -> pd.DataFrame:
        """
        Retorna composicao atual do Ibovespa.
        Colunas: ticker, nome, tipo, qtd_teorica, peso
        """
        # A B3 usa um payload base64 na URL. Este e o padrao para IBOV, segmento 1, pagina 1, 120 itens.
        url = (
            "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/"
            "GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwi"
            "cGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQk9WIiwic2VnbWVudCI6IjEifQ=="
        )
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            acoes = data.get("results", [])
            if not acoes:
                logger.warning("Composicao do Ibovespa vazia.")
                return pd.DataFrame()

            df = pd.DataFrame(acoes)

            # Mapear colunas conhecidas
            rename = {
                "cod": "ticker",
                "asset": "nome",
                "type": "tipo",
                "theoricalQty": "qtd_teorica",
                "part": "peso",
            }
            df = df.rename(
                columns={k: v for k, v in rename.items() if k in df.columns}
            )

            # Converter peso (pode vir como string "1,234")
            if "peso" in df.columns:
                df["peso"] = (
                    df["peso"]
                    .astype(str)
                    .str.replace(",", ".")
                    .astype(float, errors="ignore")
                )

            # Adicionar setor
            if "ticker" in df.columns:
                df["setor"] = df["ticker"].apply(get_setor_do_ticker)

            logger.info(f"Ibovespa: {len(df)} acoes carregadas.")
            return df
        except Exception as e:
            logger.error(f"Erro ao buscar composicao do Ibovespa: {e}")
            return pd.DataFrame()
