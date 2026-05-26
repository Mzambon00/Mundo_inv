# ==============================================================================
# ARQUIVO: src/domain/value_objects/email.py
# O QUE FAZ: Value Object imutável que valida e encapsula um endereço de e-mail
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Value Object - Email"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """
    Representa um endereço de e-mail válido e imutável.

    Como Value Object, dois emails são iguais se seus valores são iguais.
    É imutável por design (frozen=True) — não pode ser alterado após criação.
    """

    valor: str

    def __post_init__(self):
        valor_limpo = self.valor.strip().lower()
        # Usa object.__setattr__ pois o dataclass é frozen
        object.__setattr__(self, "valor", valor_limpo)
        self._validar(valor_limpo)

    def _validar(self, valor: str) -> None:
        if not valor:
            raise ValueError("E-mail não pode ser vazio.")
        if len(valor) > 254:
            raise ValueError("E-mail excede o limite de 254 caracteres.")
        padrao = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(padrao, valor):
            raise ValueError(f"E-mail inválido: '{valor}'")

    @property
    def dominio(self) -> str:
        """Retorna apenas o domínio do e-mail."""
        return self.valor.split("@")[1]

    @property
    def usuario(self) -> str:
        """Retorna apenas o usuário do e-mail (antes do @)."""
        return self.valor.split("@")[0]

    def __str__(self) -> str:
        return self.valor

    def __repr__(self) -> str:
        return f"Email('{self.valor}')"
