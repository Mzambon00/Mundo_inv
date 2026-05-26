# ==============================================================================
# ARQUIVO: src/infrastructure/database/models.py
# O QUE FAZ: Modelos SQLAlchemy — mapeamento objeto-relacional
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Modelos SQLAlchemy"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa compatível com SQLAlchemy 2.0+."""
    pass


class ClienteModel(Base):
    """Tabela de Clientes."""

    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(254), unique=True, nullable=False, index=True)
    tipo_solicitacao = Column(String(100), nullable=False)
    valor_patrimonio = Column(Float, nullable=False)
    status = Column(String(50), default="Aguardando Análise", nullable=False)
    prioridade = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ClienteModel id={self.id} email='{self.email}'>"


class EventoModel(Base):
    """Tabela de controle de idempotência dos webhooks."""

    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    card_id = Column(String(255), nullable=False)
    cliente_email = Column(String(254), nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<EventoModel event_id='{self.event_id}'>"
