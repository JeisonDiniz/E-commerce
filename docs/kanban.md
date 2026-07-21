# Quadro Kanban — TCC: Loja Virtual com Estoque Inteligente e ML

Colunas: **Backlog** → **A Fazer** → **Em Progresso** → **Em Revisão** → **Concluído**.
Cada card abaixo corresponde a uma entrega incremental rastreável (ex: em um quadro real no Trello/GitHub Projects, cada linha vira um card com este ID).

## Concluído

| ID | Card | Entrega |
|----|------|---------|
| DB-1 | Modelagem do banco de dados | Diagrama ER (`docs/er-diagram.md`) + schema SQL PostgreSQL (`database/schema.sql`) com produtos, variantes, categorias, estoque, movimentações, preços, pedidos, pagamentos, previsões de ML e sugestões de reposição |
| BE-1 | Estrutura do back-end FastAPI | Organização de pastas, conexão PostgreSQL (SQLAlchemy async) e Redis, configuração base |
| BE-2 | Models SQLAlchemy + Pydantic schemas | Mapeamento ORM de todas as tabelas + schemas de request/response |
| BE-3 | Routers de catálogo | Endpoints de categorias, produtos e variantes |
| BE-4 | Routers de estoque | Endpoints de entrada/saída/ajuste + consulta de saldo |
| BE-5 | Routers de usuários e autenticação | Cadastro, login (JWT), perfis (customer/staff/manager/admin) |
| BE-6 | Routers de carrinho e pedidos | Fluxo completo de carrinho → checkout → pedido → pagamento |
| BE-7 | Routers de relatórios | Agregações para os dashboards gerenciais |
| SEED-1 | Dataset sintético de vendas | Geração de dados de categorias, produtos, variantes, estoque e histórico de vendas com sazonalidade (`database/seed/`) |
| ML-1 | Pipeline de features (pandas) | Extração e transformação de `vw_daily_sales`/CSV para os dois modelos (`backend/app/ml/features.py`) |
| ML-2 | Treinamento Prophet | Sazonalidade semanal/mensal/feriados por categoria, avaliação MAE/MAPE (ver `docs/ml-results.md`) |
| ML-3 | Treinamento Random Forest | Pipeline scikit-learn (categoria, tamanho, cor, preço, histórico → demanda) |
| ML-4 | Endpoint de predição + cache Redis | Serve previsões via API (`/predictions/...`), cache-aside no Redis |
| ML-5 | Motor de sugestão de reposição | `train.py` converte previsões em `restock_suggestions` (status pendente, aprovação humana via `/restock-suggestions/{id}/review`) |
| FE-1 | Estrutura do front-end React | Vite + TS + React Router + Zustand + Axios (`frontend/src`) |
| FE-2 | Vitrine / catálogo / ficha de produto | `pages/storefront/HomePage`, `ProductDetailPage` |
| FE-3 | Carrinho e checkout | `pages/storefront/CartPage`, `CheckoutPage`, `OrdersHistoryPage` |
| FE-4 | Painel administrativo — estoque | `pages/admin/ProductsAdminPage`, `InventoryAdminPage` |
| FE-5 | Painel administrativo — dashboard de ML | `pages/admin/DashboardPage` (gráficos), `RestockSuggestionsPage` (aprovar/rejeitar) |
| INT-1 | Integração front-end ↔ back-end | Consumo da API FastAPI pelo React (auth, catálogo, pedidos) — `docs/integration.md` §1 |
| INT-2 | Integração dashboard ↔ predições | Fluxo predição (Prophet/RF) → cache Redis → API → gráficos React — `docs/integration.md` §2 |
| DOC-1 | Documentação para defesa do TCC | README raiz + `docs/er-diagram.md`, `docs/ml-results.md`, `docs/integration.md` |
| FE-6 | Redesign visual da loja | Identidade monocromática, tipografia editorial, header/hero/catálogo/ficha/sacola/checkout no padrão de referência |
| BE-8 | Recuperação de senha | Tabela `password_reset_tokens`, endpoints `/auth/forgot-password` e `/auth/reset-password`, rate limiting via Redis, e-mail "console backend" |
| FE-7 | UX de formulários de senha | `PasswordInput` (mostrar/ocultar + aviso de Caps Lock), telas de esqueci/redefinir senha, labels acessíveis |

## Em Progresso

_(nenhum card em progresso no momento)_

## A Fazer

_(escopo mínimo do TCC concluído — ver Backlog para melhorias futuras)_

## Backlog (melhorias futuras, fora do escopo mínimo do TCC)

| ID | Card |
|----|------|
| BL-1 | Notificações automáticas de ruptura de estoque (e-mail/webhook) |
| BL-2 | Reentreinamento agendado dos modelos (cron/job scheduler) |
| BL-3 | Testes automatizados end-to-end (Playwright/Cypress) |
| BL-4 | Deploy containerizado (Docker Compose) para banco, cache, API e front |
