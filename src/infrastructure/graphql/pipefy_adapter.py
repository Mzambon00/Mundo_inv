# ==============================================================================
# ARQUIVO: src/infrastructure/graphql/pipefy_adapter.py
# O QUE FAZ: Adapter GraphQL para o Pipefy — implementa PipefyService
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Adapter Pipefy - GraphQL"""

import logging
import os
from typing import Any

import httpx

from src.domain.repositories.pipefy_service import PipefyService

logger = logging.getLogger(__name__)

PIPEFY_API_URL = "https://api.pipefy.com/graphql"
PIPEFY_PIPE_ID = os.getenv("PIPEFY_PIPE_ID", "302428309")
PIPEFY_TOKEN = os.getenv("PIPEFY_TOKEN", "")


class PipefyAdapter(PipefyService):
    """
    Implementação concreta de PipefyService via GraphQL.

    Realiza chamadas HTTP reais ao Pipefy. Em testes, esta classe
    é substituída por um mock que implementa a mesma interface.
    """

    CREATE_CARD_MUTATION = """
    mutation CreateCard($pipeId: ID!, $fieldsAttributes: [FieldValueInput]!) {
      createCard(input: {pipe_id: $pipeId, fields_attributes: $fieldsAttributes}) {
        card { id title }
      }
    }
    """

    UPDATE_CARD_FIELD_MUTATION = """
    mutation UpdateCardField($cardId: ID!, $fieldId: String!, $newValue: String!) {
      updateCardField(input: {card_id: $cardId, field_id: $fieldId, new_value: $newValue}) {
        success
      }
    }
    """

    def __init__(self, token: str = PIPEFY_TOKEN, pipe_id: str = PIPEFY_PIPE_ID):
        self._token = token
        self._pipe_id = pipe_id
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _executar_query(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Executa uma query/mutation GraphQL no Pipefy."""
        if not self._token:
            logger.warning("[PIPEFY] Token não configurado — simulando resposta.")
            return {"data": {}}

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    PIPEFY_API_URL,
                    json=payload,
                    headers=self._headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            logger.error("[PIPEFY] Erro HTTP: %s", exc)
            raise RuntimeError(f"Falha na comunicação com Pipefy: {exc}") from exc

    def criar_card(self, nome: str, email: str, patrimonio: float) -> str:
        """
        Cria um card no Pipefy e retorna o ID gerado.
        """
        payload = {
            "query": self.CREATE_CARD_MUTATION,
            "variables": {
                "pipeId": self._pipe_id,
                "fieldsAttributes": [
                    {"field_id": "nome_cliente", "field_value": nome},
                    {"field_id": "email_cliente", "field_value": email},
                    {"field_id": "patrimonio", "field_value": str(patrimonio)},
                    {"field_id": "status_pipefy", "field_value": "Aguardando Análise"},
                ],
            },
        }
        logger.info("[PIPEFY] Criando card para: %s", email)
        resultado = self._executar_query(payload)

        try:
            card_id = resultado["data"]["createCard"]["card"]["id"]
            logger.info("[PIPEFY] Card criado: %s", card_id)
            return str(card_id)
        except (KeyError, TypeError):
            # Fallback para ambiente sem token configurado
            card_id_simulado = f"card_{nome.lower().replace(' ', '_')}"
            logger.warning("[PIPEFY] Usando card_id simulado: %s", card_id_simulado)
            return card_id_simulado

    def atualizar_card(self, card_id: str, status: str, prioridade: str) -> None:
        """
        Atualiza os campos de status e prioridade de um card.
        """
        atualizacoes = [
            ("status_pipefy", status),
            ("prioridade_cliente", prioridade),
        ]
        for field_id, valor in atualizacoes:
            payload = {
                "query": self.UPDATE_CARD_FIELD_MUTATION,
                "variables": {
                    "cardId": card_id,
                    "fieldId": field_id,
                    "newValue": valor,
                },
            }
            logger.info("[PIPEFY] Atualizando card %s: %s = %s", card_id, field_id, valor)
            self._executar_query(payload)
