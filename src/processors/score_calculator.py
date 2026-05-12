from typing import Optional


class ScoreCalculator:
    """
    Calcula scores 0-100 para cada dimensao de analise.
    100 = excelente, 0 = pessimo.
    """

    PESOS = {
        "saude": 30,
        "valuation": 25,
        "dividendos": 20,
        "crescimento": 15,
        "tecnico": 10,
    }

    # ================================================================
    # SCORE DE SAUDE FINANCEIRA (0-100)
    # ================================================================
    def score_saude(self, ind: dict) -> tuple[float, dict]:
        pts = {}

        roe = ind.get("roe") or 0
        if roe >= 20:     pts["roe"] = 25
        elif roe >= 15:   pts["roe"] = 20
        elif roe >= 10:   pts["roe"] = 15
        elif roe >= 5:    pts["roe"] = 8
        elif roe >= 0:    pts["roe"] = 3
        else:             pts["roe"] = 0

        margem = ind.get("margem_liquida") or 0
        if margem >= 20:  pts["margem"] = 20
        elif margem >= 15: pts["margem"] = 16
        elif margem >= 10: pts["margem"] = 12
        elif margem >= 5: pts["margem"] = 7
        elif margem >= 0: pts["margem"] = 2
        else:             pts["margem"] = 0

        # Divida/EBITDA estimada
        divida_liq = ind.get("divida_liquida") or 0
        ebit = ind.get("ebit_12m") or 0
        ebitda = ebit * 1.15 if ebit > 0 else 0
        if ebitda > 0 and divida_liq > 0:
            dliq = divida_liq / ebitda
        elif divida_liq <= 0:
            dliq = -1  # caixa liquido
        else:
            dliq = None

        if dliq is None:      pts["divida"] = 12
        elif dliq < 0:        pts["divida"] = 25
        elif dliq <= 1:       pts["divida"] = 22
        elif dliq <= 2:       pts["divida"] = 17
        elif dliq <= 3:       pts["divida"] = 10
        elif dliq <= 4:       pts["divida"] = 4
        else:                 pts["divida"] = 0

        m_ebit = ind.get("margem_ebit") or 0
        if m_ebit >= 30:      pts["m_ebit"] = 15
        elif m_ebit >= 20:    pts["m_ebit"] = 12
        elif m_ebit >= 10:    pts["m_ebit"] = 8
        elif m_ebit >= 0:     pts["m_ebit"] = 3
        else:                 pts["m_ebit"] = 0

        roic = ind.get("roic") or 0
        if roic >= 20:    pts["roic"] = 15
        elif roic >= 15:  pts["roic"] = 12
        elif roic >= 10:  pts["roic"] = 8
        elif roic >= 5:   pts["roic"] = 4
        elif roic >= 0:   pts["roic"] = 1
        else:             pts["roic"] = 0

        return round(sum(pts.values()), 2), pts

    # ================================================================
    # SCORE DE VALUATION (0-100)
    # ================================================================
    def score_valuation(self, ind: dict) -> tuple[float, dict]:
        pts = {}

        pl = ind.get("pl")
        if pl is None or pl <= 0: pts["pl"] = 0
        elif pl <= 8:             pts["pl"] = 30
        elif pl <= 12:            pts["pl"] = 24
        elif pl <= 18:            pts["pl"] = 18
        elif pl <= 25:            pts["pl"] = 10
        elif pl <= 40:            pts["pl"] = 4
        else:                     pts["pl"] = 0

        pvp = ind.get("pvp")
        if pvp is None or pvp <= 0: pts["pvp"] = 10
        elif pvp < 0.5:            pts["pvp"] = 20
        elif pvp <= 1.0:           pts["pvp"] = 25
        elif pvp <= 1.5:           pts["pvp"] = 20
        elif pvp <= 2.5:           pts["pvp"] = 12
        elif pvp <= 4.0:           pts["pvp"] = 5
        else:                      pts["pvp"] = 0

        ev = ind.get("ev_ebitda")
        if ev is None or ev <= 0: pts["ev"] = 10
        elif ev <= 6:             pts["ev"] = 25
        elif ev <= 9:             pts["ev"] = 20
        elif ev <= 12:            pts["ev"] = 14
        elif ev <= 18:            pts["ev"] = 7
        else:                     pts["ev"] = 0

        psr = ind.get("psr")
        if psr is None or psr <= 0: pts["psr"] = 8
        elif psr <= 0.5:           pts["psr"] = 20
        elif psr <= 1.5:           pts["psr"] = 16
        elif psr <= 3.0:           pts["psr"] = 10
        elif psr <= 5.0:           pts["psr"] = 4
        else:                      pts["psr"] = 0

        return round(sum(pts.values()), 2), pts

    # ================================================================
    # SCORE DE DIVIDENDOS (0-100)
    # ================================================================
    def score_dividendos(self, ind: dict, selic: float = 14.25) -> tuple[float, dict]:
        pts = {}

        dy = ind.get("dividend_yield") or 0
        if selic > 0:
            ratio = dy / selic
            if ratio >= 1.2:   pts["dy"] = 40
            elif ratio >= 0.9: pts["dy"] = 32
            elif ratio >= 0.6: pts["dy"] = 20
            elif ratio >= 0.3: pts["dy"] = 10
            elif dy > 0:       pts["dy"] = 4
            else:              pts["dy"] = 0
        else:
            pts["dy"] = 15 if dy > 4 else 5 if dy > 0 else 0

        # Payout estimado
        lpa = ind.get("lpa") or 0
        cotacao = ind.get("cotacao") or 0
        if lpa > 0 and cotacao > 0 and dy > 0:
            dpa = cotacao * (dy / 100)
            payout = (dpa / lpa) * 100
        else:
            payout = 0

        if payout <= 0:         pts["payout"] = 0
        elif payout <= 40:      pts["payout"] = 30
        elif payout <= 60:      pts["payout"] = 25
        elif payout <= 80:      pts["payout"] = 18
        elif payout <= 100:     pts["payout"] = 8
        else:                   pts["payout"] = 0

        # Crescimento receita 5a como proxy de consistencia
        cres = ind.get("cres_rec_5a") or 0
        if cres >= 15:    pts["consistencia"] = 30
        elif cres >= 10:  pts["consistencia"] = 24
        elif cres >= 5:   pts["consistencia"] = 18
        elif cres >= 0:   pts["consistencia"] = 10
        else:             pts["consistencia"] = 2

        return round(sum(pts.values()), 2), pts

    # ================================================================
    # SCORE DE CRESCIMENTO (0-100)
    # ================================================================
    def score_crescimento(self, ind: dict) -> tuple[float, dict]:
        pts = {}

        cres_5a = ind.get("cres_rec_5a")
        if cres_5a is None:       pts["cres_5a"] = 15
        elif cres_5a >= 20:       pts["cres_5a"] = 40
        elif cres_5a >= 12:       pts["cres_5a"] = 32
        elif cres_5a >= 7:        pts["cres_5a"] = 22
        elif cres_5a >= 3:        pts["cres_5a"] = 12
        elif cres_5a >= 0:        pts["cres_5a"] = 4
        else:                     pts["cres_5a"] = 0

        # Margem EBIT como proxy de eficiencia operacional crescente
        m_ebit = ind.get("margem_ebit") or 0
        if m_ebit >= 30:      pts["eficiencia"] = 30
        elif m_ebit >= 20:    pts["eficiencia"] = 24
        elif m_ebit >= 12:    pts["eficiencia"] = 16
        elif m_ebit >= 5:     pts["eficiencia"] = 8
        elif m_ebit >= 0:     pts["eficiencia"] = 3
        else:                 pts["eficiencia"] = 0

        # ROE como proxy de capacidade de reinvestimento
        roe = ind.get("roe") or 0
        if roe >= 25:     pts["reinvest"] = 30
        elif roe >= 18:   pts["reinvest"] = 24
        elif roe >= 12:   pts["reinvest"] = 16
        elif roe >= 5:    pts["reinvest"] = 8
        elif roe >= 0:    pts["reinvest"] = 2
        else:             pts["reinvest"] = 0

        return round(min(sum(pts.values()), 100), 2), pts

    # ================================================================
    # SCORE TECNICO (0-100)
    # ================================================================
    def score_tecnico(self, sinais: dict) -> tuple[float, dict]:
        base = 50
        detalhes = {}
        pesos = {"RSI": 25, "MACD": 25, "MEDIAS": 30, "BOLLINGER": 15, "VOLUME": 5}

        for nome, info in sinais.items():
            sinal = info.get("sinal", "NEUTRO")
            peso = pesos.get(nome, 10)

            if sinal == "COMPRA":
                base += peso * 0.5
                detalhes[nome] = f"+{peso * 0.5:.0f}"
            elif sinal == "VENDA":
                base -= peso * 0.5
                detalhes[nome] = f"-{peso * 0.5:.0f}"
            else:
                detalhes[nome] = "0"

        return round(max(0, min(100, base)), 2), detalhes

    # ================================================================
    # SCORE GERAL (media ponderada)
    # ================================================================
    def score_geral(self, scores: dict) -> float:
        total_peso = 0
        total_pond = 0
        for dim, peso in self.PESOS.items():
            val = scores.get(dim)
            if val is not None:
                total_pond += val * peso
                total_peso += peso
        if total_peso == 0:
            return 0
        return round(total_pond / total_peso, 2)
