# Quadro Kanban — TCC: Loja Virtual com Estoque Inteligente e ML

Colunas: **Backlog** → **A Fazer** → **Em Progresso** → **Em Revisão** → **Concluído**.
Cada card abaixo corresponde a uma entrega incremental rastreável (ex: em um quadro real no Trello/GitHub Projects, cada linha vira um card com este ID).

## Cronograma oficial vs entrega real

O cronograma da definição do trabalho previa as entregas semana a semana até
03/12. Na prática, todo o escopo mínimo (linhas até "Dashboard gerencial")
foi concluído com bastante antecedência — a tabela abaixo rastreia cada
marco do cronograma até a conclusão.

| Marco do cronograma | Data prevista | Status | Evidência |
|---|---|---|---|
| Stack + repositório | 30/07 | ✅ Concluído | Este repositório |
| Setup back-end/front-end | 06/08 | ✅ Concluído | BE-1, FE-1 |
| Modelagem do banco (ER + schema) | 13/08 | ✅ Concluído | DB-1 |
| CRUD produtos/categorias | 20/08 | ✅ Concluído | BE-2, BE-3 |
| Estoque + autenticação | 27/08 | ✅ Concluído | BE-4, BE-5 |
| Vitrine/catálogo (front) | 03/09 | ✅ Concluído | FE-2 |
| Carrinho/checkout | 10/09 | ✅ Concluído | FE-3, BE-6 |
| Painel administrativo | 17/09 | ✅ Concluído | FE-4 |
| Dataset sintético de vendas | 24/09 | ✅ Concluído | SEED-1 |
| Prophet | 01/10 | ✅ Concluído | ML-2 |
| Random Forest | 08/10 | ✅ Concluído | ML-3 |
| ML integrado à API + cache Redis | 15/10 | ✅ Concluído | ML-4, ML-5, INT-2 |
| Dashboard gerencial | 22/10 | ✅ Concluído | FE-5 |
| Testes gerais + validação MAE/MAPE | 29/10 | ✅ Concluído | `docs/ml-results.md`, QA-1 |
| Ajustes finos (bugs/performance/usabilidade) | 05/11 | ✅ Concluído | IMG-1, SEC-1, FIX-1, FE-8 |
| **Congelamento de escopo (feature freeze)** | 12/11 | ✅ **Declarado** | Ver seção abaixo |
| Roteiro de demonstração | 19/11 | ✅ Concluído | [`docs/roteiro-demonstracao.md`](roteiro-demonstracao.md) |
| Ensaio final / ajustes visuais | 26/11 | ⬜ A fazer pelo aluno | Usar o roteiro acima como script do ensaio |
| Entrega final | 03/12 | ⬜ A fazer pelo aluno | Sistema já está pronto — falta o ato de apresentar |

### Declaração de congelamento de escopo (feature freeze)

A partir desta data, o escopo mínimo do TCC está **congelado**: nenhuma
funcionalidade nova entra no sistema antes da apresentação — apenas
correções de bugs encontrados no ensaio/testes finais, se houver. Qualquer
ideia nova vira item de **Backlog** (ver seção ao final deste documento),
não é implementada agora.

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
| IMG-1 | Imagens de produto por cor | Tabela `product_images`, abstração de storage (`app/core/storage.py`, pronta para trocar disco local por nuvem no deploy), upload/remoção validados (Pillow, tipo/tamanho, nome gerado no servidor), galeria no front que troca de foto conforme a cor selecionada, gerenciador de fotos no painel admin |
| SEC-1 | Hardening de segurança | Correção de escalonamento de privilégio no cadastro público (`role` não é mais aceito do cliente), rate limiting de login via Redis, headers de segurança HTTP (`X-Frame-Options`, `X-Content-Type-Options`, etc.), CORS restrito a métodos/headers explícitos, guarda de `SECRET_KEY` padrão em produção — ver [`SECURITY.md`](../SECURITY.md) |
| FIX-1 | Correção de bugs críticos pós-integração | Preços exibidos sem formatação (Decimal serializado como texto), carrinho quebrando com 500 (`MissingGreenlet`), dashboard gerencial quebrando com 500 (parâmetro de data ambíguo no asyncpg), login quebrando (incompatibilidade `passlib`/`bcrypt`), `npm run dev`/`build` quebrados (versões de `vite`/`@vitejs/plugin-react` incompatíveis com o Node instalado) |
| FE-8 | Fluidez e acessibilidade do layout | Sidebar do painel admin responsiva (colapsa em mobile), remoção de botão de menu duplicado no header desktop, correção de acento cortado em títulos (`Ã`/`Ç`), tabelas do admin com rolagem horizontal em telas pequenas |
| QA-1 | Testes end-to-end manuais (Playwright) | Navegação completa da loja, troca de cor/galeria, carrinho, login, painel admin e dashboard testados em um ambiente real (Postgres + Redis + API + front rodando), guiando as correções do FIX-1 |

## Em Progresso

_(nenhum card em progresso no momento)_

## A Fazer

_(escopo mínimo do TCC concluído e congelado — ver declaração de feature freeze acima; próximos passos são o ensaio e a apresentação, não código)_

## Backlog (melhorias futuras, fora do escopo mínimo do TCC)

| ID | Card |
|----|------|
| BL-1 | Notificações automáticas de ruptura de estoque (e-mail/webhook) |
| BL-2 | Reentreinamento agendado dos modelos (cron/job scheduler) |
| BL-3 | Testes automatizados end-to-end (Playwright/Cypress) |
| BL-4 | Deploy containerizado (Docker Compose) para banco, cache, API e front |
