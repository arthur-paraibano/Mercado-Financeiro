import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.processors.cross_analyzer import CrossAnalyzer


analyzer = CrossAnalyzer()


# ===== CRUZAMENTO 1: Saude Financeira =====

def test_detecta_prejuizo():
    dados = {
        "lucro_liquido_12m": -500_000_000,
        "receita_12m": 5_000_000_000,
        "ebit_12m": -200_000_000,
        "patrimonio_liq": 3_000_000_000,
        "divida_liquida": 2_000_000_000,
        "roe": -15.0,
        "margem_liquida": -10.0,
        "liquidez_corrente": 0.5,
    }
    alertas = analyzer.analisar_saude_financeira("TEST3", dados)
    tipos = [a.tipo for a in alertas]
    assert "PREJUIZO_LIQUIDO" in tipos
    assert "ROE_NEGATIVO" in tipos
    assert "LIQUIDEZ_BAIXA" in tipos


def test_detecta_endividamento_critico():
    dados = {
        "lucro_liquido_12m": 100_000_000,
        "receita_12m": 2_000_000_000,
        "ebit_12m": 200_000_000,
        "patrimonio_liq": 1_000_000_000,
        "divida_liquida": 2_000_000_000,
        "roe": 10.0,
        "margem_liquida": 5.0,
        "liquidez_corrente": 1.2,
    }
    alertas = analyzer.analisar_saude_financeira("DIV3", dados)
    tipos = [a.tipo for a in alertas]
    # EBITDA estimado = 200M * 1.15 = 230M. Div/EBITDA = 2000/230 = 8.7x -> CRITICO
    assert "ENDIVIDAMENTO_CRITICO" in tipos


def test_empresa_saudavel_sem_alertas_graves():
    dados = {
        "lucro_liquido_12m": 5_000_000_000,
        "receita_12m": 30_000_000_000,
        "ebit_12m": 8_000_000_000,
        "patrimonio_liq": 20_000_000_000,
        "divida_liquida": -1_000_000_000,  # caixa liquido
        "roe": 25.0,
        "margem_liquida": 16.0,
        "liquidez_corrente": 1.5,
    }
    alertas = analyzer.analisar_saude_financeira("SAUD3", dados)
    tipos = [a.tipo for a in alertas]
    assert "PREJUIZO_LIQUIDO" not in tipos
    assert "ENDIVIDAMENTO_CRITICO" not in tipos
    assert "ROE_NEGATIVO" not in tipos


# ===== CRUZAMENTO 2: Divergencia Resultados =====

def test_trimestre_prejuizo_com_lucro_anual():
    dados = {
        "lucro_liquido_12m": 1_000_000_000,
        "lucro_liquido_3m": -200_000_000,
        "receita_12m": 10_000_000_000,
        "receita_3m": 2_500_000_000,
    }
    alertas = analyzer.analisar_divergencia_lucro_resultados("TEST3", dados)
    tipos = [a.tipo for a in alertas]
    assert "TRIMESTRE_PREJUIZO" in tipos


def test_lucro_extraordinario():
    dados = {
        "lucro_liquido_12m": 1_000_000_000,
        "lucro_liquido_3m": 800_000_000,  # 3.2x a media trimestral
        "receita_12m": 10_000_000_000,
        "receita_3m": 2_500_000_000,
    }
    alertas = analyzer.analisar_divergencia_lucro_resultados("TEST3", dados)
    tipos = [a.tipo for a in alertas]
    assert "LUCRO_EXTRAORDINARIO" in tipos


# ===== CRUZAMENTO 3: Valuation vs Setor =====

def test_valuation_caro():
    indicadores = {"pl": 30.0, "pvp": 5.0, "ev_ebitda": 20.0, "roe": 15.0}
    mediana = {"pl": 10.0, "pvp": 1.5, "ev_ebitda": 8.0, "roe": 12.0}
    alertas = analyzer.analisar_valuation_vs_setor("CARO3", indicadores, mediana, "Teste")
    tipos = [a.tipo for a in alertas]
    assert "VALUATION_CARO" in tipos


def test_valuation_barato():
    indicadores = {"pl": 4.0, "pvp": 0.5, "ev_ebitda": 3.0, "roe": 20.0}
    mediana = {"pl": 12.0, "pvp": 2.0, "ev_ebitda": 10.0, "roe": 12.0}
    alertas = analyzer.analisar_valuation_vs_setor("BAR3", indicadores, mediana, "Teste")
    tipos = [a.tipo for a in alertas]
    assert "VALUATION_BARATO" in tipos


# ===== CRUZAMENTO 4: Impacto Macro =====

def test_selic_pressiona_varejo():
    macro = {"selic_atual": 14.25, "selic_6m_atras": 13.25, "cambio_atual": 5.7, "cambio_6m_atras": 5.4}
    alertas = analyzer.analisar_impacto_macro("VARJ3", "Varejo", macro)
    tipos = [a.tipo for a in alertas]
    assert "MACRO_SELIC_PRESSAO" in tipos


def test_selic_beneficia_bancos():
    macro = {"selic_atual": 14.25, "selic_6m_atras": 13.25, "cambio_atual": 5.7, "cambio_6m_atras": 5.4}
    alertas = analyzer.analisar_impacto_macro("BANC3", "Financeiro", macro)
    tipos = [a.tipo for a in alertas]
    assert "MACRO_SELIC_BENEFICIO" in tipos


# ===== CRUZAMENTO 5: Dividendos =====

def test_dividendo_insustentavel():
    dados = {
        "dividend_yield": 10.0,
        "cotacao": 20.0,
        "lpa": 1.0,  # DPA = 20*0.10 = 2.0, payout = 200%
        "lucro_liquido_12m": 500_000_000,
        "num_acoes": 500_000_000,
    }
    alertas = analyzer.analisar_dividendos("DIV3", dados, selic_atual=14.25)
    tipos = [a.tipo for a in alertas]
    assert "DIVIDENDO_INSUSTENTAVEL" in tipos


def test_dy_abaixo_selic():
    dados = {
        "dividend_yield": 3.0,
        "cotacao": 50.0,
        "lpa": 5.0,
        "lucro_liquido_12m": 2_000_000_000,
        "num_acoes": 400_000_000,
    }
    alertas = analyzer.analisar_dividendos("LOW3", dados, selic_atual=14.25)
    tipos = [a.tipo for a in alertas]
    assert "DY_ABAIXO_SELIC" in tipos
