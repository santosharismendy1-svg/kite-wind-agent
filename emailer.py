import os
import smtplib
from email.message import EmailMessage


def send_email(subject: str, body: str):
    """
    Envío por SMTP.
    Recomendado: Gmail con App Password.
    Env vars:
      SMTP_HOST (default smtp.gmail.com)
      SMTP_PORT (default 587)
      EMAIL_USER
      EMAIL_PASS
      EMAIL_TO (puede ser coma-separado)
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    user = os.getenv("EMAIL_USER")
    pwd = os.getenv("EMAIL_PASS")
    to = os.getenv("EMAIL_TO")

    if not user or not pwd or not to:
        raise SystemExit("❌ Faltan EMAIL_USER / EMAIL_PASS / EMAIL_TO en variables de entorno")

    recipients = [x.strip() for x in to.split(",") if x.strip()]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)
