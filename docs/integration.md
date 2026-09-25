# Integração completa (Etapa 5)

Como as quatro peças do sistema (PostgreSQL, Redis, FastAPI, React) e os
dois modelos de ML se conectam, ponta a ponta.

## 1. Como o React consome a API FastAPI

```mermaid
sequenceDiagram
    participant U as Usuário (navegador)
    participant R as React (Vite dev server :5173)
    participant A as FastAPI (:8000)
    participant DB as PostgreSQL
    participant C as Redis

    U->>R: Acessa /produtos/:id, clica "Adicionar ao carrinho"
    R->>A: POST /api/v1/cart/items (Authorization: Bearer <JWT>)
    A->>DB: INSERT/UPDATE cart_items
    A-->>R: CartRead (itens + preço + nome do produto)
    R-->>U: Atualiza contador do carrinho (zustand: cartStore)

    U->>R: Confirma pedido no checkout
    R->>A: POST /api/v1/orders {shipping_address_id, payment_method}
    A->>DB: INSERT orders + order_items + payments;<br/>baixa de estoque via inventory_movements (saida)
    A-->>R: OrderRead
    R-->>U: Redireciona para /meus-pedidos
```

Pontos-chave:
- **Vite faz proxy de `/api` para `http://localhost:8000`** (`frontend/vite.config.ts`) — em desenvolvimento, o React nunca precisa saber a porta real do back-end, e não há problema de CORS entre `:5173` e `:8000`.
- **Todo request autenticado carrega o JWT** via interceptor do Axios (`frontend/src/api/client.ts`), que também desloga automaticamente o usuário em caso de `401`.
- **Cada domínio tem seu próprio módulo de API tipado** (`frontend/src/api/*.ts`), espelhando 1:1 os routers do back-end (`backend/app/api/v1/endpoints/*.py`) — facilita rastrear qual endpoint alimenta qual tela.

## 2. Como as previsões de ML chegam ao dashboard

```mermaid
sequenceDiagram
    participant T as app.ml.train (script offline)
    participant DB as PostgreSQL
    participant A as FastAPI
    participant C as Redis
    participant R as React (DashboardPage)
    participant G as Gestor

    T->>DB: Treina Prophet (por categoria) e Random Forest (por variante)
    T->>DB: INSERT ml_model_metrics, ml_predictions, restock_suggestions (status=pendente)

    Note over R,A: Gestor abre /admin (DashboardPage)
    R->>A: GET /api/v1/predictions/categories/{id}
    A->>C: GET prediction:prophet:{id} (cache-aside)
    alt cache miss
        A->>DB: SELECT * FROM ml_predictions WHERE ...
        A->>C: SET prediction:prophet:{id} (TTL configurável)
    end
    A-->>R: MLPrediction[] (yhat + intervalo de confiança)
    R-->>G: CategoryTrendChart (linha + faixa de confiança)

    G->>R: Abre "Sugestões de reposição", clica "Aprovar"
    R->>A: POST /api/v1/restock-suggestions/{id}/review {approve: true}
    A->>DB: UPDATE restock_suggestions SET status='aprovada', reviewed_by, reviewed_at
    Note over A,DB: Nenhuma compra/entrada de estoque é gerada automaticamente —<br/>a entrada física é lançada manualmente depois, via POST /inventory/movements
```

Pontos-chave:
- **O treinamento (`app.ml.train`) é desacoplado do runtime da API** — roda como um script separado (ver `backend/app/ml/README.md`), o que é o padrão esperado para ML em produção (retreinar não deve exigir redeploy da API). Reexecutar o treinamento apenas substitui as linhas em `ml_predictions`/`ml_model_metrics`/`restock_suggestions`.
- **Redis é só cache de leitura (cache-aside), nunca fonte de verdade** — se o Redis for limpo, a próxima requisição recalcula a partir do Postgres e repopula o cache automaticamente (`backend/app/api/v1/endpoints/predictions.py::_cached_predictions`).
- **A aprovação humana é obrigatória e não há atalho no código** para transformar uma sugestão em movimento de estoque automaticamente — reforça o requisito do TCC de que a decisão final de compra é sempre do gestor.

## 3. Como uma foto de produto chega até a galeria por cor

```mermaid
sequenceDiagram
    participant G as Gestor (painel admin)
    participant R as React (ProductsAdminPage)
    participant A as FastAPI
    participant P as Pillow (validação)
    participant S as StorageBackend (local)
    participant DB as PostgreSQL
    participant C as Cliente (ProductDetailPage)

    G->>R: Escolhe a cor "Preto", seleciona um arquivo, clica "Enviar imagem"
    R->>A: POST /products/{id}/images (multipart: file, color)
    A->>A: Valida content-type (JPEG/PNG/WEBP) e tamanho (MAX_UPLOAD_SIZE_MB)
    A->>P: Abre e re-salva a imagem (confirma que é um arquivo de imagem de<br/>verdade, descarta metadados/qualquer payload embutido)
    A->>S: save(bytes, chave gerada com uuid4 — nunca o nome do arquivo do cliente)
    A->>DB: INSERT product_images (product_id, color, storage_key)
    A-->>R: ProductImageRead (url resolvida via StorageBackend.url_for)

    Note over C,A: Cliente abre a ficha do produto
    C->>A: GET /products/{id}
    A-->>C: ProductRead.images[] (cada foto já com a cor associada)
    C->>C: Clica no swatch "Preto" → filtra images por color === "Preto"<br/>e troca a galeria (fallback: cor geral → qualquer foto → placeholder)
```

Pontos-chave:
- **`storage_key` nunca é uma URL** — é resolvida em tempo de leitura via `StorageBackend.url_for()` (`backend/app/core/storage.py`). Trocar de disco local para um provedor de nuvem no deploy é implementar uma nova classe ali; nada no front-end ou no schema do banco muda.
- **A troca de galeria por cor é 100% client-side** — o back-end já manda todas as fotos do produto numa única resposta; o React apenas filtra localmente (`ProductDetailPage.tsx`) ao clicar em um swatch, sem round-trip extra à API.
- **Em desenvolvimento, o Vite precisa de proxy para `/media`** (além de `/api`) — sem isso, as imagens servidas pelo back-end em `:8000/media/...` não carregam quando a página é aberta em `:5173` (`frontend/vite.config.ts`).

## 4. Checklist de verificação end-to-end

1. `psql "$DATABASE_URL" -f database/schema.sql` — cria as tabelas.
2. `cd backend && python -m scripts.seed_database` — popula catálogo + 2 anos de histórico de vendas sintético.
3. `python -m app.ml.train --source db` — treina os modelos e grava previsões/sugestões.
4. `uvicorn app.main:app --reload` — sobe a API em `:8000`; Swagger em `/docs`.
5. `cd frontend && npm run dev` — sobe o React em `:5173`.
6. Login como `gestor@loja.com` (senha `Senha@123`) → `/admin` deve mostrar gráficos de vendas, a previsão de tendência por categoria e sugestões de reposição pendentes.
7. Login como um cliente (`cliente1@exemplo.com`) → navegar no catálogo, adicionar ao carrinho, finalizar compra → o pedido deve aparecer em `/meus-pedidos` e o estoque da variante comprada deve diminuir (visível em `/admin/estoque`).
8. Como `gestor@loja.com`, em `/admin/produtos` → "Gerenciar fotos" de um produto, subir uma imagem para uma cor → abrir a ficha desse produto na loja e confirmar que a galeria troca ao clicar nessa cor.