# ==============================================================================
# ARQUIVO: src/infrastructure/database/cliente_repository_impl.py
# O QUE FAZ: Implementação concreta do repositório de clientes com SQLAlchemy
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Repositório SQLAlchemy - Cliente"""

from typing import Optional

from sqlalchemy.orm import Session

from src.domain.entities.cliente import Cliente
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.value_objects.email import Email
from src.domain.value_objects.prioridade import Prioridade
from src.infrastructure.database.models import ClienteModel


class SQLAlchemyClienteRepository(ClienteRepository):
    """
    Implementação concreta do ClienteRepository usando SQLAlchemy.

    Esta classe pertence à camada de infraestrutura — os Use Cases
    nunca a importam diretamente. A injeção de dependências é feita
    via FastAPI (Depends) no ponto de entrada (main.py).
    """

    def __init__(self, db: Session):
        self._db = db

    def salvar(self, cliente: Cliente) -> Cliente:
        if self.email_existe(str(cliente.email)):
            raise ValueError(f"E-mail '{cliente.email}' já está cadastrado.")

        model = ClienteModel(
            nome=cliente.nome,
            email=str(cliente.email),
            tipo_solicitacao=cliente.tipo_solicitacao,
            valor_patrimonio=cliente.valor_patrimonio,
            status=cliente.status,
            prioridade=str(cliente.prioridade) if cliente.prioridade else None,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)

        cliente.id = model.id
        return cliente

    def atualizar(self, cliente: Cliente) -> Cliente:
        model = self._db.query(ClienteModel).filter_by(id=cliente.id).first()
        if not model:
            raise ValueError(f"Cliente com id={cliente.id} não encontrado.")

        model.status = cliente.status
        model.prioridade = str(cliente.prioridade) if cliente.prioridade else None
        self._db.commit()
        self._db.refresh(model)
        return cliente

    def buscar_por_email(self, email: str) -> Optional[Cliente]:
        model = self._db.query(ClienteModel).filter_by(email=email.lower()).first()
        return self._model_para_entidade(model) if model else None

    def buscar_por_id(self, id: int) -> Optional[Cliente]:
        model = self._db.query(ClienteModel).filter_by(id=id).first()
        return self._model_para_entidade(model) if model else None

    def email_existe(self, email: str) -> bool:
        return (
            self._db.query(ClienteModel).filter_by(email=email.lower()).first()
            is not None
        )

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------
    @staticmethod
    def _model_para_entidade(model: ClienteModel) -> Cliente:
        """Converte um ClienteModel para a entidade de domínio Cliente."""
        prioridade = None
        if model.prioridade:
            try:
                prioridade = Prioridade(model.prioridade)
            except ValueError:
                prioridade = None

        return Cliente(
            id=model.id,
            nome=model.nome,
            email=Email(model.email),
            tipo_solicitacao=model.tipo_solicitacao,
            valor_patrimonio=model.valor_patrimonio,
            status=model.status,
            prioridade=prioridade,
            criado_em=model.created_at,
        )
