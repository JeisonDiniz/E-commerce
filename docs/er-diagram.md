# Diagrama Entidade-Relacionamento (ER)

> Renderizável no GitHub, GitLab, VS Code (extensão Mermaid) e em ferramentas como o [Mermaid Live Editor](https://mermaid.live).
> Este diagrama corresponde 1:1 ao schema em [`../database/schema.sql`](../database/schema.sql).

```mermaid
erDiagram
    USERS ||--o{ ADDRESSES : possui
    USERS ||--o{ ORDERS : realiza
    USERS ||--o{ CARTS : possui
    USERS ||--o{ INVENTORY_MOVEMENTS : registra
    USERS ||--o{ PRICE_LOGS : altera
    USERS ||--o{ RESTOCK_SUGGESTIONS : revisa

    CATEGORIES ||--o{ CATEGORIES : subcategoria_de
    CATEGORIES ||--o{ PRODUCTS : classifica
    CATEGORIES ||--o{ ML_PREDICTIONS : agrega

    PRODUCTS ||--o{ PRODUCT_VARIANTS : possui

    PRODUCT_VARIANTS ||--|| INVENTORY : possui
    PRODUCT_VARIANTS ||--o{ INVENTORY_MOVEMENTS : movimenta
    PRODUCT_VARIANTS ||--o{ PRICE_LOGS : historico_preco
    PRODUCT_VARIANTS ||--o{ CART_ITEMS : compoe
    PRODUCT_VARIANTS ||--o{ ORDER_ITEMS : vendido_em
    PRODUCT_VARIANTS ||--o{ ML_PREDICTIONS : previsto_para
    PRODUCT_VARIANTS ||--o{ RESTOCK_SUGGESTIONS : sugerido_para

    CARTS ||--o{ CART_ITEMS : contem

    ORDERS ||--o{ ORDER_ITEMS : contem
    ORDERS ||--o{ PAYMENTS : pago_por
    ORDERS }o--|| ADDRESSES : entregue_em

    ML_PREDICTIONS ||--o{ RESTOCK_SUGGESTIONS : fundamenta

    USERS {
        uuid id PK
        varchar name
        varchar email UK
        varchar password_hash
        user_role role
        timestamptz created_at
        timestamptz updated_at
    }

    ADDRESSES {
        uuid id PK
        uuid user_id FK
        varchar street
        varchar city
        varchar state
        varchar zip_code
        boolean is_default
    }

    CATEGORIES {
        uuid id PK
        uuid parent_id FK
        varchar name
        varchar slug UK
    }

    PRODUCTS {
        uuid id PK
        uuid category_id FK
        varchar name
        text description
        varchar brand
        gender_type gender
        season_type season
        numeric base_price
        boolean active
    }

    PRODUCT_VARIANTS {
        uuid id PK
        uuid product_id FK
        varchar sku UK
        size_type size
        varchar color
        numeric price
        numeric cost_price
    }

    INVENTORY {
        uuid id PK
        uuid variant_id FK "UNIQUE"
        int quantity
        int min_quantity
        int max_quantity
        timestamptz updated_at
    }

    INVENTORY_MOVEMENTS {
        uuid id PK
        uuid variant_id FK
        movement_type movement_type
        int quantity
        varchar reason
        uuid reference_order_id FK
        uuid created_by FK
        timestamptz created_at
    }

    PRICE_LOGS {
        uuid id PK
        uuid variant_id FK
        numeric old_price
        numeric new_price
        uuid changed_by FK
        timestamptz changed_at
    }

    CARTS {
        uuid id PK
        uuid user_id FK
        timestamptz created_at
    }

    CART_ITEMS {
        uuid id PK
        uuid cart_id FK
        uuid variant_id FK
        int quantity
    }

    ORDERS {
        uuid id PK
        uuid user_id FK
        uuid shipping_address_id FK
        order_status status
        numeric total_amount
        timestamptz created_at
    }

    ORDER_ITEMS {
        uuid id PK
        uuid order_id FK
        uuid variant_id FK
        int quantity
        numeric unit_price
    }

    PAYMENTS {
        uuid id PK
        uuid order_id FK
        payment_method method
        payment_status status
        numeric amount
        timestamptz paid_at
    }

    ML_PREDICTIONS {
        uuid id PK
        model_type model_type
        uuid variant_id FK
        uuid category_id FK
        date prediction_date
        numeric predicted_quantity
        numeric confidence_lower
        numeric confidence_upper
        varchar model_version
        timestamptz generated_at
    }

    ML_MODEL_METRICS {
        uuid id PK
        model_type model_type
        numeric mae
        numeric mape
        numeric rmse
        int training_samples
        varchar model_version
        timestamptz trained_at
    }

    RESTOCK_SUGGESTIONS {
        uuid id PK
        uuid variant_id FK
        uuid based_on_prediction_id FK
        int suggested_quantity
        suggestion_status status
        uuid reviewed_by FK
        timestamptz reviewed_at
        timestamptz created_at
    }
```

## Decisões de modelagem (para a defesa do TCC)

1. **`products` vs `product_variants`** — um produto de vestuário (ex: "Camiseta Básica Oversized") tem várias combinações de tamanho/cor, cada uma com SKU e estoque próprios. Separar as duas entidades evita duplicar nome/descrição/categoria a cada variante e é o modelo padrão de e-commerces de moda (mesma abordagem usada por Shopify e VTEX).
2. **`inventory` (snapshot) + `inventory_movements` (log)** — a tabela `inventory` guarda a *quantidade atual* (leitura rápida no catálogo/checkout), enquanto `inventory_movements` é o *livro-razão* de entradas/saídas. Isso permite auditar todo movimento sem recalcular somas a cada requisição, e é a fonte de dados para o treinamento dos modelos de ML (histórico de vendas = saídas do tipo `venda`).
3. **`price_logs` separado de `product_variants.price`** — a coluna `price` sempre reflete o preço vigente; toda alteração gera uma linha em `price_logs`, atendendo ao requisito de "logs de precificação" e permitindo análises futuras de elasticidade de preço.
4. **`ml_predictions` e `ml_model_metrics` desacoplados dos produtos** — previsões são dados derivados (recalculáveis), não fonte de verdade. Guardá-las no Postgres (além do cache Redis) permite auditoria histórica de acurácia e comparação de versões de modelo ao longo do tempo — importante para a seção de resultados do TCC.
5. **`restock_suggestions` com campo `status`** — implementa o requisito de que a IA **sugere**, mas a decisão final é humana: toda sugestão nasce `pendente` e só é efetivada (gerando uma `inventory_movement` de entrada) depois que um gestor aprova.
6. **UUID como chave primária** — evita IDs sequenciais previsíveis expostos via API pública (catálogo) e facilita merge de dados entre ambientes (dev/seed/produção) sem colisão de PKs.
