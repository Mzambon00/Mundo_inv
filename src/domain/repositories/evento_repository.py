# ==============================================================================
# ARQUIVO: src/domain/repositories/evento_repository.py
# O QUE FAZ: Interface abstrata do repositório de eventos (idempotência)
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Repositório Abstrato - Evento"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Evento:
    """Value Object representando um evento de webhook já processado."""

    event_id: str
    card_id: str
    cliente_email: str
    processed_at: datetime = None

    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.utcnow()


class EventoRepository(ABC):
    """
    Interface (porta de saída) do repositório de eventos processados.

    Garante idempotência: se um event_id já foi processado,
    o Use Case não o processa novamente.
    """

    @abstractmethod
    def salvar(self, evento: Evento) -> Evento:
        """
        Persiste um evento processado.

        Args:
            evento: Evento a ser salvo.

        Returns:
            Evento salvo.
        """
        ...

    @abstractmethod
    def ja_processado(self, event_id: str) -> bool:
        """
        Verifica se um evento já foi processado.

        Args:
            event_id: Identificador único do evento.

        Returns:
            True se já processado, False caso contrário.
        """
        ...

    @abstractmethod
    def buscar_por_id(self, event_id: str) -> Optional[Evento]:
        """
        Busca um evento pelo seu identificador.

        Args:
            event_id: Identificador único do evento.

        Returns:
            Evento encontrado ou None.
        """
        ...
