# ==============================================================================
# ARQUIVO: src/domain/repositories/pipefy_service.py
# O QUE FAZ: Interface abstrata para o serviço Pipefy (porta de saída)
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Interface - Serviço Pipefy"""

from abc import ABC, abstractmethod


class PipefyService(ABC):
    """
    Interface de saída para integração com o Pipefy.

    Ao depender desta abstração, os Use Cases permanecem
    desacoplados do GraphQL e de qualquer detalhe do Pipefy.
    Facilita testes (mock) e futuras trocas de provedor.
    """

    @abstractmethod
    def criar_card(self, nome: str, email: str, patrimonio: float) -> str:
        """
        Cria um card no Pipefy.

        Args:
            nome: Nome do cliente.
            email: E-mail do cliente.
            patrimonio: Valor do patrimônio.

        Returns:
            ID do card criado no Pipefy.
        """
        ...

    @abstractmethod
    def atualizar_card(self, card_id: str, status: str, prioridade: str) -> None:
        """
        Atualiza os campos de um card existente no Pipefy.

        Args:
            card_id: Identificador do card no Pipefy.
            status: Novo status do cliente.
            prioridade: Nova prioridade do cliente.
        """
        ...
