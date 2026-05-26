# ==============================================================================
# ARQUIVO: tests/test_cliente_entity.py
# O QUE FAZ: Testes unitários da entidade Cliente e Value Object Prioridade
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Testes - Entidade Cliente e Prioridade"""

import pytest

from src.domain.entities.cliente import Cliente
from src.domain.value_objects.email import Email
from src.domain.value_objects.prioridade import Prioridade


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def email_valido() -> Email:
    return Email("marcos@mundoinvest.com.br")


@pytest.fixture
def cliente_normal(email_valido) -> Cliente:
    return Cliente(
        nome="Marcos Normal",
        email=email_valido,
        tipo_solicitacao="Renda Fixa",
        valor_patrimonio=50_000.0,
    )


@pytest.fixture
def cliente_alta(email_valido) -> Cliente:
    return Cliente(
        nome="Marcos VIP",
        email=email_valido,
        tipo_solicitacao="Renda Variável",
        valor_patrimonio=500_000.0,
    )


# ---------------------------------------------------------------------------
# Testes de Prioridade
# ---------------------------------------------------------------------------
class TestPrioridade:
    def test_patrimonio_abaixo_limiar_e_normal(self):
        assert Prioridade.calcular(199_999.99) == Prioridade.NORMAL

    def test_patrimonio_igual_limiar_e_alta(self):
        assert Prioridade.calcular(200_000.0) == Prioridade.ALTA

    def test_patrimonio_acima_limiar_e_alta(self):
        assert Prioridade.calcular(1_000_000.0) == Prioridade.ALTA

    def test_patrimonio_zero_e_normal(self):
        assert Prioridade.calcular(0) == Prioridade.NORMAL

    def test_patrimonio_negativo_lanca_excecao(self):
        with pytest.raises(ValueError):
            Prioridade.calcular(-1.0)

    def test_str_prioridade_alta(self):
        assert str(Prioridade.ALTA) == "prioridade_alta"

    def test_str_prioridade_normal(self):
        assert str(Prioridade.NORMAL) == "prioridade_normal"

    def test_label_prioridade_alta(self):
        assert "Alta" in Prioridade.ALTA.label

    def test_label_prioridade_normal(self):
        assert "Normal" in Prioridade.NORMAL.label


# ---------------------------------------------------------------------------
# Testes de Cliente — criação
# ---------------------------------------------------------------------------
class TestClienteCriacao:
    def test_cliente_criado_com_status_padrao(self, cliente_normal):
        assert cliente_normal.status == "Aguardando Análise"

    def test_cliente_criado_sem_prioridade_definida_pode_calcular(self, cliente_normal):
        """Prioridade pode ser None na criação, mas calcular_prioridade() sempre funciona."""
        prioridade = cliente_normal.calcular_prioridade()
        assert prioridade == Prioridade.NORMAL

    def test_cliente_nome_vazio_lanca_excecao(self, email_valido):
        with pytest.raises(ValueError, match="Nome"):
            Cliente(nome="", email=email_valido, tipo_solicitacao="RF", valor_patrimonio=0)

    def test_cliente_tipo_vazio_lanca_excecao(self, email_valido):
        with pytest.raises(ValueError, match="solicitação"):
            Cliente(nome="Marcos", email=email_valido, tipo_solicitacao="", valor_patrimonio=0)

    def test_cliente_patrimonio_negativo_lanca_excecao(self, email_valido):
        with pytest.raises(ValueError, match="negativo"):
            Cliente(nome="Marcos", email=email_valido, tipo_solicitacao="RF", valor_patrimonio=-1)


# ---------------------------------------------------------------------------
# Testes de Cliente — regras de negócio
# ---------------------------------------------------------------------------
class TestClienteRegrasNegocio:
    def test_calcular_prioridade_normal(self, cliente_normal):
        assert cliente_normal.calcular_prioridade() == Prioridade.NORMAL

    def test_calcular_prioridade_alta(self, cliente_alta):
        assert cliente_alta.calcular_prioridade() == Prioridade.ALTA

    def test_e_prioritario_false(self, cliente_normal):
        assert cliente_normal.e_prioritario() is False

    def test_e_prioritario_true(self, cliente_alta):
        assert cliente_alta.e_prioritario() is True

    def test_processar_atualiza_status(self, cliente_normal):
        cliente_normal.processar()
        assert cliente_normal.status == "Processado"

    def test_processar_define_prioridade(self, cliente_normal):
        cliente_normal.processar()
        assert cliente_normal.prioridade == Prioridade.NORMAL

    def test_processar_define_prioridade_alta(self, cliente_alta):
        cliente_alta.processar()
        assert cliente_alta.prioridade == Prioridade.ALTA

    def test_processar_duas_vezes_lanca_excecao(self, cliente_normal):
        """Processar o mesmo cliente duas vezes deve lançar erro."""
        cliente_normal.processar()
        with pytest.raises(ValueError, match="já foi processado"):
            cliente_normal.processar()

    def test_prioridade_consistente_com_patrimonio_no_limiar(self, email_valido):
        """Patrimônio exatamente no limiar deve ser ALTA."""
        cliente = Cliente(
            nome="Limiar",
            email=email_valido,
            tipo_solicitacao="RF",
            valor_patrimonio=200_000.0,
        )
        assert cliente.calcular_prioridade() == Prioridade.ALTA
        cliente.processar()
        assert cliente.prioridade == Prioridade.ALTA
