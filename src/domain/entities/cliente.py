# ==============================================================================
# ARQUIVO: src/domain/entities/cliente.py
# O QUE FAZ: Entidade principal do domínio com regras de negócio centralizadas
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Entidade - Cliente"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.domain.value_objects.email import Email
from src.domain.value_objects.prioridade import Prioridade


@dataclass
class Cliente:
    """
    Entidade principal do domínio Mundo Invest.

    Contém todas as regras de negócio relativas ao cliente.
    A prioridade é SEMPRE calculada pela entidade — nunca externamente —
    garantindo consistência em todo o sistema.
    """

    nome: str
    email: Email
    tipo_solicitacao: str
    valor_patrimonio: float
    id: Optional[int] = None
    status: str = "Aguardando Análise"
    prioridade: Optional[Prioridade] = None
    criado_em: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self._validar()

    def _validar(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do cliente não pode ser vazio.")
        if not self.tipo_solicitacao or not self.tipo_solicitacao.strip():
            raise ValueError("Tipo de solicitação não pode ser vazio.")
        if self.valor_patrimonio < 0:
            raise ValueError("Valor do patrimônio não pode ser negativo.")

    # ------------------------------------------------------------------
    # Regra de negócio: cálculo de prioridade — ÚNICA FONTE DE VERDADE
    # ------------------------------------------------------------------
    def calcular_prioridade(self) -> Prioridade:
        """
        Calcula a prioridade com base no patrimônio declarado.

        Regra: patrimônio >= R$ 200.000 → ALTA; caso contrário → NORMAL.
        Delega para Prioridade.calcular para evitar duplicação da regra.
        """
        return Prioridade.calcular(self.valor_patrimonio)

    def processar(self) -> None:
        """
        Processa o cliente: calcula prioridade e atualiza status.

        Deve ser chamado apenas UMA vez por fluxo de webhook.
        """
        if self.status == "Processado":
            raise ValueError("Cliente já foi processado anteriormente.")
        self.prioridade = self.calcular_prioridade()
        self.status = "Processado"

    def e_prioritario(self) -> bool:
        """Atalho para verificar se o cliente tem prioridade alta."""
        return self.calcular_prioridade() == Prioridade.ALTA

    def __str__(self) -> str:
        return f"Cliente(id={self.id}, nome='{self.nome}', email='{self.email}')"
