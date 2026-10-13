# Orders sync

Забирает заявки с `ORDERS_URL` (по умолчанию https://test.ooobs.ru/api/orders), нормализует телефоны к `+7XXXXXXXXXX`,
отбрасывает невалидные, дедуплицирует по телефону (max `amount`, при равенстве — позднее `created_at`).

- `GET /result` (также `/` и `/sync`) — JSON `{clients, stats}`
- Идемпотентно: результат вычисляется заново из исходных данных, ничего не накапливается.
- Секретов нет; URL источника задаётся переменной окружения `ORDERS_URL`.

Запуск: `pip install -r requirements.txt && uvicorn main:app --port 8080`
