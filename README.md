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

Следующий этап MVP - возвраты (`Refund`) для успешно обработанных платежей.
На первом шаге поддерживается только один полный refund на один payment.

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

### Refund

Возврат платежа.

В первой версии refund создается только для платежа со статусом `succeeded` и
только на полную сумму платежа. На один payment может быть максимум один refund.

Поля:

- `id`
- `organization_id`
- `payment_id`
- `amount_kopecks`
- `status`
- `reason`
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
        | 1
        |
        | payments.id -> refunds.payment_id
        | 0..1
        v
+-----------------------------------------------------------+
| refunds                                                   |
+---------------------+-------------------------------------+
| id                  | PK                                  |
| organization_id     | FK -> organizations.id              |
| payment_id          | FK -> payments.id, UNIQUE           |
| amount_kopecks      |                                     |
| status              |                                     |
| reason              |                                     |
| created_at          |                                     |
| updated_at          |                                     |
| processed_at        |                                     |
+---------------------+-------------------------------------+
        ^
        | many
        | organizations.id -> refunds.organization_id
        | 1
+-----------------------------------------------------------+
| organizations                                             |
+-----------------------------------------------------------+
```

Связи:

- `api_keys.organization_id` ссылается на `organizations.id`.
- `payments.organization_id` ссылается на `organizations.id`.
- `payments.api_key_id` ссылается на `api_keys.id`.
- `refunds.organization_id` ссылается на `organizations.id`.
- `refunds.payment_id` ссылается на `payments.id` и уникален.

## Merchant API v1

Endpoint'ы для backend'а организации.

```text
POST /api/v1/payments
GET /api/v1/payments/{payment_id}
GET /api/v1/payments/by-order/{merchant_order_id}
POST /api/v1/payments/{payment_id}/refund
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

## Правила Refund

Статусы:

- `pending`
- `succeeded`
- `failed`

Правила создания:

- Refund принадлежит той же `Organization`, что и исходный Payment.
- Refund связан с одним Payment через `payment_id`.
- На один Payment может быть максимум один Refund.
- Refund можно создать только для Payment со статусом `succeeded`.
- Для Payment со статусом `pending` или `failed` создание Refund возвращает
  `409 Conflict`.
- Refund создается на всю сумму исходного Payment.
- `amount_kopecks` для Refund не передается merchant'ом в request body, а
  копируется из Payment.
- Если Refund для Payment уже существует, повторный запрос возвращает
  существующий Refund.


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


