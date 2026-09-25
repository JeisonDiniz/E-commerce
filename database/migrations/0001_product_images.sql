-- Migração incremental para bancos já provisionados a partir de uma versão
-- anterior de database/schema.sql (que não tinha suporte a imagens de
-- produto). Rode este arquivo uma única vez com psql, por exemplo:
--   psql -U postgres -d ecommerce_ml -f database/migrations/0001_product_images.sql
-- Quem estiver criando o banco do zero não precisa disso: basta rodar o
-- database/schema.sql atualizado, que já inclui esta tabela.

CREATE TABLE IF NOT EXISTS product_images (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id  UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    color       VARCHAR(50),
    storage_key VARCHAR(500) NOT NULL,
    alt_text    VARCHAR(200),
    sort_order  INTEGER NOT NULL DEFAULT 0,
    is_primary  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_images_product_color ON product_images(product_id, color);
