# Учебная payment platform

Учебный backend-проект на FastAPI: небольшая симуляция payment provider /
интернет-эквайринга.

Проект не работает с настоящими деньгами, банковскими картами и реальной
банковской инфраструктурой. Все платежи и внешние провайдеры будут
симулироваться.

## MVP v1

Первая версия фокусируется на создании платежей через API мерчанта.

Merchant backend отправляет запрос в нашу систему, используя API key. Наша
система определяет организацию по ключу и создает платеж со статусом
`pending`.

## Таблицы

### Organization

Организация / merchant, которому принадлежат API keys и платежи.

Поля:

- `id`
- `name`

### ApiKey

API key, с помощью которого backend организации обращается к Merchant API.

Поля:

- `id`
- `organization_id`
- `name`
- `secret_hash`
- `is_active`

### Payment

Платеж, созданный организацией через Merchant API.

Поля:

- `id`
- `organization_id`
- `api_key_id`
- `amount_kopecks`
- `status`
- `merchant_order_id`
- `description`
- `created_at`
- `updated_at`
- `processed_at`

## Схема таблиц и связей

```text
+-----------------------------------------------------------+
| organizations                                             |
+---------------------+-------------------------------------+
| id                  | PK                                  |
| name                |                                     |
+---------------------+-------------------------------------+
        | 1
        |
        | organizations.id -> api_keys.organization_id
        | many
        v
+-----------------------------------------------------------+
| api_keys                                                  |
+---------------------+-------------------------------------+
| id                  | PK                                  |
| organization_id     | FK -> organizations.id              |
| name                |                                     |
| secret_hash         |                                     |
| is_active           |                                     |
+---------------------+-------------------------------------+
        | 1
        |
        | api_keys.id -> payments.api_key_id
        | many
        v
+-----------------------------------------------------------+
| payments                                                  |
+---------------------+-------------------------------------+
| id                  | PK                                  |
| organization_id     | FK -> organizations.id              |
| api_key_id          | FK -> api_keys.id                   |
| amount_kopecks      |                                     |
| status              |                                     |
| merchant_order_id   |                                     |
| description         |                                     |
| created_at          |                                     |
| updated_at          |                                     |
| processed_at        |                                     |
+---------------------+-------------------------------------+
        ^
        | many
        | organizations.id -> payments.organization_id
        | 1
+-----------------------------------------------------------+
| organizations                                             |
+-----------------------------------------------------------+
```

Связи:

- `api_keys.organization_id` ссылается на `organizations.id`.
- `payments.organization_id` ссылается на `organizations.id`.
- `payments.api_key_id` ссылается на `api_keys.id`.

## Merchant API v1

Endpoint'ы для backend'а организации.

```text
POST /api/v1/payments
GET /api/v1/payments/{payment_id}
GET /api/v1/payments/by-order/{merchant_order_id}
```

Авторизация:

```http
Authorization: Bearer <api_key>
```

`organization_id` и `api_key_id` не передаются в body запроса. Система
определяет их по API key.

## Создание платежа

Request body:

```json
{
  "merchant_order_id": "order_42",
  "amount_kopecks": 150000,
  "description": "Оплата заказа #42"
}
```

Response:

```json
{
  "id": 10,
  "merchant_order_id": "order_42",
  "amount_kopecks": 150000,
  "status": "pending",
  "description": "Оплата заказа #42",
  "created_at": "2026-09-30T12:00:00Z",
  "updated_at": "2026-09-30T12:00:00Z",
  "processed_at": null
}
```

## Правила Payment

Статусы:

- `pending`
- `succeeded`
- `failed`

Разрешенные переходы:

```text
pending -> succeeded
pending -> failed
```

Запрещенные переходы:

```text
succeeded -> failed
failed -> succeeded
succeeded -> succeeded
failed -> failed
```

Если платеж уже в финальном статусе, попытка изменить его статус должна
возвращать `409 Conflict`.

Ограничения:

- `amount_kopecks` хранится в копейках.
- Минимальная сумма: `5000` копеек.
- Максимальная сумма: `100000000` копеек.
- `merchant_order_id` обязателен.
- `merchant_order_id` не может быть пустым.
- Максимальная длина `merchant_order_id`: `128`.
- `description` необязателен.
- Максимальная длина `description`: `500`.
- Пара `organization_id + merchant_order_id` уникальна.

Повторное создание платежа:

- Если `organization_id + merchant_order_id` уже существуют и данные совпадают,
  возвращается существующий Payment.
- Если `organization_id + merchant_order_id` уже существуют, но важные данные
  отличаются, возвращается `409 Conflict`.

## Internal API v1

Внутренний endpoint для учебной симуляции обработки платежа.

```text
POST /internal/payments/{payment_id}/process
```

Request body:

```json
{
  "status": "succeeded"
}
```

или:

```json
{
  "status": "failed"
}
```

Этот endpoint не является Merchant API. Merchant не должен сам подтверждать
успешность своих платежей.
