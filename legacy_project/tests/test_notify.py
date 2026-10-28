# tests/test_notify.py
# Tests for CR-014: bulk_notify() retry + logging, log_notification() -> stderr

import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import notify  # noqa: E402

USERS = [
    {"id": 1, "email": "a@test.com"},
    {"id": 2, "email": "b@test.com"},
]


@mock.patch("src.notify.time.sleep")
@mock.patch("src.notify.send_email")
def test_bulk_notify_all_success(mock_send, mock_sleep):
    mock_send.return_value = True
    result = notify.bulk_notify(USERS, "hello")
    assert result["sent"] == 2
    assert result["failed"] == 0
    assert result["failed_emails"] == []
    assert mock_send.call_count == 2
    mock_sleep.assert_not_called()


@mock.patch("src.notify.time.sleep")
@mock.patch("src.notify.send_email")
def test_bulk_notify_retry_then_success(mock_send, mock_sleep):
    # first attempt fails, second succeeds -> user is counted as sent
    mock_send.side_effect = [Exception("smtp error"), True]
    result = notify.bulk_notify([USERS[0]], "hello")
    assert result["sent"] == 1
    assert result["failed"] == 0
    assert result["failed_emails"] == []
    assert mock_send.call_count == 2
    mock_sleep.assert_called_once()


@mock.patch("src.notify.time.sleep")
@mock.patch("src.notify.send_email")
def test_bulk_notify_all_attempts_fail(mock_send, mock_sleep):
    # 1 attempt + 2 retries = 3 calls, then the user is counted as failed
    mock_send.side_effect = [Exception("e1"), Exception("e2"), Exception("e3")]
    result = notify.bulk_notify([USERS[0]], "hello")
    assert result["sent"] == 0
    assert result["failed"] == 1
    assert result["failed_emails"] == ["a@test.com"]
    assert mock_send.call_count == 3
    assert mock_sleep.call_count == 2  # no pause after the last attempt


@mock.patch("src.notify.time.sleep")
@mock.patch("src.notify.send_email")
def test_bulk_notify_partial_failure(mock_send, mock_sleep):
    def fake_send(to, subj, body):
        if to == "b@test.com":
            raise ConnectionError("down")
        return True

    mock_send.side_effect = fake_send
    result = notify.bulk_notify(USERS, "hello")
    assert result["sent"] == 1
    assert result["failed"] == 1
    assert result["failed_emails"] == ["b@test.com"]


@mock.patch("src.notify.time.sleep")
@mock.patch("src.notify.send_email")
def test_bulk_notify_logs_errors_to_stderr(mock_send, mock_sleep, capsys):
    mock_send.side_effect = [Exception("boom")] * 3
    notify.bulk_notify([USERS[0]], "hello")
    err = capsys.readouterr().err
    assert "boom" in err
    assert "user_id=1" in err
    assert "failed after 3 attempts" in err


@mock.patch("src.notify.time.sleep")
@mock.patch("src.notify.send_email")
def test_bulk_notify_empty_users(mock_send, mock_sleep):
    result = notify.bulk_notify([], "hello")
    assert result == {"sent": 0, "failed": 0, "failed_emails": []}
    mock_send.assert_not_called()


@mock.patch("src.notify.time.sleep")
@mock.patch("src.notify.send_email")
def test_bulk_notify_retries_zero_disables_retry(mock_send, mock_sleep):
    mock_send.side_effect = [Exception("e1")]
    result = notify.bulk_notify([USERS[0]], "hello", retries=0)
    assert result["failed"] == 1
    assert mock_send.call_count == 1
    mock_sleep.assert_not_called()


@mock.patch("src.notify.time.sleep")
@mock.patch("src.notify.send_email")
def test_bulk_notify_negative_retries_still_sends_once(mock_send, mock_sleep):
    mock_send.return_value = True
    result = notify.bulk_notify([USERS[0]], "hello", retries=-5)
    assert result["sent"] == 1
    assert mock_send.call_count == 1


@mock.patch("src.notify.send_email")
def test_bulk_notify_result_keeps_old_keys(mock_send):
    # backward compatibility: callers that read only sent/failed keep working
    mock_send.return_value = True
    result = notify.bulk_notify(USERS, "hello")
    assert {"sent", "failed"} <= set(result)


def test_log_notification_writes_to_stderr(capsys):
    notify.log_notification(42, "order_confirmed", "sent")
    captured = capsys.readouterr()
    assert "user_id=42" in captured.err
    assert "type=order_confirmed" in captured.err
    assert "status=sent" in captured.err
    assert captured.out == ""