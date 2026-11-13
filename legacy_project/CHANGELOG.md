# Changelog

### Changed
- Реінженерія `src/process.py` (ПЗ 8): `proc()` — оркестратор (CC 21 → 1), чиста функція
  `process_orders()` без звернень до БД, `build_summary()`, обробники статусів через словник,
  пошук користувача/продукту через `{id: obj}` замість вкладених циклів.
- Податки та знижки — лише в `calculate_tax()` / `get_discount()` (закрито дублювання CR-212).
- Magic numbers → `Role`, `OrderStatus` (Enum) та іменовані константи.
- `validate_order()` — табличні правила (CC 8 → 4), поведінка не змінена.

### Added
- `tests/test_process.py` — 48 тестів (characterization + unit), coverage `process.py` 100 %.
- `REENGINEERING-PLAN.md` — Reengineering Plan.

### Known follow-ups (not in reengineering scope)
- Статус `refunded` допустимий у `validate_order()`, але `proc()` повертає для нього помилку
  «unknown status» — поведінку збережено, потрібен окремий CR.
- Ставки та ролі дублюються у `config/settings.py`; `analytics.py` має власну ставку 0.2.
### Fixed
- CR-014 (Preventive): `bulk_notify()` більше не ковтає помилки мовчки — до 2 повторних спроб
  з паузою, логування кожної помилки у stderr, список `failed_emails` у результаті
  (ключі `sent` і `failed` збережено для зворотної сумісності).
- CR-014: `log_notification()` записує подію у stderr (раніше — `pass`).

### Added
- `tests/test_notify.py` — 10 тестів для `bulk_notify()` і `log_notification()`.
- `docs/MIP-CR-014.md` — Maintenance Implementation Plan.

### Known follow-ups (not in CR-014)
- `send_email()` — заглушка; повернення `False` не вважається помилкою.
- `settings.MAX_RETRIES` не використовується; у `notify.py` власна константа `BULK_RETRIES`.
- Сповіщення адміністратора про невдалі розсилки та запис у БД не реалізовано.
