from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

from config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cria todas as tabelas definidas no schema.sql."""
    schema_path = Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    with engine.connect() as conn:
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()

    logger.info("Banco de dados inicializado com sucesso.")
