# Back-end — API FastAPI

## Estrutura de pastas

```
backend/
├── requirements.txt
├── .env.example              # copie para .env e ajuste
└── app/
    ├── main.py                # instancia o FastAPI, CORS, inclui routers
    ├── core/
    │   ├── config.py          # Settings (pydantic-settings) lidas do .env
    │   ├── database.py        # engine/session assíncronos (SQLAlchemy + asyncpg)
    │   ├── redis_client.py    # client Redis assíncrono (cache de predições)
    │   └── security.py        # hash de senha (bcrypt) + JWT
    ├── models/                 # SQLAlchemy ORM — espelha database/schema.sql
    │   ├── base.py             # Base declarativa + mixins (UUID PK, timestamps)
    │   ├── enums.py            # bindings dos ENUM nativos do Postgres
    │   ├── user.py             # User, Address
    │   ├── catalog.py          # Category, Product, ProductVariant
    │   ├── inventory.py        # Inventory, InventoryMovement, PriceLog
    │   ├── commerce.py         # Cart, CartItem, Order, OrderItem, Payment
    │   └── ml.py               # MLPrediction, MLModelMetric, RestockSuggestion
    ├── schemas/                 # Pydantic — request/response da API
    ├── services/                 # regras de negócio multi-tabela
    │   ├── inventory_service.py  # aplica movimentações mantendo saldo consistente
    │   └── order_service.py      # checkout: carrinho → pedido → baixa de estoque
    └── api/
        ├── deps.py               # get_current_user, RBAC (require_roles)
        └── v1/
            ├── router.py         # agrega todos os routers sob /api/v1
            └── endpoints/
                ├── auth.py        # /auth/register, /auth/login (JWT)
                ├── users.py       # /users/me, endereços
                ├── categories.py  # /categories
                ├── products.py    # /products (catálogo + variantes)
                ├── inventory.py   # /inventory (saldo, movimentações, ruptura)
                ├── cart.py        # /cart
                ├── orders.py      # /orders (checkout, status)
                ├── reports.py     # /reports (dashboards gerenciais)
                └── predictions.py # /predictions, /ml/metrics, /restock-suggestions
```

## Por que esta organização (para a defesa do TCC)

- **Camadas separadas por responsabilidade** (`models` = estrutura de dados, `schemas` = contrato da API, `services` = regra de negócio, `api/v1/endpoints` = transporte HTTP) — um router nunca acessa o banco diretamente para lógica multi-tabela; ele delega a um `service`. Isso evita duplicar a lógica de baixa de estoque, por exemplo, em vários lugares.
- **`schema.sql` é a fonte de verdade da estrutura do banco**; os models SQLAlchemy apenas mapeiam essas tabelas para uso via ORM. Assim o SQL revisado na Etapa 1 nunca diverge silenciosamente do código Python.
- **Async ponta a ponta** (FastAPI + SQLAlchemy async + asyncpg + redis.asyncio) — atende ao requisito de "execução assíncrona nativa" e evita bloquear o event loop sob carga concorrente (vários usuários navegando/comprando ao mesmo tempo).
- **Redis como camada de cache, não de fonte de verdade** — toda predição também é persistida em `ml_predictions` (Postgres); o Redis só acelera leituras repetidas, e pode ser esvaziado sem perda de dado.

## Como rodar localmente

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # ajuste DATABASE_URL / REDIS_URL

# Suba PostgreSQL e Redis (ex: via Docker) e execute o schema:
psql "$DATABASE_URL" -f ../database/schema.sql

uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Autenticação e papéis (RBAC)

- `POST /api/v1/auth/register` cria um usuário (`customer` por padrão).
- `POST /api/v1/auth/login` (formulário `username`/`password`) retorna um JWT.
- Endpoints de estoque, relatórios e revisão de sugestões de reposição exigem papel `staff`, `manager` ou `admin` (`Depends(require_roles(...))` em `app/api/deps.py`).
