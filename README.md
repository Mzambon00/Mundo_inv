# Mundo Invest — Client Management API

API empresarial para gerenciamento de clientes com integração inteligente ao Pipefy,
construída com **Clean Architecture** e princípios **SOLID**.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Tecnologias](#tecnologias)
3. [Arquitetura](#arquitetura)
4. [Instalação](#instalação)
5. [Endpoints da API](#endpoints-da-api)
6. [Regras de Negócio](#regras-de-negócio)
7. [Testes](#testes)
8. [Variáveis de Ambiente](#variáveis-de-ambiente)
9. [Estrutura do Projeto](#estrutura-do-projeto)

---

## Visão Geral

Sistema de gestão de clientes para instituições financeiras que:

- Valida dados e calcula prioridade de atendimento automaticamente na criação
- Processa webhooks do Pipefy com garantia de idempotência
- Cria e atualiza cards no Pipefy via GraphQL
- Persiste todos os dados em banco relacional

### Casos de Uso

- **Criação de cliente** → valida email, calcula prioridade, persiste no banco e cria card no Pipefy
- **Processamento de webhook** → atualiza status e prioridade no banco e no Pipefy, com proteção contra reprocessamento

---

## Tecnologias

| Camada        | Tecnologia       | Versão  | Finalidade                    |
|---------------|------------------|---------|-------------------------------|
| Web Framework | FastAPI          | 0.110+  | API REST assíncrona           |
| ORM           | SQLAlchemy       | 2.0+    | Acesso ao banco de dados      |
| Validação     | Pydantic         | 2.0+    | Schemas e validação de dados  |
| Servidor      | Uvicorn          | 0.27+   | Servidor ASGI                 |
| HTTP Client   | HTTPX            | 0.27+   | Chamadas GraphQL ao Pipefy    |
| Testes        | Pytest           | 8.0+    | Suite de testes automatizados |
| Dev DB        | SQLite           | —       | Banco local para desenvolvimento |
| Prod DB       | PostgreSQL       | 14+     | Banco para produção           |

---

## Arquitetura

O projeto segue **Clean Architecture** (Arquitetura Limpa), com dependências apontando
sempre de fora para dentro — a camada de domínio não conhece nenhuma outra:

```
┌─────────────────────────────────────────────────────┐
│  Apresentação (FastAPI — src/main.py)               │
│  Schemas Pydantic, rotas, DI, tratamento de erros  │
├─────────────────────────────────────────────────────┤
│  Aplicação (src/application/use_cases/)             │
│  CriarClienteUseCase, ProcessarWebhookUseCase       │
│  DTOs de entrada/saída, orquestração do fluxo       │
├─────────────────────────────────────────────────────┤
│  Domínio (src/domain/)                              │
│  Entidades, Value Objects, interfaces de repositório│
│  Regras de negócio puras — sem dependências externas│
├─────────────────────────────────────────────────────┤
│  Infraestrutura (src/infrastructure/)               │
│  SQLAlchemy, PipefyAdapter (GraphQL), modelos DB    │
└─────────────────────────────────────────────────────┘
```

### Princípios SOLID aplicados

- **S** — Cada classe tem uma única responsabilidade (repositório, use case, adapter)
- **O** — Novas integrações não exigem modificar use cases existentes
- **L** — Implementações concretas são substituíveis pelas abstrações
- **I** — Interfaces segregadas por responsabilidade (`ClienteRepository`, `EventoRepository`, `PipefyService`)
- **D** — Use cases dependem de abstrações, não de SQLAlchemy ou Pipefy diretamente

### Fluxo de Inversão de Dependências

```
Use Cases
    └── dependem de → ClienteRepository (ABC)
                          ↑ implementado por
                   SQLAlchemyClienteRepository
```

Em testes, `SQLAlchemyClienteRepository` é substituído por mocks sem alterar
nenhuma linha dos use cases.

---

## Instalação

### Pré-requisitos

- Python 3.10+
- pip

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/mundo-inv.git
cd mundo-inv

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie a API
uvicorn src.main:app --reload
```

A documentação interativa estará disponível em:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Endpoints da API

### POST /clientes

Cria um novo cliente, calcula a prioridade e abre card no Pipefy.

**Request:**
```json
{
  "cliente_nome": "João Silva",
  "cliente_email": "joao@empresa.com.br",
  "tipo_solicitacao": "Renda Fixa",
  "valor_patrimonio": 250000.00
}
```

**Response (201):**
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao@empresa.com.br",
  "status": "Aguardando Análise",
  "prioridade": "prioridade_alta",
  "card_id": "card_joao_silva"
}
```

**Erros:**
- `422` — E-mail inválido, duplicado, patrimônio negativo ou campos vazios

---

### POST /webhooks/pipefy/card-updated

Processa evento de webhook recebido do Pipefy. Garante idempotência.

**Request:**
```json
{
  "event_id": "evt_abc123",
  "card_id": "card_456",
  "cliente_email": "joao@empresa.com.br"
}
```

**Response (200) — primeira vez:**
```json
{
  "status": "processed",
  "event_id": "evt_abc123",
  "card_id": "card_456",
  "prioridade": "prioridade_alta",
  "cliente_nome": "João Silva"
}
```

**Response (200) — evento duplicado:**
```json
{
  "status": "already_processed",
  "event_id": "evt_abc123",
  "card_id": "card_456"
}
```

**Erros:**
- `404` — Cliente não encontrado
- `422` — Dados inválidos

---

### GET /health

```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

---

## Regras de Negócio

### Cálculo de Prioridade

A prioridade é calculada **exclusivamente pela entidade `Cliente`**, delegando
para `Prioridade.calcular()`. Isso garante que a regra existe em um único lugar.

| Patrimônio             | Prioridade          |
|------------------------|---------------------|
| >= R$ 200.000,00       | `prioridade_alta`   |
| < R$ 200.000,00        | `prioridade_normal` |

O limiar de R$ 200.000 está centralizado em `Prioridade.LIMIAR_ALTA` — para
alterá-lo, basta modificar um único valor.

### Idempotência de Webhooks

Cada `event_id` é registrado na tabela `eventos` após processamento. Requisições
subsequentes com o mesmo `event_id` retornam `already_processed` sem reprocessar.

### Status do Cliente

- Criação: `"Aguardando Análise"`
- Após webhook: `"Processado"`
- Tentativa de processar cliente já processado: lança `ValueError`

---

## Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Com cobertura
python -m pytest tests/ --cov=src --cov-report=term-missing

# Apenas testes unitários de domínio
python -m pytest tests/test_cliente_entity.py tests/test_email_value_object.py -v

# Apenas testes de integração da API
python -m pytest tests/test_main.py -v
```

### Cobertura por Módulo de Teste

| Arquivo                        | O que cobre                                         |
|-------------------------------|------------------------------------------------------|
| `test_email_value_object.py`  | Email válidos, inválidos, normalização, propriedades |
| `test_cliente_entity.py`      | Prioridade, criação, validações, processamento       |
| `test_main.py`                | Endpoints, validações, webhook, idempotência, erros  |

Os testes de integração usam um banco SQLite em arquivo temporário (limpo entre
cada teste), um mock do `PipefyAdapter` que registra chamadas sem HTTP real, e
overrides de dependências do FastAPI para isolamento completo.

---

## Variáveis de Ambiente

| Variável        | Padrão                        | Descrição                              |
|-----------------|-------------------------------|----------------------------------------|
| `DATABASE_URL`  | `sqlite:///./mundo_invest.db` | URL de conexão com o banco de dados   |
| `PIPEFY_TOKEN`  | `""`                          | Bearer token de autenticação do Pipefy|
| `PIPEFY_PIPE_ID`| `"302428309"`                 | ID do pipe no Pipefy                  |
| `DB_ECHO`       | `"false"`                     | Ativa logs SQL do SQLAlchemy          |

Crie um arquivo `.env` na raiz do projeto (nunca o commite):

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/mundo_invest
PIPEFY_TOKEN=seu_token_aqui
PIPEFY_PIPE_ID=302428309
```

---

## Estrutura do Projeto

```
Mundo_Inv/
├── src/
│   ├── domain/                          # Regras de negócio puras
│   │   ├── entities/
│   │   │   └── cliente.py               # Entidade Cliente
│   │   ├── value_objects/
│   │   │   ├── email.py                 # Email (imutável, validado)
│   │   │   └── prioridade.py            # Prioridade (enum + regra)
│   │   └── repositories/               # Interfaces (portas de saída)
│   │       ├── cliente_repository.py
│   │       ├── evento_repository.py
│   │       └── pipefy_service.py
│   │
│   ├── application/
│   │   └── use_cases/
│   │       ├── criar_cliente_use_case.py
│   │       └── processar_webhook_use_case.py
│   │
│   ├── infrastructure/                  # Adaptadores concretos
│   │   ├── database/
│   │   │   ├── models.py               # SQLAlchemy models
│   │   │   ├── connection.py           # Session management
│   │   │   ├── cliente_repository_impl.py
│   │   │   └── evento_repository_impl.py
│   │   └── graphql/
│   │       └── pipefy_adapter.py       # GraphQL client
│   │
│   └── main.py                          # FastAPI app + DI
│
├── tests/
│   ├── test_email_value_object.py
│   ├── test_cliente_entity.py
│   └── test_main.py
│
├── scripts/
│   └── reset_database.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Licença

MIT — Marcos Zambon, 2026
