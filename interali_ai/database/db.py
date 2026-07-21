"""Conexao com o banco de dados (SQLAlchemy engine/session)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from interali_ai import config
from interali_ai.database.models import Base

_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(config.DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def _aplicar_migracoes_leves() -> None:
    """Adiciona colunas novas em tabelas ja existentes (SQLite nao suporta
    migracoes automaticas via create_all - so cria tabelas ausentes)."""
    inspector = inspect(engine)
    if "empresas" not in inspector.get_table_names():
        return
    colunas_existentes = {c["name"] for c in inspector.get_columns("empresas")}
    for coluna in Base.metadata.tables["empresas"].columns:
        if coluna.name not in colunas_existentes:
            tipo_sql = coluna.type.compile(dialect=engine.dialect)
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE empresas ADD COLUMN {coluna.name} {tipo_sql}"))


def init_db() -> None:
    """Cria as tabelas caso ainda nao existam e aplica migracoes leves."""
    Base.metadata.create_all(bind=engine)
    _aplicar_migracoes_leves()


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
