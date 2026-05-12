import pytest

from src.processors.indicator_calculator import IndicatorCalculator


def _fazer_dados(lucro=2e9, receita=10e9, ebitda=3e9, ebit=2.5e9, lucro_bruto=5e9,
                 pl=10e9, ativo=30e9, divida=5e9, caixa=2e9,
                 preco=20.0, market_cap=20e9):
    cotacao = {"regularMarketPrice": preco, "marketCap": market_cap}
    dre = {
        "lucro_liquido": lucro,
        "receita_liquida": receita,
        "ebitda": ebitda,
        "ebit": ebit,
        "lucro_bruto": lucro_bruto,
    }
    balanco = {
        "patrimonio_liquido": pl,
        "ativo_total": ativo,
        "divida_bruta": divida,
        "caixa_equivalentes": caixa,
    }
    return cotacao, dre, balanco


def test_calcula_pl():
    cotacao, dre, balanco = _fazer_dados()
    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)
    # P/L = preco / (lucro / acoes) = 20 / (2e9 / 1e9) = 10
    assert ind["pl"] == pytest.approx(10.0, rel=0.01)


def test_calcula_pvp():
    cotacao, dre, balanco = _fazer_dados()
    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)
    # PVP = preco / (PL / acoes) = 20 / (10e9 / 1e9) = 2.0
    assert ind["pvp"] == pytest.approx(2.0, rel=0.01)


def test_calcula_roe():
    cotacao, dre, balanco = _fazer_dados()
    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)
    # ROE = lucro / PL * 100 = 2e9 / 10e9 * 100 = 20%
    assert ind["roe"] == pytest.approx(20.0, rel=0.01)


def test_calcula_margem_liquida():
    cotacao, dre, balanco = _fazer_dados()
    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)
    # Margem = lucro / receita * 100 = 2e9 / 10e9 * 100 = 20%
    assert ind["margem_liquida"] == pytest.approx(20.0, rel=0.01)


def test_calcula_divida_ebitda():
    cotacao, dre, balanco = _fazer_dados()
    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)
    # Div Liq / EBITDA = (5e9 - 2e9) / 3e9 = 1.0
    assert ind["divida_liq_ebitda"] == pytest.approx(1.0, rel=0.01)


def test_pl_nulo_quando_lucro_negativo():
    cotacao, dre, balanco = _fazer_dados(lucro=-500_000_000)
    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)
    assert ind["pl"] is None


def test_indicadores_com_valores_zero():
    cotacao = {"regularMarketPrice": 0, "marketCap": 0}
    dre = {"lucro_liquido": 0, "receita_liquida": 0, "ebitda": 0, "ebit": 0, "lucro_bruto": 0}
    balanco = {"patrimonio_liquido": 0, "ativo_total": 0, "divida_bruta": 0, "caixa_equivalentes": 0}

    ind = IndicatorCalculator.calcular_indicadores(cotacao, dre, balanco)
    assert ind["pl"] is None
    assert ind["pvp"] is None
    assert ind["roe"] is None
