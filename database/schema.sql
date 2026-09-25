-- =====================================================================
-- SCHEMA POSTGRESQL — Loja Virtual de Roupas com Estoque Inteligente e ML
-- TCC: E-commerce + Controle de Estoque + Predição de Tendências (ML)
--
-- Convenções adotadas:
--   - PKs em UUID (gerado via pgcrypto/gen_random_uuid()) para evitar
--     IDs sequenciais previsíveis expostos pela API pública do catálogo.
--   - Todos os relacionamentos usam ON DELETE RESTRICT por padrão para
--     preservar histórico (vendas e movimentações nunca são apagadas
--     em cascata), exceto onde o próprio ciclo de vida exige CASCADE
--     (ex: itens de carrinho quando o carrinho é removido).
--   - Tipos ENUM nativos do Postgres para os campos de domínio fechado
--     (status, papéis, tipos de movimento), o que garante integridade
--     em nível de banco (não depende só de validação na aplicação).
--   - Timestamps em TIMESTAMPTZ (timezone-aware) — essencial para os
--     modelos de série temporal (Prophet), que são sensíveis a fuso
--     horário na hora de agregar vendas por dia.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Extensões
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- fornece gen_random_uuid()

-- ---------------------------------------------------------------------
-- Tipos ENUM (domínios fechados)
-- ---------------------------------------------------------------------
CREATE TYPE user_role AS ENUM ('customer', 'staff', 'manager', 'admin');

CREATE TYPE gender_type AS ENUM ('masculino', 'feminino', 'unissex', 'infantil');

CREATE TYPE season_type AS ENUM ('verao', 'inverno', 'outono', 'primavera', 'o_ano_todo');

CREATE TYPE size_type AS ENUM ('PP', 'P', 'M', 'G', 'GG', 'XG', 'UNICO', '34', '36', '38', '40', '42', '44', '46', '48');

CREATE TYPE movement_type AS ENUM ('entrada', 'saida', 'ajuste', 'devolucao');

CREATE TYPE order_status AS ENUM ('pendente', 'pago', 'processando', 'enviado', 'entregue', 'cancelado');

CREATE TYPE payment_method AS ENUM ('cartao_credito', 'cartao_debito', 'pix', 'boleto');

CREATE TYPE payment_status AS ENUM ('pendente', 'aprovado', 'recusado', 'estornado');

CREATE TYPE model_type AS ENUM ('prophet', 'random_forest');

CREATE TYPE suggestion_status AS ENUM ('pendente', 'aprovada', 'rejeitada');

-- ---------------------------------------------------------------------
-- Função utilitária: atualiza automaticamente a coluna updated_at
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 1. USUÁRIOS E ENDEREÇOS
-- =====================================================================
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(150) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          user_role NOT NULL DEFAULT 'customer',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_users_role ON users(role);

CREATE TABLE addresses (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    street       VARCHAR(255) NOT NULL,
    number       VARCHAR(20) NOT NULL,
    complement   VARCHAR(120),
    neighborhood VARCHAR(120) NOT NULL,
    city         VARCHAR(120) NOT NULL,
    state        CHAR(2) NOT NULL,
    zip_code     VARCHAR(9) NOT NULL,
    is_default   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_addresses_user ON addresses(user_id);

-- Tokens de recuperação de senha ("esqueci minha senha"). Guardamos o HASH
-- do token (nunca o valor em texto puro) — o mesmo princípio de não
-- armazenar segredos em claro aplicado a password_hash. Token de uso único
-- (used_at) e de curta duração (expires_at), enviado por e-mail ao usuário.
CREATE TABLE password_reset_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_password_reset_tokens_user ON password_reset_tokens(user_id);

-- =====================================================================
-- 2. CATÁLOGO: CATEGORIAS, PRODUTOS E VARIANTES
-- =====================================================================
CREATE TABLE categories (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id  UUID REFERENCES categories(id) ON DELETE SET NULL,
    name       VARCHAR(100) NOT NULL,
    slug       VARCHAR(120) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_categories_parent ON categories(parent_id);

CREATE TABLE products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    brand       VARCHAR(100),
    gender      gender_type NOT NULL DEFAULT 'unissex',
    season      season_type NOT NULL DEFAULT 'o_ano_todo',
    base_price  NUMERIC(10, 2) NOT NULL CHECK (base_price >= 0),
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(active);
CREATE INDEX idx_products_gender_season ON products(gender, season);

-- Cada combinação vendável de tamanho/cor de um produto.
-- É a unidade real de estoque, preço e venda (features de ML: categoria
-- vem do produto pai; tamanho, cor e preço vêm diretamente da variante).
CREATE TABLE product_variants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id  UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sku         VARCHAR(60) NOT NULL UNIQUE,
    size        size_type NOT NULL,
    color       VARCHAR(50) NOT NULL,
    price       NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    cost_price  NUMERIC(10, 2) CHECK (cost_price >= 0),
    -- Peso/dimensões da embalagem desta variante — usados para cotar frete
    -- (Melhor Envio) somando os itens do carrinho. Valores padrão razoáveis
    -- para uma peça de roupa dobrada, ajustáveis por produto no cadastro.
    weight_grams INTEGER NOT NULL DEFAULT 300 CHECK (weight_grams > 0),
    height_cm   NUMERIC(6, 2) NOT NULL DEFAULT 3 CHECK (height_cm > 0),
    width_cm    NUMERIC(6, 2) NOT NULL DEFAULT 25 CHECK (width_cm > 0),
    length_cm   NUMERIC(6, 2) NOT NULL DEFAULT 35 CHECK (length_cm > 0),
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, size, color)
);

