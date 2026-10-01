-- Payment part
-- One row per charge attempt
-- Failed attempts are kept

CREATE TABLE payments (
    id                      UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id                 UUID           NOT NULL REFERENCES carts(id),
    payment_method_id       UUID           NOT NULL REFERENCES user_payment_methods(id),
    amount                  NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency                CHAR(3)        NOT NULL DEFAULT 'USD',
    status                  TEXT           NOT NULL CHECK (status IN ('succeeded', 'failed')),
    provider_transaction_id TEXT,
    created_at              TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payments_cart_id ON payments(cart_id);

-- A cart can be paid successfully only once
CREATE UNIQUE INDEX uq_payments_one_success_per_cart
    ON payments(cart_id) WHERE status = 'succeeded';
