# ==============================================================================
# ARQUIVO: src/domain/value_objects/prioridade.py
# O QUE FAZ: Enum que define as prioridades do cliente com limiar configurável
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Value Object - Prioridade"""

from enum import Enum


class Prioridade(Enum):
    """
    Enum imutável representando a prioridade de atendimento de um cliente.

    Regra de negócio:
        - ALTA: Patrimônio >= R$ 200.000,00
        - NORMAL: Patrimônio < R$ 200.000,00
    """

    ALTA = "prioridade_alta"
    NORMAL = "prioridade_normal"

    # Limiar centralizando a regra de negócio em um único lugar
    LIMIAR_ALTA: float = 200_000.0  # type: ignore[assignment]

    @classmethod
    def calcular(cls, valor_patrimonio: float) -> "Prioridade":
        """
        Calcula a prioridade com base no patrimônio.

        Args:
            valor_patrimonio: Valor do patrimônio em reais.

        Returns:
            Prioridade correspondente.

        Raises:
            ValueError: Se patrimônio for negativo.
        """
        if valor_patrimonio < 0:
            raise ValueError("Patrimônio não pode ser negativo.")
        return cls.ALTA if valor_patrimonio >= cls.LIMIAR_ALTA.value else cls.NORMAL

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Prioridade.{self.name}"

    @property
    def label(self) -> str:
        """Rótulo legível para exibição."""
        labels = {
            "ALTA": "Alta Prioridade",
            "NORMAL": "Prioridade Normal",
        }
        return labels[self.name]
