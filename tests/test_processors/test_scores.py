import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.processors.score_calculator import ScoreCalculator
from src.processors.technical_calculator import TechnicalCalculator


calc = ScoreCalculator()


# ===== Score Saude =====

def test_saude_empresa_excelente():
    ind = {"roe": 25, "margem_liquida": 22, "divida_liquida": -1e9, "ebit_12m": 5e9, "margem_ebit": 30, "roic": 22}
    score, _ = calc.score_saude(ind)
    assert score >= 80


def test_saude_empresa_ruim():
    ind = {"roe": -5, "margem_liquida": -10, "divida_liquida": 10e9, "ebit_12m": 1e9, "margem_ebit": -2, "roic": -3}
    score, _ = calc.score_saude(ind)
    assert score <= 15


# ===== Score Valuation =====

def test_valuation_barata():
    ind = {"pl": 6, "pvp": 0.8, "ev_ebitda": 5, "psr": 0.4}
    score, _ = calc.score_valuation(ind)
    assert score >= 80


def test_valuation_cara():
    ind = {"pl": 50, "pvp": 6, "ev_ebitda": 25, "psr": 8}
    score, _ = calc.score_valuation(ind)
    assert score <= 15


# ===== Score Dividendos =====

def test_dividendos_bom():
    ind = {"dividend_yield": 8, "lpa": 5, "cotacao": 40, "cres_rec_5a": 12}
    score, _ = calc.score_dividendos(ind, selic=14.25)
    assert score >= 40


def test_dividendos_sem_pagamento():
    ind = {"dividend_yield": 0, "lpa": 2, "cotacao": 20, "cres_rec_5a": 5}
    score, _ = calc.score_dividendos(ind, selic=14.25)
    assert score <= 30


# ===== Score Crescimento =====

def test_crescimento_alto():
    ind = {"cres_rec_5a": 25, "margem_ebit": 30, "roe": 28}
    score, _ = calc.score_crescimento(ind)
    assert score >= 80


def test_crescimento_negativo():
    ind = {"cres_rec_5a": -5, "margem_ebit": 3, "roe": 2}
    score, _ = calc.score_crescimento(ind)
    assert score <= 20


# ===== Score Tecnico =====

def test_tecnico_compra():
    sinais = {
        "RSI": {"sinal": "COMPRA", "valor": 25, "desc": "Sobrevenda"},
        "MACD": {"sinal": "COMPRA", "valor": 0.5, "desc": "Cruzou acima"},
        "MEDIAS": {"sinal": "COMPRA", "valor": 50, "desc": "Acima SMA200"},
        "BOLLINGER": {"sinal": "COMPRA", "valor": 48, "desc": "Banda inferior"},
    }
    score, _ = calc.score_tecnico(sinais)
    assert score > 70


def test_tecnico_venda():
    sinais = {
        "RSI": {"sinal": "VENDA", "valor": 80, "desc": "Sobrecompra"},
        "MACD": {"sinal": "VENDA", "valor": -0.5, "desc": "Cruzou abaixo"},
        "MEDIAS": {"sinal": "VENDA", "valor": 50, "desc": "Abaixo SMA200"},
    }
    score, _ = calc.score_tecnico(sinais)
    assert score < 30


# ===== Score Geral =====

def test_score_geral():
    scores = {"saude": 80, "valuation": 70, "dividendos": 60, "crescimento": 50, "tecnico": 55}
    geral = calc.score_geral(scores)
    assert 60 < geral < 75


# ===== Technical Calculator =====

def test_technical_calcula_rsi():
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    close = 50 + np.cumsum(np.random.randn(100) * 0.5)
    df = pd.DataFrame({
        "date": dates, "open": close - 0.2, "high": close + 0.5,
        "low": close - 0.5, "close": close, "volume": np.random.randint(1e6, 5e6, 100),
    })
    result = TechnicalCalculator.calcular_todos(df)
    assert "rsi_14" in result.columns
    assert "macd" in result.columns
    assert "sma_20" in result.columns
    assert "bollinger_upper" in result.columns
    # RSI deve estar entre 0 e 100
    rsi_valid = result["rsi_14"].dropna()
    assert (rsi_valid >= 0).all() and (rsi_valid <= 100).all()


def test_technical_gera_sinais():
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    close = 50 + np.cumsum(np.random.randn(60) * 0.5)
    df = pd.DataFrame({
        "date": dates, "open": close - 0.2, "high": close + 0.5,
        "low": close - 0.5, "close": close, "volume": np.random.randint(1e6, 5e6, 60),
    })
    result = TechnicalCalculator.calcular_todos(df)
    sinais = TechnicalCalculator.gerar_sinais(result)
    assert isinstance(sinais, dict)
    # Deve ter pelo menos RSI e MACD
    assert "RSI" in sinais
    assert sinais["RSI"]["sinal"] in ["COMPRA", "VENDA", "NEUTRO"]
