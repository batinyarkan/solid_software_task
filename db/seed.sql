-- Sample data for local testing.
-- Delete or replace as you like.

INSERT INTO users (id, email, name) VALUES
    ('11111111-1111-1111-1111-111111111111', 'alice@example.com', 'Alice'),
    ('22222222-2222-2222-2222-222222222222', 'bob@example.com',   'Bob');

INSERT INTO products (id, name, price, stock_quantity) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Kettle', 45.00, 10),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Mug',    12.50, 100);

INSERT INTO carts (id, user_id) VALUES
    ('a0000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111'),
    ('b0000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222');

INSERT INTO cart_items (cart_id, product_id, quantity, unit_price) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 1, 45.00),
    ('a0000000-0000-0000-0000-000000000001', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 2, 12.50),
    ('b0000000-0000-0000-0000-000000000001', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 1, 12.50);

INSERT INTO user_payment_methods (user_id, provider_token, last_four, is_default) VALUES
    ('11111111-1111-1111-1111-111111111111', 'tok_visa', '4242', TRUE),
    ('22222222-2222-2222-2222-222222222222', 'tok_fail', '0002', TRUE);
