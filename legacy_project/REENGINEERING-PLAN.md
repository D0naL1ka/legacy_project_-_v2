# Reengineering Plan — src/process.py

Гілка: `reengineering/process-module`

## Baseline (до)
| Метрика | Значення |
|---|---|
| pylint score | 8.16/10 |
| CC proc() | 21 (D) |
| CC validate_order() | 8 (B) |
| LOC | 177 |
| Функцій | 4 |
| Coverage process.py | 0 % |

## To-Be Architecture
| Функція / об'єкт | Відповідальність (SRP) | Очікуваний CC |
|---|---|---|
| `Role`, `OrderStatus` (Enum), константи ставок | Іменовані бізнес-значення замість magic numbers | — |
| `calculate_tax(amount, role)` | Податок за роллю (одне джерело правди) | ≤ 2 |
| `get_discount(amount, role)` | Знижка premium за порогами | ≤ 4 |
| `_index_by_id(items)` | Словник `{id: obj}` замість лінійного пошуку | 2 |
| `_paid_record / _pending_record / _cancelled_record` | Формування запису для одного статусу | 1 |
| `_process_order(order, users, products)` | Обробка одного замовлення → (запис, помилка) | ≤ 5 |
| `build_summary(records, errors, totals)` | Підсумок | ≤ 3 |
| `process_orders(orders, users, products)` | Чиста бізнес-логіка без БД | ≤ 4 |
| `proc(params=None)` | Оркестратор: fetch → process → persist | 1 |
| `validate_order(o)` | Табличні правила валідації | ≤ 5 |

## Ітерації (після кожної — `pytest tests/ -v`)
1. Introduce Enum + Replace Magic Number; прибрати невикористані імпорти.
2. Consolidate Duplicates: 3 гілки ролей у proc() → calculate_tax()/get_discount().
3. Extract Function + словник `{id: obj}` + dict-dispatch статусів.
4. Separate Concerns: `process_orders()` (чиста) + `build_summary()`; `proc()` — оркестратор.
5. validate_order() — табличні правила; docstrings; unit-тести нових функцій.

## Критерій Done
pylint > 7.5; CC proc() < 8, validate_order() < 6, решта < 10; coverage > 80 %;
усі тести зелені; зовнішній інтерфейс (`proc`, `validate_order`, `calculate_tax`, `get_discount`) не змінено.
