# PharmaAgent AI — API Reference

Base URL: `http://localhost:8000`

---

## Authentication

### POST /auth/register
Create a new user account.

**Request:**
```json
{ "name": "John Doe", "email": "john@example.com", "password": "pass123" }
```
**Response 201:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "name": "John Doe", "email": "john@example.com", "role": "user" }
}
```

---

### POST /auth/login
Authenticate and receive a JWT token.

**Request:**
```json
{ "email": "john@example.com", "password": "pass123" }
```
**Response 200:** Same as register.

---

## Medicines

### GET /medicines
Get all medicines in inventory.

**Response 200:**
```json
[
  {
    "id": 1, "name": "Paracetamol 500mg", "stock": 500,
    "unit": "tablets", "price": 5.0,
    "prescription_required": false, "expiry_date": "2026-12-31"
  }
]
```

---

### GET /medicines/search?q={query}
Search medicines by name (partial, case-insensitive).

**Example:** `GET /medicines/search?q=para`

---

### GET /medicines/{id}
Get a single medicine by ID.

**Response 404** if not found.

---

## Orders

> All order endpoints require `Authorization: Bearer <token>` header.

### POST /orders/create
Create a new order directly (bypasses agent).

**Request:**
```json
{ "medicine_id": 1, "quantity": 2 }
```
**Response 201:**
```json
{
  "id": 42, "user_id": 1, "medicine_id": 1,
  "quantity": 2, "total_price": 10.0, "status": "confirmed"
}
```
**Response 403** if medicine requires prescription.

---

### GET /orders/user/{user_id}
Get all orders for a specific user. Users can only view their own orders.

---

### GET /orders/all
Get all orders (admin only). Returns 403 for regular users.

---

## AI Agent

### POST /agent/chat
Send a natural language message to the pharmacy agent.

**Request:**
```json
{ "user_id": 1, "message": "I need 2 Paracetamol strips" }
```

**Response 200:**
```json
{
  "response": "✅ Order placed successfully! 2 tablets of 'Paracetamol 500mg' for ₹10.00. Order ID: #42",
  "action": "order_created",
  "order_id": 42,
  "trace_url": null
}
```

**Possible `action` values:**
| Value | Meaning |
|-------|---------|
| `order_created` | Order was successfully created |
| `prescription_required` | Medicine requires prescription — order blocked |
| `out_of_stock` | Insufficient stock |
| `info` | Informational response (no order action) |
| `error` | Agent encountered an error |

---

## Payment

### POST /payment/process
Process payment for an order (dummy, always succeeds in Phase 1).

**Request:**
```json
{ "order_id": 42, "amount": 10.0, "payment_method": "card" }
```

**Response 200:**
```json
{
  "status": "success",
  "transaction_id": "TXN-A1B2C3D4E5F6",
  "message": "Payment of ₹10.00 received via card. Thank you!",
  "order_id": 42
}
```

---

## System

### GET /health
Health check.

```json
{ "status": "healthy", "service": "PharmaAgent AI Backend", "version": "1.0.0" }
```
