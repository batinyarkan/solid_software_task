import uuid

import pytest
from sqlalchemy import text

from app import app, engine


@pytest.fixture
def client():
    return app.test_client()


@pytest.fixture
def make_cart():
    created = []

    def _make_cart(provider_token="tok_visa", quantities=(2, 1), cart_status="active"):
        user_id, product_id, cart_id = (str(uuid.uuid4()) for _ in range(3))
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO users (id, email, name) VALUES (:id, :email, 'Test')"),
                {"id": user_id, "email": f"{user_id}@test.com"},
            )
            conn.execute(
                text("INSERT INTO products (id, name, price, stock_quantity) VALUES (:id, 'Pen', 10.25, 100)"),
                {"id": product_id},
            )
            conn.execute(
                text("INSERT INTO carts (id, user_id, status) VALUES (:id, :user_id, :status)"),
                {"id": cart_id, "user_id": user_id, "status": cart_status},
            )
            for quantity in quantities:
                conn.execute(
                    text("""
                        INSERT INTO cart_items (cart_id, product_id, quantity, unit_price)
                        VALUES (:cart_id, :product_id, :quantity, 10.25)
                    """),
                    {"cart_id": cart_id, "product_id": product_id, "quantity": quantity},
                )
            if provider_token:
                conn.execute(
                    text("""
                        INSERT INTO user_payment_methods (user_id, provider_token, is_default)
                        VALUES (:user_id, :token, TRUE)
                    """),
                    {"user_id": user_id, "token": provider_token},
                )
        created.append((user_id, product_id))
        return cart_id

    yield _make_cart

    with engine.begin() as conn:
        for user_id, product_id in created:
            params = {"user_id": user_id, "product_id": product_id}
            conn.execute(text("DELETE FROM payments WHERE cart_id IN (SELECT id FROM carts WHERE user_id = :user_id)"), params)
            conn.execute(text("DELETE FROM carts WHERE user_id = :user_id"), params)  # cascades to cart_items
            conn.execute(text("DELETE FROM user_payment_methods WHERE user_id = :user_id"), params)
            conn.execute(text("DELETE FROM users WHERE id = :user_id"), params)
            conn.execute(text("DELETE FROM products WHERE id = :product_id"), params)


def cart_status(cart_id):
    with engine.connect() as conn:
        return conn.execute(text("SELECT status FROM carts WHERE id = :id"), {"id": cart_id}).scalar_one()


def pay(client, cart_id):
    return client.post(f"/carts/{cart_id}/payments")


def test_successful_payment_checks_out_cart(client, make_cart):
    cart_id = make_cart()

    response = pay(client, cart_id)

    assert response.status_code == 201
    payment = response.json["payment"]
    assert payment["status"] == "succeeded"
    assert payment["amount"] == "30.75"  # 3 x 10.25
    assert payment["provider_transaction_id"].startswith("txn_")
    assert cart_status(cart_id) == "checked_out"


def test_declined_card_records_failed_payment_and_keeps_cart_active(client, make_cart):
    cart_id = make_cart(provider_token="tok_fail")

    response = pay(client, cart_id)

    assert response.status_code == 402
    assert response.json["payment"]["status"] == "failed"
    assert response.json["payment"]["provider_transaction_id"] is None
    assert cart_status(cart_id) == "active"


def test_cart_cannot_be_paid_twice(client, make_cart):
    cart_id = make_cart()
    pay(client, cart_id)

    response = pay(client, cart_id)

    assert response.status_code == 409


def test_abandoned_cart_cannot_be_paid(client, make_cart):
    cart_id = make_cart(cart_status="abandoned")

    assert pay(client, cart_id).status_code == 409


def test_empty_cart_cannot_be_paid(client, make_cart):
    cart_id = make_cart(quantities=())

    assert pay(client, cart_id).status_code == 422


def test_user_without_card_cannot_pay(client, make_cart):
    cart_id = make_cart(provider_token=None)

    assert pay(client, cart_id).status_code == 422


@pytest.mark.parametrize("cart_id", [uuid.uuid4(), "not-a-uuid"])
def test_unknown_cart_returns_404(client, cart_id):
    assert pay(client, cart_id).status_code == 404
