from unittest.mock import patch

import pytest

from src.collectors.brapi_collector import BrapiCollector


@pytest.fixture
def collector():
    return BrapiCollector()


def test_get_cotacao_retorna_dados(collector):
    mock_response = {
        "results": [
            {
                "symbol": "PETR4",
                "regularMarketPrice": 38.50,
                "marketCap": 500_000_000_000,
                "priceEarnings": 5.2,
            }
        ]
    }
    with patch.object(collector, "_get", return_value=mock_response):
        dados = collector.get_cotacao("PETR4")
        assert dados["symbol"] == "PETR4"
        assert dados["regularMarketPrice"] == 38.50
        assert dados["priceEarnings"] == 5.2


def test_get_cotacao_ticker_invalido(collector):
    with patch.object(collector, "_get", return_value={"results": []}):
        with pytest.raises(ValueError, match="nao encontrado"):
            collector.get_cotacao("XXXXXX")


def test_get_historico_retorna_lista(collector):
    mock_response = {
        "results": [
            {
                "historicalDataPrice": [
                    {
                        "date": 1700000000,
                        "open": 38.0,
                        "high": 39.0,
                        "low": 37.5,
                        "close": 38.5,
                    }
                ]
            }
        ]
    }
    with patch.object(collector, "_get", return_value=mock_response):
        historico = collector.get_historico("PETR4", "1mo")
        assert len(historico) == 1
        assert historico[0]["close"] == 38.5


def test_get_historico_vazio(collector):
    with patch.object(collector, "_get", return_value={"results": []}):
        historico = collector.get_historico("PETR4")
        assert historico == []


def test_get_dividendos_retorna_lista(collector):
    mock_response = {
        "results": [
            {
                "dividendsData": {
                    "cashDividends": [
                        {"paymentDate": "2024-01-15", "value": 1.50}
                    ]
                }
            }
        ]
    }
    with patch.object(collector, "_get", return_value=mock_response):
        divs = collector.get_dividendos("PETR4")
        assert len(divs) == 1
        assert divs[0]["value"] == 1.50
