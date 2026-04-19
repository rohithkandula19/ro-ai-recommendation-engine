"""Pluggable email: Resend (preferred) → SMTP → dev-log fallback."""
import os
import smtplib
from email.mime.text import MIMEText

import httpx
from loguru import logger


FROM_ADDR = os.getenv("EMAIL_FROM", "RO Rec <noreply@ro-rec.local>")
APP_URL = os.getenv("APP_URL", "http://localhost:3000")


async def send_email(to: str, subject: str, body: str) -> bool:
    resend_key = os.getenv("RESEND_API_KEY")
    smtp_url = os.getenv("SMTP_URL")  # smtp://user:pass@host:port

    if resend_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                    json={"from": FROM_ADDR, "to": [to], "subject": subject, "text": body},
                )
                if r.status_code // 100 == 2:
                    return True
                logger.warning(f"Resend failed: {r.status_code} {r.text[:200]}")
        except Exception as e:
            logger.warning(f"Resend error: {e}")

    if smtp_url:
        try:
            from urllib.parse import urlparse
            u = urlparse(smtp_url)
            server = smtplib.SMTP(u.hostname, u.port or 587, timeout=10)
            server.starttls()
            if u.username and u.password:
                server.login(u.username, u.password)
            msg = MIMEText(body)
            msg["From"] = FROM_ADDR
            msg["To"] = to
            msg["Subject"] = subject
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.warning(f"SMTP error: {e}")

    logger.info(f"[DEV] Email to {to}: {subject}\n{body}")
    return False


async def send_password_reset(to: str, token: str) -> bool:
    link = f"{APP_URL}/reset-password?token={token}"
    body = (
        "Reset your password\n\n"
        f"Click here: {link}\n\n"
        "This link expires in 30 minutes. If you did not request this, ignore this email."
    )
    return await send_email(to, "Reset your RO Rec password", body)
