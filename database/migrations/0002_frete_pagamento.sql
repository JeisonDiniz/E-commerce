-- Migração incremental para bancos já provisionados a partir de uma versão
-- anterior de database/schema.sql (sem frete e sem os campos de gateway de
-- pagamento). Rode uma única vez:
--   psql -U postgres -d ecommerce_ml -f database/migrations/0002_frete_pagamento.sql
-- Quem estiver criando o banco do zero não precisa disso: basta rodar o
-- database/schema.sql atualizado, que já inclui essas colunas.

ALTER TABLE product_variants
    ADD COLUMN IF NOT EXISTS weight_grams INTEGER NOT NULL DEFAULT 300 CHECK (weight_grams > 0),
    ADD COLUMN IF NOT EXISTS height_cm NUMERIC(6, 2) NOT NULL DEFAULT 3 CHECK (height_cm > 0),
    ADD COLUMN IF NOT EXISTS width_cm NUMERIC(6, 2) NOT NULL DEFAULT 25 CHECK (width_cm > 0),
    ADD COLUMN IF NOT EXISTS length_cm NUMERIC(6, 2) NOT NULL DEFAULT 35 CHECK (length_cm > 0);

ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS shipping_service VARCHAR(60),
    ADD COLUMN IF NOT EXISTS shipping_cost NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (shipping_cost >= 0),
    ADD COLUMN IF NOT EXISTS shipping_deadline_days INTEGER;

ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS gateway VARCHAR(30) NOT NULL DEFAULT 'mercadopago',
    ADD COLUMN IF NOT EXISTS gateway_payment_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS installments INTEGER,
    ADD COLUMN IF NOT EXISTS card_brand VARCHAR(20),
    ADD COLUMN IF NOT EXISTS card_last4 VARCHAR(4),
    ADD COLUMN IF NOT EXISTS pix_qr_code TEXT,
    ADD COLUMN IF NOT EXISTS pix_qr_code_base64 TEXT;

-- UNIQUE precisa ser adicionada separadamente (ADD COLUMN ... UNIQUE não é
-- aceito em todas as versões do Postgres da mesma forma); ignora se já existir.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'payments_gateway_payment_id_key'
    ) THEN
        ALTER TABLE payments ADD CONSTRAINT payments_gateway_payment_id_key UNIQUE (gateway_payment_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_payments_gateway_payment_id ON payments(gateway_payment_id);
