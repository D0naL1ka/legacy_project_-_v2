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
