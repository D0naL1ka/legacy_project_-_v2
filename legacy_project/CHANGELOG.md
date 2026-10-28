# Changelog

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