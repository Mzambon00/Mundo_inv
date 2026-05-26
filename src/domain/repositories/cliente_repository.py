# ==============================================================================
# ARQUIVO: src/domain/repositories/cliente_repository.py
# O QUE FAZ: Interface abstrata do repositório de clientes (porta de saída)
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Repositório Abstrato - Cliente"""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.cliente import Cliente


class ClienteRepository(ABC):
    """
    Interface (porta de saída) do repositório de clientes.

    Os Use Cases dependem DESTA abstração — nunca das implementações
    concretas (SQLAlchemy, DynamoDB, etc). Isso implementa o princípio
    de Inversão de Dependências do SOLID.
    """

    @abstractmethod
    def salvar(self, cliente: Cliente) -> Cliente:
        """
        Persiste um novo cliente.

        Args:
            cliente: Entidade Cliente a ser salva.

        Returns:
            Cliente salvo com o id preenchido.

        Raises:
            ValueError: Se e-mail já estiver cadastrado.
        """
        ...

    @abstractmethod
    def atualizar(self, cliente: Cliente) -> Cliente:
        """
        Atualiza dados de um cliente existente.

        Args:
            cliente: Entidade Cliente com dados atualizados (deve ter id).

        Returns:
            Cliente atualizado.

        Raises:
            ValueError: Se cliente não for encontrado.
        """
        ...

    @abstractmethod
    def buscar_por_email(self, email: str) -> Optional[Cliente]:
        """
        Busca um cliente pelo e-mail.

        Args:
            email: Endereço de e-mail.

        Returns:
            Cliente encontrado ou None.
        """
        ...

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Cliente]:
        """
        Busca um cliente pelo id.

        Args:
            id: Identificador numérico.

        Returns:
            Cliente encontrado ou None.
        """
        ...

    @abstractmethod
    def email_existe(self, email: str) -> bool:
        """
        Verifica se um e-mail já está cadastrado.

        Args:
            email: Endereço de e-mail.

        Returns:
            True se já cadastrado, False caso contrário.
        """
        ...
