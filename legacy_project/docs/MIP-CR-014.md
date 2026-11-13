# MIP — CR-014: bulk_notify() мовчки ковтає помилки без retry та логування

**Timestamp створення MIP (до змін у коді):** 28.10.2026 13:19:49

| Розділ MIP | Зміст |
|---|---|
| Назва гілки | fix/CR-014-bulk-notify-retry-logging |
| Scope (файли/функції) | src/notify.py: bulk_notify(users, msg), log_notification(user_id, tp, status); новий файл tests/test_notify.py |
| Підхід до реалізації | bulk_notify(): до 2 повторних спроб надсилання з паузою перед збільшенням лічильника failed; кожна помилка логується через log_notification(); у результат додається список failed_emails (ключі sent і failed зберігаються — зворотна сумісність). log_notification(): запис рядка у stderr замість pass. Пауза і кількість retry — параметри з безпечними значеннями за замовчуванням. |
| Нові тести (що перевіряємо) | успішна розсилка без помилок; помилка, потім успіх (side_effect=[Exception, True]) -> sent=1, failed=0; три помилки поспіль (side_effect=[Exception]*3) -> failed=1, email у failed_emails; часткова невдача; логування у stderr; порожній список користувачів; зворотна сумісність ключів результату |
| Критерій Done | 2 retry при помилці; log_notification() пише у stderr; результат містить список failed_emails; тест «помилка -> retry -> success» зелений; регресій у tests/ немає |
| Стратегія відкату | git revert <commit> або відмова від злиття гілки; м'який відкат — виклик bulk_notify(..., retries=0) вимикає повтори |