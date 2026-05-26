# ==============================================================================
# ARQUIVO: src/infrastructure/database/connection.py
# O QUE FAZ: Gerenciamento da conexão com banco de dados
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Conexão com Banco de Dados"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mundo_invest.db")

# connect_args apenas necessário para SQLite
_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
)

# Cria tabelas automaticamente (apenas para SQLite/dev)
# Em produção, use Alembic para migrações controladas
Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency FastAPI para injeção de sessão do banco.

    Garante que a sessão é sempre fechada após o request,
    mesmo em caso de exceção.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
