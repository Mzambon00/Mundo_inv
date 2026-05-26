# ==============================================================================
# ARQUIVO: src/application/use_cases/criar_cliente_use_case.py
# O QUE FAZ: Use Case responsável pela criação de um novo cliente
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Use Case - Criar Cliente"""

from dataclasses import dataclass

from src.domain.entities.cliente import Cliente
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.repositories.pipefy_service import PipefyService
from src.domain.value_objects.email import Email


@dataclass
class CriarClienteInput:
    """DTO de entrada para criação de cliente."""

    nome: str
    email: str
    tipo_solicitacao: str
    valor_patrimonio: float


@dataclass
class CriarClienteOutput:
    """DTO de saída após criação de cliente."""

    id: int
    nome: str
    email: str
    status: str
    prioridade: str
    card_id: str


class CriarClienteUseCase:
    """
    Caso de uso: criar um novo cliente.

    Responsabilidades:
    1. Validar e-mail via Value Object
    2. Verificar duplicidade de e-mail
    3. Calcular prioridade já na criação (consistência)
    4. Persistir no banco via repositório (abstração)
    5. Criar card no Pipefy com dados corretos
    """

    def __init__(
        self,
        cliente_repo: ClienteRepository,
        pipefy_service: PipefyService,
    ):
        self._cliente_repo = cliente_repo
        self._pipefy = pipefy_service

    def executar(self, dados: CriarClienteInput) -> CriarClienteOutput:
        """
        Executa o caso de uso.

        Args:
            dados: Dados de entrada para criação do cliente.

        Returns:
            CriarClienteOutput com os dados do cliente criado.

        Raises:
            ValueError: Se e-mail for inválido ou já estiver cadastrado.
        """
        # 1. Valida e-mail (lança ValueError se inválido)
        email_obj = Email(dados.email)

        # 2. Verifica duplicidade
        if self._cliente_repo.email_existe(str(email_obj)):
            raise ValueError(f"E-mail '{email_obj}' já está cadastrado.")

        # 3. Cria entidade — prioridade calculada na criação (FIX: consistência)
        cliente = Cliente(
            nome=dados.nome,
            email=email_obj,
            tipo_solicitacao=dados.tipo_solicitacao,
            valor_patrimonio=dados.valor_patrimonio,
        )
        # Calcula prioridade desde a criação para que o card no Pipefy
        # já seja criado com o valor correto
        cliente.prioridade = cliente.calcular_prioridade()

        # 4. Persiste no banco
        cliente_salvo = self._cliente_repo.salvar(cliente)

        # 5. Cria card no Pipefy (FIX: adapter sendo efetivamente utilizado)
        card_id = self._pipefy.criar_card(
            nome=cliente_salvo.nome,
            email=str(cliente_salvo.email),
            patrimonio=cliente_salvo.valor_patrimonio,
        )

        return CriarClienteOutput(
            id=cliente_salvo.id,
            nome=cliente_salvo.nome,
            email=str(cliente_salvo.email),
            status=cliente_salvo.status,
            prioridade=str(cliente_salvo.prioridade),
            card_id=card_id,
        )
