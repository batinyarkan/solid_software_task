import os
import uuid

from flask import Flask, jsonify
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://shop:shop@localhost:5432/shop")

engine = create_engine(DATABASE_URL)
app = Flask(__name__)


def calculate_total(conn, cart_id):
    return conn.execute(
        text("SELECT COALESCE(SUM(quantity * unit_price), 0) FROM cart_items WHERE cart_id = :cart_id"),
        {"cart_id": cart_id},
    ).scalar_one()

# mock payment provider
def charge_card(provider_token, amount):
    if "fail" in provider_token:
        return None
    return f"txn_{uuid.uuid4().hex}"


def error(message, status_code):
    return jsonify(error=message), status_code


def is_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


@app.post("/carts/<cart_id>/payments")
def pay_for_cart(cart_id):
    if not is_uuid(cart_id):
        return error("cart not found", 404)

    with engine.begin() as conn:
        # FOR UPDATE locks the cart, so two parallel requests cannot both pay for it.
        cart = conn.execute(
            text("SELECT user_id, status FROM carts WHERE id = :id FOR UPDATE"),
            {"id": cart_id},
        ).one_or_none()
        if cart is None:
            return error("cart not found", 404)
        if cart.status != "active":
            return error(f"cart is {cart.status}", 409)

        amount = calculate_total(conn, cart_id)
        if amount <= 0:
            return error("cart is empty", 422)

        card = conn.execute(
            text("""
                SELECT id, provider_token FROM user_payment_methods
                WHERE user_id = :user_id
                ORDER BY is_default DESC, created_at DESC
                LIMIT 1
            """),
            {"user_id": cart.user_id},
        ).one_or_none()
        if card is None:
            return error("user has no payment method", 422)

        transaction_id = charge_card(card.provider_token, amount)
        payment = conn.execute(
            text("""
                INSERT INTO payments (cart_id, payment_method_id, amount, status, provider_transaction_id)
                VALUES (:cart_id, :card_id, :amount, :status, :transaction_id)
                RETURNING id, cart_id, amount, currency, status, provider_transaction_id, created_at
            """),
            {
                "cart_id": cart_id,
                "card_id": card.id,
                "amount": amount,
                "status": "succeeded" if transaction_id else "failed",
                "transaction_id": transaction_id,
            },
        ).one()

        if transaction_id:
            conn.execute(
                text("UPDATE carts SET status = 'checked_out', updated_at = NOW() WHERE id = :id"),
                {"id": cart_id},
            )

    body = {
        "id": str(payment.id),
        "cart_id": str(payment.cart_id),
        "amount": str(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
        "provider_transaction_id": payment.provider_transaction_id,
        "created_at": payment.created_at.isoformat(),
    }
    return jsonify(payment=body), 201 if transaction_id else 402
