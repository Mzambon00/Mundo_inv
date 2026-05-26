# ==============================================================================
# ARQUIVO: tests/test_email_value_object.py
# O QUE FAZ: Testes unitários completos do Value Object Email
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Testes - Email Value Object"""

import pytest

from src.domain.value_objects.email import Email


class TestEmailValido:
    """Testa criação de e-mails válidos."""

    def test_email_simples(self):
        email = Email("marcos@mundoinvest.com.br")
        assert str(email) == "marcos@mundoinvest.com.br"

    def test_email_com_pontos(self):
        email = Email("marcos.zambon@mundoinvest.com.br")
        assert email.valor == "marcos.zambon@mundoinvest.com.br"

    def test_email_com_subdominio(self):
        email = Email("user@mail.empresa.com")
        assert str(email) == "user@mail.empresa.com"

    def test_email_com_numeros(self):
        email = Email("user123@test123.org")
        assert str(email) == "user123@test123.org"

    def test_email_com_mais(self):
        email = Email("user+tag@example.com")
        assert str(email) == "user+tag@example.com"

    def test_email_normalizado_para_minusculas(self):
        """E-mails devem ser normalizados para lowercase."""
        email = Email("MARCOS@MUNDOINVEST.COM.BR")
        assert email.valor == "marcos@mundoinvest.com.br"

    def test_email_remove_espacos(self):
        """E-mails com espaços nas bordas devem ser limpos."""
        email = Email("  marcos@mundoinvest.com.br  ")
        assert email.valor == "marcos@mundoinvest.com.br"

    def test_email_imutavel(self):
        """Value Object deve ser imutável (frozen dataclass)."""
        email = Email("marcos@test.com")
        with pytest.raises((AttributeError, TypeError)):
            email.valor = "outro@test.com"  # type: ignore


class TestEmailInvalido:
    """Testa rejeição de e-mails inválidos."""

    @pytest.mark.parametrize("email_invalido", [
        "",
        " ",
        "nao-e-email",
        "@semdominio.com",
        "semat.com",
        "a@b",
        "a@.com",
        "a@ .com",
    ])
    def test_email_invalido_lanca_excecao(self, email_invalido: str):
        with pytest.raises(ValueError):
            Email(email_invalido)

    def test_email_vazio_mensagem_clara(self):
        with pytest.raises(ValueError, match="vazio"):
            Email("")

    def test_email_sem_arroba(self):
        with pytest.raises(ValueError, match="inválido"):
            Email("marcosmundoinvest.com")

    def test_email_muito_longo(self):
        email_longo = "a" * 250 + "@test.com"
        with pytest.raises(ValueError):
            Email(email_longo)


class TestEmailPropriedades:
    """Testa propriedades derivadas do e-mail."""

    def test_dominio(self):
        email = Email("marcos@mundoinvest.com.br")
        assert email.dominio == "mundoinvest.com.br"

    def test_usuario(self):
        email = Email("marcos@mundoinvest.com.br")
        assert email.usuario == "marcos"

    def test_igualdade_por_valor(self):
        """Dois Value Objects com mesmo valor devem ser iguais."""
        email1 = Email("marcos@test.com")
        email2 = Email("marcos@test.com")
        assert email1 == email2

    def test_desigualdade_por_valor(self):
        email1 = Email("marcos@test.com")
        email2 = Email("outro@test.com")
        assert email1 != email2

    def test_hashavel(self):
        """Value Object deve ser hashável (para uso em sets/dicts)."""
        email = Email("marcos@test.com")
        s = {email}
        assert email in s

    def test_repr(self):
        email = Email("marcos@test.com")
        assert "marcos@test.com" in repr(email)
