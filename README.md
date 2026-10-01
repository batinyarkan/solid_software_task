# Payment endpoint

Minimal payment service for an online shop. Python, Flask, SQLAlchemy, PostgreSQL.

Only Docker is needed.

## Run

```bash
docker compose up --build

# Alice's cart: 1 x 45.00 + 2 x 12.50 -> 201, payment succeeded
curl -i -X POST localhost:5000/carts/a0000000-0000-0000-0000-000000000001/payments

# Same cart again -> 409, cart is already checked out
curl -i -X POST localhost:5000/carts/a0000000-0000-0000-0000-000000000001/payments

# Bob's card is declined -> 402, payment failed
curl -i -X POST localhost:5000/carts/b0000000-0000-0000-0000-000000000001/payments

# Test
docker compose run --rm app pytest -v
```

## API

`POST /carts/<cart_id>/payments` — no request body.

| Status | When |
|---|---|
| `201` | Card charged. Cart is now `checked_out`. |
| `402` | Card declined. Payment saved as `failed`. Cart stays `active`. |
| `404` | Cart does not exist. |
| `409` | Cart is not `active` (already paid or abandoned). |
| `422` | Cart is empty, or the user has no saved card. |

Response for `201` and `402`:

```json
{
  "payment": {
    "id": "6c1f...",
    "cart_id": "a0000000-0000-0000-0000-000000000001",
    "amount": "70.00",
    "currency": "USD",
    "status": "succeeded",
    "provider_transaction_id": "txn_9b2e...",
    "created_at": "2026-10-22T17:00:00.000000+00:00"
  }
}
```

## Assumptions

- **Total**: the total-calculation service already exists. `calculate_total()` is a stand-in: it sums `quantity * unit_price` of the cart items.
- **Card**: the user's default card is used. If no card is default, the newest card is used.
- **Mock provider**: a token that contains `fail` is declined. Every other token succeeds.
- **Failed payments** are saved for audit. The cart stays `active`, so the user can try again.
- **Double payment** is not possible:
  - The cart row is locked (`SELECT ... FOR UPDATE`) during the payment.
  - A partial unique index allows only one `succeeded` payment per cart.
- **Known trade-off**: the provider call runs inside the DB transaction. This is fine for a mock. With a real provider, save a `pending` payment first, call the provider outside the transaction, then update the payment.
