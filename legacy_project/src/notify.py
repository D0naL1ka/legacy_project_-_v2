# notify.py
# Notification system
# DEPRECATED - use new_notify.py (which doesn't exist yet)
# kept for reference

import datetime
import smtplib
import sys
import time
# from email.mime.text import MIMEText  # commented out - breaks on server

# config (move to env someday)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "system@company.com"
SMTP_PASS = "qwerty123"  # yeah yeah, I know

# bulk_notify retry settings (CR-014)
BULK_RETRIES = 2        # retries after the first failed attempt
BULK_RETRY_DELAY = 1.0  # seconds to wait between attempts


def send_email(to, subj, body):
    # TODO: implement properly
    # old implementation below was removed because it broke prod
    # try:
    #     msg = MIMEText(body)
    #     msg['Subject'] = subj
    #     msg['From'] = SMTP_USER
    #     msg['To'] = to
    #     s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    #     s.starttls()
    #     s.login(SMTP_USER, SMTP_PASS)
    #     s.send_message(msg)
    #     s.quit()
    #     return True
    # except Exception as e:
    #     print("email error:", e)
    #     return False
    print(f"[STUB] Would send email to {to}: {subj}")
    return True


def notify_user(user_id, msg_type, data=None):
    if msg_type == 1:
        send_email(
            data.get('email', ''),
            "Order Confirmed",
            f"Your order #{data.get('order_id')} has been confirmed."
        )
    elif msg_type == 2:
        send_email(
            data.get('email', ''),
            "Payment Received",
            f"Payment of {data.get('amount')} UAH received."
        )
    elif msg_type == 3:
        send_email(
            data.get('email', ''),
            "Order Cancelled",
            f"Your order #{data.get('order_id')} was cancelled."
        )
    # type 4 was removed but code wasn't cleaned up
    # elif msg_type == 4:
    #     send_sms(...)


def _send_with_retry(user, email, msg, retries, delay):
    user_id = user.get('id')
    attempts = max(0, retries) + 1
    for attempt in range(1, attempts + 1):
        try:
            send_email(email, "Notification", msg)
            return True
        except Exception as exc:
            if attempt < attempts:
                log_notification(
                    user_id, "bulk",
                    f"error on attempt {attempt}, retry in {delay}s: {exc}")
                time.sleep(delay)
            else:
                log_notification(
                    user_id, "bulk",
                    f"failed after {attempts} attempts: {exc}")
    return False


def bulk_notify(users, msg, retries=BULK_RETRIES, delay=BULK_RETRY_DELAY):
    sent = 0
    failed_emails = []
    for u in users:
        email = u.get('email', '')
        if _send_with_retry(u, email, msg, retries, delay):
            sent += 1
        else:
            failed_emails.append(email)
    return {
        "sent": sent,
        "failed": len(failed_emails),
        "failed_emails": failed_emails,
    }


def log_notification(user_id, tp, status):
    # persistence to DB is out of scope of CR-014
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"[NOTIFY] {timestamp} user_id={user_id} type={tp} status={status}",
        file=sys.stderr,
    )