# ==============================================================================
# ARQUIVO: src/application/use_cases/processar_webhook_use_case.py
# O QUE FAZ: Use Case responsável por processar o webhook do Pipefy
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Use Case - Processar Webhook"""

from dataclasses import dataclass

from src.domain.entities.cliente import Cliente
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.repositories.evento_repository import Evento, EventoRepository
from src.domain.repositories.pipefy_service import PipefyService
from src.domain.value_objects.email import Email


@dataclass
class ProcessarWebhookInput:
    """DTO de entrada do webhook."""

    event_id: str
    card_id: str
    cliente_email: str


@dataclass
class ProcessarWebhookOutput:
    """DTO de saída após processamento do webhook."""

    status: str
    event_id: str
    card_id: str
    prioridade: str | None = None
    cliente_nome: str | None = None


class ProcessarWebhookUseCase:
    """
    Caso de uso: processar evento de webhook do Pipefy.

    Responsabilidades:
    1. Garantir idempotência (não reprocessar eventos duplicados)
    2. Buscar cliente pelo e-mail
    3. Executar lógica de negócio (processar cliente)
    4. Atualizar status e prioridade no banco (FIX: antes não atualizava)
    5. Atualizar card no Pipefy via adapter (FIX: adapter agora efetivamente usado)
    6. Registrar evento como processado
    """

    def __init__(
        self,
        cliente_repo: ClienteRepository,
        evento_repo: EventoRepository,
        pipefy_service: PipefyService,
    ):
        self._cliente_repo = cliente_repo
        self._evento_repo = evento_repo
        self._pipefy = pipefy_service

    def executar(self, dados: ProcessarWebhookInput) -> ProcessarWebhookOutput:
        """
        Executa o caso de uso de processamento de webhook.

        Args:
            dados: Dados do evento recebido.

        Returns:
            ProcessarWebhookOutput com resultado do processamento.

        Raises:
            ValueError: Se o cliente não for encontrado.
        """
        # 1. Idempotência: ignora eventos já processados
        if self._evento_repo.ja_processado(dados.event_id):
            return ProcessarWebhookOutput(
                status="already_processed",
                event_id=dados.event_id,
                card_id=dados.card_id,
            )

        # 2. Valida e-mail
        email_obj = Email(dados.cliente_email)

        # 3. Busca cliente — lança ValueError se não encontrado
        cliente = self._cliente_repo.buscar_por_email(str(email_obj))
        if not cliente:
            raise ValueError(
                f"Cliente com e-mail '{email_obj}' não encontrado."
            )

        # 4. Executa lógica de negócio na entidade
        cliente.processar()

        # 5. Persiste atualização no banco (FIX: bug resolvido)
        self._cliente_repo.atualizar(cliente)

        # 6. Atualiza card no Pipefy (FIX: adapter efetivamente invocado)
        self._pipefy.atualizar_card(
            card_id=dados.card_id,
            status=cliente.status,
            prioridade=str(cliente.prioridade),
        )

        # 7. Registra evento para garantir idempotência futura
        evento = Evento(
            event_id=dados.event_id,
            card_id=dados.card_id,
            cliente_email=str(email_obj),
        )
        self._evento_repo.salvar(evento)

        return ProcessarWebhookOutput(
            status="processed",
            event_id=dados.event_id,
            card_id=dados.card_id,
            prioridade=str(cliente.prioridade),
            cliente_nome=cliente.nome,
        )