CREATE TRIGGER trg_variants_updated_at
    BEFORE UPDATE ON product_variants
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_variants_product ON product_variants(product_id);
CREATE INDEX idx_variants_size_color ON product_variants(size, color);

-- Fotos do produto, agrupadas por cor (color = NULL é a imagem "geral",
-- usada como fallback quando a cor selecionada ainda não tem foto própria).
-- `storage_key` guarda sempre uma chave RELATIVA (nunca URL absoluta) para
-- que o back-end possa trocar de storage local para nuvem (S3 etc.) no
-- futuro sem precisar migrar os dados já cadastrados.
CREATE TABLE product_images (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id  UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    color       VARCHAR(50),
    storage_key VARCHAR(500) NOT NULL,
    alt_text    VARCHAR(200),
    sort_order  INTEGER NOT NULL DEFAULT 0,
    is_primary  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_product_images_product_color ON product_images(product_id, color);

-- =====================================================================
-- 3. ESTOQUE: SALDO ATUAL + LIVRO-RAZÃO DE MOVIMENTAÇÕES
-- =====================================================================

-- Snapshot do saldo atual por variante (leitura O(1) no catálogo/checkout).
CREATE TABLE inventory (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id   UUID NOT NULL UNIQUE REFERENCES product_variants(id) ON DELETE CASCADE,
    quantity     INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    min_quantity INTEGER NOT NULL DEFAULT 5 CHECK (min_quantity >= 0),
    max_quantity INTEGER NOT NULL DEFAULT 100 CHECK (max_quantity >= min_quantity),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_inventory_updated_at
    BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_inventory_low_stock ON inventory(variant_id) WHERE quantity <= min_quantity;

-- Livro-razão: toda entrada/saída/ajuste/devolução gera uma linha aqui.
-- É a fonte primária de "histórico de vendas" (movement_type = 'saida'
-- com reference_order_id preenchido) usada no treinamento dos modelos.
CREATE TABLE inventory_movements (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id          UUID NOT NULL REFERENCES product_variants(id) ON DELETE RESTRICT,
    movement_type       movement_type NOT NULL,
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    reason              VARCHAR(150),
    reference_order_id  UUID,  -- FK lógica para orders(id); ver seção 5
    created_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_movements_variant_date ON inventory_movements(variant_id, created_at);
CREATE INDEX idx_movements_type_date ON inventory_movements(movement_type, created_at);

-- Log de precificação: toda alteração de preço de uma variante fica
-- registrada aqui, permitindo auditoria e análises de elasticidade.
CREATE TABLE price_logs (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id UUID NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    old_price  NUMERIC(10, 2) NOT NULL,
    new_price  NUMERIC(10, 2) NOT NULL,
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_price_logs_variant ON price_logs(variant_id, changed_at);

-- =====================================================================
-- 4. CARRINHO
-- =====================================================================
CREATE TABLE carts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_carts_updated_at
    BEFORE UPDATE ON carts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Um carrinho persistente por usuário (modelo simplificado, sem múltiplos
-- carrinhos simultâneos por conta).
CREATE UNIQUE INDEX idx_carts_user_unique ON carts(user_id);

CREATE TABLE cart_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id    UUID NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    added_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (cart_id, variant_id)
);

CREATE INDEX idx_cart_items_cart ON cart_items(cart_id);

-- =====================================================================
-- 5. PEDIDOS, ITENS DE PEDIDO (= VENDAS) E PAGAMENTOS
-- =====================================================================
CREATE TABLE orders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    shipping_address_id UUID NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
    status              order_status NOT NULL DEFAULT 'pendente',
    total_amount        NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    -- Frete escolhido no checkout (cotado via Melhor Envio antes de criar o
    -- pedido) — total_amount já inclui shipping_cost.
    shipping_service        VARCHAR(60),
    shipping_cost           NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (shipping_cost >= 0),
    shipping_deadline_days  INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status_date ON orders(status, created_at);

-- Cada linha é, ao mesmo tempo, um item do pedido e um registro de
-- venda histórica: (data = orders.created_at, categoria/tamanho/cor
-- via variant_id, quantidade, preço praticado). É a tabela-fonte das
-- features de treinamento do Random Forest e da série temporal do Prophet.
CREATE TABLE order_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES product_variants(id) ON DELETE RESTRICT,
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_variant_date ON order_items(variant_id, created_at);

ALTER TABLE inventory_movements
    ADD CONSTRAINT fk_movements_order
    FOREIGN KEY (reference_order_id) REFERENCES orders(id) ON DELETE SET NULL;

CREATE TABLE payments (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    method     payment_method NOT NULL,
    status     payment_status NOT NULL DEFAULT 'pendente',
    amount     NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
    paid_at    TIMESTAMPTZ,
    -- Dados do gateway (Mercado Pago) — NUNCA número de cartão/CVV, que
    -- nunca chegam ao back-end (tokenizados no navegador do cliente).
    -- `gateway_payment_id` é UNIQUE: garante idempotência quando o mesmo
    -- webhook chega duplicado (comportamento normal de gateways).
    gateway              VARCHAR(30) NOT NULL DEFAULT 'mercadopago',
    gateway_payment_id   VARCHAR(100) UNIQUE,
    installments         INTEGER,
    card_brand           VARCHAR(20),
    card_last4           VARCHAR(4),
    pix_qr_code          TEXT,
    pix_qr_code_base64   TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_gateway_payment_id ON payments(gateway_payment_id);

-- =====================================================================
-- 6. MACHINE LEARNING: PREVISÕES, MÉTRICAS E SUGESTÕES DE REPOSIÇÃO
-- =====================================================================

-- Previsões geradas pelos modelos. Persistidas no Postgres (fonte de
-- verdade / auditoria histórica) e espelhadas no Redis (cache de leitura
-- rápida para o dashboard — ver módulo de ML na etapa 3).
CREATE TABLE ml_predictions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type          model_type NOT NULL,
    variant_id          UUID REFERENCES product_variants(id) ON DELETE CASCADE,
    category_id         UUID REFERENCES categories(id) ON DELETE CASCADE,
    prediction_date     DATE NOT NULL,
    predicted_quantity  NUMERIC(10, 2) NOT NULL,
    confidence_lower    NUMERIC(10, 2),
    confidence_upper    NUMERIC(10, 2),
    model_version       VARCHAR(40) NOT NULL,
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Random Forest prevê por variante; Prophet prevê por categoria/global.
    -- Exatamente um dos dois deve estar preenchido.
    CHECK (
        (model_type = 'random_forest' AND variant_id IS NOT NULL AND category_id IS NULL)
        OR
        (model_type = 'prophet' AND category_id IS NOT NULL AND variant_id IS NULL)
    )
);

CREATE INDEX idx_predictions_variant_date ON ml_predictions(variant_id, prediction_date);
CREATE INDEX idx_predictions_category_date ON ml_predictions(category_id, prediction_date);
CREATE INDEX idx_predictions_model_generated ON ml_predictions(model_type, generated_at);

-- Métricas de avaliação de cada treinamento/versão de modelo, usadas
-- para validar os critérios de aceitação definidos no TCC
-- (Prophet: MAE < 5.0 / MAPE < 7%; Random Forest: MAE < 3.0 / MAPE < 5%).
CREATE TABLE ml_model_metrics (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type        model_type NOT NULL,
    model_version     VARCHAR(40) NOT NULL,
    mae               NUMERIC(10, 4) NOT NULL,
    mape              NUMERIC(6, 3) NOT NULL,
    rmse              NUMERIC(10, 4),
    training_samples  INTEGER NOT NULL,
    trained_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes             TEXT
);

CREATE INDEX idx_metrics_model_trained ON ml_model_metrics(model_type, trained_at);

-- Sugestões de reposição derivadas das previsões. O gestor humano
-- SEMPRE aprova ou rejeita — não há compra automática (requisito do TCC).
CREATE TABLE restock_suggestions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id              UUID NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    based_on_prediction_id  UUID REFERENCES ml_predictions(id) ON DELETE SET NULL,
    suggested_quantity      INTEGER NOT NULL CHECK (suggested_quantity > 0),
    status                  suggestion_status NOT NULL DEFAULT 'pendente',
    reviewed_by             UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_restock_status ON restock_suggestions(status, created_at);
CREATE INDEX idx_restock_variant ON restock_suggestions(variant_id);

-- =====================================================================
-- 7. VIEW DE APOIO: VENDAS DIÁRIAS CONSOLIDADAS
-- Usada diretamente pelo pipeline de features (pandas) do módulo de ML
-- para alimentar tanto o Prophet (agregado por data) quanto o
-- Random Forest (agregado por variante/categoria/tamanho/cor).
-- =====================================================================
CREATE VIEW vw_daily_sales AS
SELECT
    oi.variant_id,
    pv.sku,
    pv.size,
    pv.color,
    pv.price,
    p.category_id,
    p.gender,
    p.season,
    date_trunc('day', o.created_at)::date AS sale_date,
    SUM(oi.quantity)                       AS units_sold,
    SUM(oi.quantity * oi.unit_price)       AS revenue
FROM order_items oi
JOIN orders o            ON o.id = oi.order_id
JOIN product_variants pv ON pv.id = oi.variant_id
JOIN products p          ON p.id = pv.product_id
WHERE o.status <> 'cancelado'
GROUP BY oi.variant_id, pv.sku, pv.size, pv.color, pv.price,
         p.category_id, p.gender, p.season, date_trunc('day', o.created_at)::date;

-- =====================================================================
-- Fim do schema
-- =====================================================================
