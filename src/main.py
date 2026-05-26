# ==============================================================================
# ARQUIVO: src/main.py
# O QUE FAZ: Ponto de entrada da aplicação FastAPI com DI correta
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Main - FastAPI Application"""

import logging
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from src.application.use_cases.criar_cliente_use_case import (
    CriarClienteInput,
    CriarClienteUseCase,
)
from src.application.use_cases.processar_webhook_use_case import (
    ProcessarWebhookInput,
    ProcessarWebhookUseCase,
)
from src.infrastructure.database.cliente_repository_impl import (
    SQLAlchemyClienteRepository,
)
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.evento_repository_impl import (
    SQLAlchemyEventoRepository,
)
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Mundo Invest — Client Management API",
    description=(
        "API de gerenciamento de clientes com integração Pipefy. "
        "Construída com Clean Architecture e princípios SOLID."
    ),
    version="2.0.0",
    contact={"name": "Marcos Zambon", "email": "marcos@mundoinvest.com.br"},
)


# ---------------------------------------------------------------------------
# Schemas de Request/Response (Pydantic)
# ---------------------------------------------------------------------------
class CriarClienteRequest(BaseModel):
    cliente_nome: str
    cliente_email: EmailStr
    tipo_solicitacao: str
    valor_patrimonio: float

    @field_validator("cliente_nome")
    @classmethod
    def nome_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nome não pode ser vazio.")
        return v.strip()

    @field_validator("valor_patrimonio")
    @classmethod
    def patrimonio_nao_negativo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Patrimônio não pode ser negativo.")
        return v

    @field_validator("tipo_solicitacao")
    @classmethod
    def tipo_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Tipo de solicitação não pode ser vazio.")
        return v.strip()


class CriarClienteResponse(BaseModel):
    id: int
    nome: str
    email: str
    status: str
    prioridade: str
    card_id: str


class WebhookPayload(BaseModel):
    event_id: str
    card_id: str
    cliente_email: EmailStr
    timestamp: Optional[str] = None

    @field_validator("event_id", "card_id")
    @classmethod
    def nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Campo não pode ser vazio.")
        return v.strip()


class WebhookResponse(BaseModel):
    status: str
    event_id: str
    card_id: str
    prioridade: Optional[str] = None
    cliente_nome: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str


# ---------------------------------------------------------------------------
# Fábrica de dependências (injeção de dependências via FastAPI)
# ---------------------------------------------------------------------------
def _pipefy_service() -> PipefyAdapter:
    """Singleton simples do adapter Pipefy."""
    return PipefyAdapter()


def _cliente_repo(db: Session = Depends(get_db)) -> SQLAlchemyClienteRepository:
    return SQLAlchemyClienteRepository(db)


def _evento_repo(db: Session = Depends(get_db)) -> SQLAlchemyEventoRepository:
    return SQLAlchemyEventoRepository(db)


# ---------------------------------------------------------------------------
# Handlers de exceção globais
# ---------------------------------------------------------------------------
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
def criar_cliente_endpoint(
    request: CriarClienteRequest,
    cliente_repo: SQLAlchemyClienteRepository = Depends(_cliente_repo),
    pipefy: PipefyAdapter = Depends(_pipefy_service),
) -> CriarClienteResponse:
    """
    Cria um novo cliente e registra no Pipefy.

    - Valida e-mail e dados de entrada
    - Calcula prioridade automaticamente
    - Cria card no Pipefy
    """
    use_case = CriarClienteUseCase(
        cliente_repo=cliente_repo,
        pipefy_service=pipefy,
    )
    try:
        resultado = use_case.executar(
            CriarClienteInput(
                nome=request.cliente_nome,
                email=str(request.cliente_email),
                tipo_solicitacao=request.tipo_solicitacao,
                valor_patrimonio=request.valor_patrimonio,
            )
        )
        return CriarClienteResponse(
            id=resultado.id,
            nome=resultado.nome,
            email=resultado.email,
            status=resultado.status,
            prioridade=resultado.prioridade,
            card_id=resultado.card_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Erro inesperado ao criar cliente")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar requisição.",
        )


def webhook_endpoint(
    payload: WebhookPayload,
    cliente_repo: SQLAlchemyClienteRepository = Depends(_cliente_repo),
    evento_repo: SQLAlchemyEventoRepository = Depends(_evento_repo),
    pipefy: PipefyAdapter = Depends(_pipefy_service),
) -> WebhookResponse:
    """
    Processa evento de webhook recebido do Pipefy.

    - Garante idempotência (eventos duplicados são ignorados)
    - Calcula e persiste prioridade no banco
    - Atualiza card no Pipefy
    """
    use_case = ProcessarWebhookUseCase(
        cliente_repo=cliente_repo,
        evento_repo=evento_repo,
        pipefy_service=pipefy,
    )
    try:
        resultado = use_case.executar(
            ProcessarWebhookInput(
                event_id=payload.event_id,
                card_id=payload.card_id,
                cliente_email=str(payload.cliente_email),
            )
        )
        return WebhookResponse(
            status=resultado.status,
            event_id=resultado.event_id,
            card_id=resultado.card_id,
            prioridade=resultado.prioridade,
            cliente_nome=resultado.cliente_nome,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Erro inesperado ao processar webhook")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar webhook.",
        )


def health_endpoint() -> HealthResponse:
    """Verifica se a API está operacional."""
    return HealthResponse(status="ok", version="2.0.0")


# ---------------------------------------------------------------------------
# Registro das rotas
# ---------------------------------------------------------------------------
app.add_api_route(
    "/clientes",
    criar_cliente_endpoint,
    methods=["POST"],
    response_model=CriarClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Cliente",
    tags=["Clientes"],
)

app.add_api_route(
    "/webhooks/pipefy/card-updated",
    webhook_endpoint,
    methods=["POST"],
    response_model=WebhookResponse,
    summary="Processar Webhook Pipefy",
    tags=["Webhooks"],
)

app.add_api_route(
    "/health",
    health_endpoint,
    methods=["GET"],
    response_model=HealthResponse,
    summary="Health Check",
    tags=["Sistema"],
)
