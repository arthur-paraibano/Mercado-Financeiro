from loguru import logger


class IndicatorCalculator:
    """Calcula indicadores fundamentalistas a partir de dados brutos."""

    @staticmethod
    def calcular_indicadores(cotacao: dict, dre: dict, balanco: dict) -> dict:
        """
        Recebe dados brutos e retorna dict com todos os indicadores.

        cotacao: dict com regularMarketPrice, marketCap, etc (brapi).
        dre:     dict com receita_liquida, lucro_liquido, ebitda, etc (CVM).
        balanco: dict com patrimonio_liquido, ativo_total, divida_bruta, etc (CVM).
        """
        indicadores = {}

        preco = cotacao.get("regularMarketPrice") or 0
        market_cap = cotacao.get("marketCap") or 0
        acoes = market_cap / preco if preco else 0

        lucro_liquido = dre.get("lucro_liquido") or 0
        receita = dre.get("receita_liquida") or 0
        ebitda = dre.get("ebitda") or 0
        ebit = dre.get("ebit") or 0
        lucro_bruto = dre.get("lucro_bruto") or 0

        pl = balanco.get("patrimonio_liquido") or 0
        ativo = balanco.get("ativo_total") or 0
        divida = balanco.get("divida_bruta") or 0
        caixa = balanco.get("caixa_equivalentes") or 0
        divida_liq = divida - caixa

        # --- Valuation ---
        lpa = lucro_liquido / acoes if acoes else None
        indicadores["pl"] = round(preco / lpa, 2) if lpa and lpa > 0 else None

        vpa = pl / acoes if acoes else None
        indicadores["pvp"] = round(preco / vpa, 2) if vpa and vpa > 0 else None

        ev = market_cap + divida_liq
        indicadores["ev_ebitda"] = (
            round(ev / ebitda, 2) if ebitda and ebitda > 0 else None
        )
        indicadores["psr"] = (
            round(market_cap / receita, 2) if receita and receita > 0 else None
        )
        indicadores["market_cap"] = market_cap
        indicadores["enterprise_value"] = ev

        # --- Rentabilidade ---
        indicadores["roe"] = (
            round(lucro_liquido / pl * 100, 2) if pl and pl != 0 else None
        )
        indicadores["roa"] = (
            round(lucro_liquido / ativo * 100, 2) if ativo and ativo != 0 else None
        )
        indicadores["margem_liquida"] = (
            round(lucro_liquido / receita * 100, 2) if receita and receita != 0 else None
        )
        indicadores["margem_ebitda"] = (
            round(ebitda / receita * 100, 2) if receita and ebitda else None
        )
        indicadores["margem_bruta"] = (
            round(lucro_bruto / receita * 100, 2) if receita and lucro_bruto else None
        )

        # --- Endividamento ---
        indicadores["divida_liq_ebitda"] = (
            round(divida_liq / ebitda, 2) if ebitda and ebitda > 0 else None
        )

        logger.debug(f"Indicadores calculados: {list(indicadores.keys())}")
        return indicadores
