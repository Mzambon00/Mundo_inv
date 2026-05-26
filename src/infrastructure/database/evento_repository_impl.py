# ==============================================================================
# ARQUIVO: src/infrastructure/database/evento_repository_impl.py
# O QUE FAZ: Implementação concreta do repositório de eventos com SQLAlchemy
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Repositório SQLAlchemy - Evento"""

from typing import Optional

from sqlalchemy.orm import Session

from src.domain.repositories.evento_repository import Evento, EventoRepository
from src.infrastructure.database.models import EventoModel


class SQLAlchemyEventoRepository(EventoRepository):
    """
    Implementação concreta do EventoRepository usando SQLAlchemy.

    Responsável por garantir a idempotência dos webhooks:
    cada event_id é persistido e verificado antes do processamento.
    """

    def __init__(self, db: Session):
        self._db = db

    def salvar(self, evento: Evento) -> Evento:
        model = EventoModel(
            event_id=evento.event_id,
            card_id=evento.card_id,
            cliente_email=evento.cliente_email,
            processed_at=evento.processed_at,
        )
        self._db.add(model)
        self._db.commit()
        return evento

    def ja_processado(self, event_id: str) -> bool:
        return (
            self._db.query(EventoModel).filter_by(event_id=event_id).first()
            is not None
        )

    def buscar_por_id(self, event_id: str) -> Optional[Evento]:
        model = self._db.query(EventoModel).filter_by(event_id=event_id).first()
        if not model:
            return None
        return Evento(
            event_id=model.event_id,
            card_id=model.card_id,
            cliente_email=model.cliente_email,
            processed_at=model.processed_at,
        )
