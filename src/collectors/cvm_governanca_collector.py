from loguru import logger


# Nivel de listagem da B3 e seus direitos minimos
NIVEL_LISTAGEM = {
    "NM":  {"nome": "Novo Mercado",   "tag_along": 100, "free_float_min": 25, "score_base": 90},
    "N2":  {"nome": "Nivel 2",        "tag_along": 100, "free_float_min": 25, "score_base": 80},
    "N1":  {"nome": "Nivel 1",        "tag_along": 80,  "free_float_min": 25, "score_base": 65},
    "N1|N2": {"nome": "Nivel 1/2",    "tag_along": 90,  "free_float_min": 25, "score_base": 72},
    "MA":  {"nome": "Bovespa Mais",   "tag_along": 100, "free_float_min": 25, "score_base": 75},
    "MB":  {"nome": "Bovespa Mais 2", "tag_along": 100, "free_float_min": 10, "score_base": 70},
    "TR":  {"nome": "Tradicional",    "tag_along": 80,  "free_float_min": 0,  "score_base": 40},
}

# Mapeamento de empresas conhecidas para nivel de listagem
EMPRESAS_NIVEL = {
    # Novo Mercado
    "WEGE3": "NM", "RDOR3": "NM", "TOTS3": "NM", "EQTL3": "NM",
    "RENT3": "NM", "LREN3": "NM", "CYRE3": "NM", "MRVE3": "NM",
    "B3SA3": "NM", "HAPV3": "NM", "PETZ3": "NM", "LWSA3": "NM",
    "PRIO3": "NM", "ENEV3": "NM", "SLCE3": "NM", "FLRY3": "NM",
    "RADL3": "NM", "MULT3": "NM", "COGN3": "NM", "MGLU3": "NM",
    "BBSE3": "NM", "CCRO3": "NM", "HYPE3": "NM", "SMTO3": "NM",
    "VIVT3": "NM", "TIMS3": "NM", "EMBR3": "NM", "NTCO3": "NM",
    "IGTI11": "NM", "ABEV3": "NM", "JBSS3": "NM", "BRFS3": "NM",
    "MRFG3": "NM",
    # Nivel 1
    "ITUB4": "N1", "BBDC4": "N1", "ITSA4": "N1", "GGBR4": "N1",
    "GOAU4": "N1", "USIM5": "N1", "CMIG4": "N1", "KLBN11": "N1",
    # Nivel 2
    "SANB11": "N2", "ENGI11": "N2", "TAEE11": "N2", "SAPR11": "N2",
    # Tradicional
    "PETR4": "TR", "PETR3": "TR", "VALE3": "NM", "BBAS3": "NM",
    "CSNA3": "TR", "AZUL4": "N2", "BEEF3": "NM", "CPFE3": "NM",
    "EGIE3": "NM", "CSAN3": "NM", "SUZB3": "NM", "UGPA3": "NM",
    "VBBR3": "NM", "RECV3": "NM", "BPAC11": "N2",
}


class CVMGovernancaCollector:
    """Avalia governanca corporativa das empresas."""

    def get_nivel_listagem(self, ticker: str) -> str:
        """Retorna nivel de listagem do ticker."""
        return EMPRESAS_NIVEL.get(ticker.upper(), "TR")

    def calcular_score_governanca(
        self,
        ticker: str,
        nivel_listagem: str | None = None,
        free_float: float = 30.0,
        dados_adicionais: dict | None = None,
    ) -> dict:
        """Calcula score de governanca (0-100)."""
        if nivel_listagem is None:
            nivel_listagem = self.get_nivel_listagem(ticker)

        nivel = nivel_listagem.upper().strip()
        config = NIVEL_LISTAGEM.get(nivel, NIVEL_LISTAGEM["TR"])

        score = config["score_base"]
        ajustes = []

        # Free float
        if free_float >= 50:
            score += 5
            ajustes.append(f"+5 free float alto ({free_float:.0f}%)")
        elif free_float < 15:
            score -= 5
            ajustes.append(f"-5 free float baixo ({free_float:.0f}%)")

        if dados_adicionais:
            pct_indep = dados_adicionais.get("pct_independentes", 0)
            if pct_indep >= 50:
                score += 5
                ajustes.append(f"+5 conselho independente ({pct_indep:.0f}%)")
            elif pct_indep < 20:
                score -= 5
                ajustes.append(f"-5 poucos independentes ({pct_indep:.0f}%)")

            if dados_adicionais.get("tem_comite_auditoria"):
                score += 3
                ajustes.append("+3 comite de auditoria")

            if dados_adicionais.get("tem_politica_dividendos"):
                score += 2
                ajustes.append("+2 politica de dividendos")

        score = max(0, min(100, score))

        return {
            "ticker": ticker,
            "nivel": config["nome"],
            "nivel_codigo": nivel,
            "tag_along": config["tag_along"],
            "score_base": config["score_base"],
            "score_final": score,
            "ajustes": ajustes,
        }

    def comparar_governanca(self, tickers: list[str]) -> list[dict]:
        """Compara governanca de multiplos tickers."""
        resultados = []
        for ticker in tickers:
            resultados.append(self.calcular_score_governanca(ticker))
        return sorted(resultados, key=lambda x: x["score_final"], reverse=True)
