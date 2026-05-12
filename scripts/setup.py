"""Executa setup inicial: cria tabelas no banco e testa conexao com APIs."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
from src.database.connection import init_db
from src.collectors.brapi_collector import BrapiCollector


def main():
    logger.info("=== Setup do Projeto ===")

    # 1. Criar tabelas
    logger.info("Criando tabelas no banco de dados...")
    try:
        init_db()
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        logger.info("Verifique se o PostgreSQL esta rodando e o banco 'mercado_financeiro' existe.")
        return

    # 2. Testar conexao com brapi
    logger.info("Testando conexao com brapi.dev...")
    collector = BrapiCollector()
    tickers_teste = ["WEGE3", "PETR4", "VALE3", "ITUB4", "BBAS3"]

    for ticker in tickers_teste:
        try:
            dados = collector.get_cotacao(ticker)
            preco = dados.get("regularMarketPrice", "N/A")
            nome = dados.get("longName", "N/A")
            logger.info(f"  {ticker}: R$ {preco} - {nome}")
        except Exception as e:
            logger.error(f"  {ticker}: ERRO - {e}")

    logger.info("=== Setup concluido! ===")
    logger.info("Execute o dashboard com: streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
