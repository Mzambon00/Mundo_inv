# ==============================================================================
# ARQUIVO: tests/test_main.py
# O QUE FAZ: Testes de integração da API FastAPI
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Testes - API FastAPI (integração)"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Banco de dados em arquivo temporário (evita o problema do SQLite in-memory
# onde cada conexão é um banco diferente)
TEST_DB_PATH = "./test_temp_mundo_invest.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

from src.infrastructure.database.models import Base
from src.infrastructure.database.connection import get_db
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter
from src.domain.repositories.pipefy_service import PipefyService
from src.main import app, _pipefy_service

# ---------------------------------------------------------------------------
# Setup do banco de testes
# ---------------------------------------------------------------------------
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    """Override do banco para testes — usa SQLite em arquivo temporário."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class MockPipefyAdapter(PipefyService):
    """
    Mock do PipefyAdapter que não faz chamadas HTTP reais.
    Registra chamadas para asserção nos testes.
    """

    def __init__(self):
        self.cards_criados: list[dict] = []
        self.cards_atualizados: list[dict] = []

    def criar_card(self, nome: str, email: str, patrimonio: float) -> str:
        card_id = f"card_mock_{email.split('@')[0]}"
        self.cards_criados.append({"nome": nome, "email": email, "patrimonio": patrimonio})
        return card_id

    def atualizar_card(self, card_id: str, status: str, prioridade: str) -> None:
        self.cards_atualizados.append({"card_id": card_id, "status": status, "prioridade": prioridade})


mock_pipefy = MockPipefyAdapter()


def override_pipefy():
    return mock_pipefy


# Aplica overrides de dependências
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[_pipefy_service] = override_pipefy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def limpar_banco():
    """Limpa todas as tabelas antes de cada teste."""
    with test_engine.connect() as conn:
        conn.execute(text("DELETE FROM eventos"))
        conn.execute(text("DELETE FROM clientes"))
        conn.commit()
    mock_pipefy.cards_criados.clear()
    mock_pipefy.cards_atualizados.clear()
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_db_file():
    """Remove o arquivo de banco de dados de teste ao finalizar a sessão."""
    yield
    # Fecha todas as conexões antes de deletar (necessário no Windows)
    test_engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass  # Windows pode manter o arquivo bloqueado; ignorar é seguro


@pytest.fixture
def client():
    """TestClient com overrides aplicados."""
    with TestClient(app) as c:
        yield c


PAYLOAD_CLIENTE_NORMAL = {
    "cliente_nome": "João Silva",
    "cliente_email": "joao@test.com",
    "tipo_solicitacao": "Renda Fixa",
    "valor_patrimonio": 50_000.0,
}

PAYLOAD_CLIENTE_VIP = {
    "cliente_nome": "Maria VIP",
    "cliente_email": "maria@test.com",
    "tipo_solicitacao": "Renda Variável",
    "valor_patrimonio": 500_000.0,
}


# ---------------------------------------------------------------------------
# Testes — Health Check
# ---------------------------------------------------------------------------
class TestHealthCheck:
    def test_health_retorna_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_retorna_versao(self, client):
        resp = client.get("/health")
        assert "version" in resp.json()


# ---------------------------------------------------------------------------
# Testes — Criar Cliente (fluxo feliz)
# ---------------------------------------------------------------------------
class TestCriarClienteFluxoFeliz:
    def test_cria_cliente_normal_retorna_201(self, client):
        resp = client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        assert resp.status_code == 201

    def test_cria_cliente_retorna_id(self, client):
        resp = client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        assert resp.json()["id"] is not None

    def test_cria_cliente_retorna_nome(self, client):
        resp = client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        assert resp.json()["nome"] == "João Silva"

    def test_cria_cliente_status_aguardando(self, client):
        resp = client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        assert resp.json()["status"] == "Aguardando Análise"

    def test_cria_cliente_normal_prioridade_normal(self, client):
        resp = client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        assert resp.json()["prioridade"] == "prioridade_normal"

    def test_cria_cliente_vip_prioridade_alta(self, client):
        resp = client.post("/clientes", json=PAYLOAD_CLIENTE_VIP)
        assert resp.json()["prioridade"] == "prioridade_alta"

    def test_cria_cliente_retorna_card_id(self, client):
        resp = client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        assert "card_id" in resp.json()
        assert resp.json()["card_id"] != ""

    def test_cria_cliente_no_limiar_prioridade_alta(self, client):
        payload = {**PAYLOAD_CLIENTE_NORMAL, "valor_patrimonio": 200_000.0}
        resp = client.post("/clientes", json=payload)
        assert resp.json()["prioridade"] == "prioridade_alta"

    def test_cria_cliente_chama_pipefy(self, client):
        client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        assert len(mock_pipefy.cards_criados) == 1
        assert mock_pipefy.cards_criados[0]["email"] == "joao@test.com"


# ---------------------------------------------------------------------------
# Testes — Criar Cliente (validações e erros)
# ---------------------------------------------------------------------------
class TestCriarClienteValidacoes:
    def test_email_duplicado_retorna_422(self, client):
        client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        resp = client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        assert resp.status_code == 422

    def test_email_invalido_retorna_422(self, client):
        payload = {**PAYLOAD_CLIENTE_NORMAL, "cliente_email": "nao-e-email"}
        resp = client.post("/clientes", json=payload)
        assert resp.status_code == 422

    def test_nome_vazio_retorna_422(self, client):
        payload = {**PAYLOAD_CLIENTE_NORMAL, "cliente_nome": ""}
        resp = client.post("/clientes", json=payload)
        assert resp.status_code == 422

    def test_patrimonio_negativo_retorna_422(self, client):
        payload = {**PAYLOAD_CLIENTE_NORMAL, "valor_patrimonio": -1000}
        resp = client.post("/clientes", json=payload)
        assert resp.status_code == 422

    def test_tipo_solicitacao_vazio_retorna_422(self, client):
        payload = {**PAYLOAD_CLIENTE_NORMAL, "tipo_solicitacao": ""}
        resp = client.post("/clientes", json=payload)
        assert resp.status_code == 422

    def test_campos_obrigatorios_ausentes_retorna_422(self, client):
        resp = client.post("/clientes", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Testes — Webhook (fluxo feliz)
# ---------------------------------------------------------------------------
class TestWebhookFluxoFeliz:
    def _criar_cliente(self, client, payload=None):
        return client.post("/clientes", json=payload or PAYLOAD_CLIENTE_NORMAL)

    def test_webhook_retorna_200(self, client):
        self._criar_cliente(client)
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_001",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert resp.status_code == 200

    def test_webhook_status_processed(self, client):
        self._criar_cliente(client)
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_001",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert resp.json()["status"] == "processed"

    def test_webhook_retorna_prioridade(self, client):
        self._criar_cliente(client)
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_001",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert resp.json()["prioridade"] == "prioridade_normal"

    def test_webhook_vip_retorna_prioridade_alta(self, client):
        self._criar_cliente(client, PAYLOAD_CLIENTE_VIP)
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_002",
            "card_id": "card_xyz",
            "cliente_email": "maria@test.com",
        })
        assert resp.json()["prioridade"] == "prioridade_alta"

    def test_webhook_retorna_nome_cliente(self, client):
        self._criar_cliente(client)
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_001",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert resp.json()["cliente_nome"] == "João Silva"

    def test_webhook_chama_pipefy_atualizar(self, client):
        self._criar_cliente(client)
        client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_001",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert len(mock_pipefy.cards_atualizados) == 1
        assert mock_pipefy.cards_atualizados[0]["status"] == "Processado"


# ---------------------------------------------------------------------------
# Testes — Webhook (idempotência)
# ---------------------------------------------------------------------------
class TestWebhookIdempotencia:
    def _criar_e_processar(self, client):
        client.post("/clientes", json=PAYLOAD_CLIENTE_NORMAL)
        return client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_idempotente",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })

    def test_segundo_webhook_retorna_already_processed(self, client):
        self._criar_e_processar(client)
        resp2 = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_idempotente",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert resp2.json()["status"] == "already_processed"

    def test_segundo_webhook_retorna_200(self, client):
        self._criar_e_processar(client)
        resp2 = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_idempotente",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert resp2.status_code == 200

    def test_pipefy_nao_chamado_em_evento_duplicado(self, client):
        self._criar_e_processar(client)
        mock_pipefy.cards_atualizados.clear()  # zera após primeiro processamento
        client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_idempotente",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert len(mock_pipefy.cards_atualizados) == 0


# ---------------------------------------------------------------------------
# Testes — Webhook (erros)
# ---------------------------------------------------------------------------
class TestWebhookErros:
    def test_cliente_nao_encontrado_retorna_404(self, client):
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_erro",
            "card_id": "card_abc",
            "cliente_email": "naoexiste@test.com",
        })
        assert resp.status_code == 404

    def test_event_id_vazio_retorna_422(self, client):
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "",
            "card_id": "card_abc",
            "cliente_email": "joao@test.com",
        })
        assert resp.status_code == 422

    def test_email_invalido_no_webhook_retorna_422(self, client):
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_001",
            "card_id": "card_abc",
            "cliente_email": "nao-e-email",
        })
        assert resp.status_code == 422
