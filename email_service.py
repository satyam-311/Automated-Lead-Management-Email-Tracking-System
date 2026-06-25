import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

# ── Email template ────────────────────────────────────────────────────────────

def _build_html(name: str, requirement: str, trackable_link: str,
                email: str, tracking_pixel: str) -> str:
    safe_name        = escape(name)
    safe_requirement = escape(requirement)
    safe_email       = escape(email)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Thank you for reaching out!</title>
<style>
  body      {{ font-family: Inter, Arial, sans-serif; background:#F0F2F6; margin:0; padding:24px; }}
  .wrap     {{ max-width:580px; margin:0 auto; }}
  .card     {{ background:white; border-radius:16px; overflow:hidden;
               box-shadow:0 4px 24px rgba(0,0,0,0.08); }}
  .header   {{ background:linear-gradient(135deg,#4F46E5 0%,#7C3AED 100%);
               padding:32px 40px; text-align:center; }}
  .header h1{{ color:white; font-size:26px; font-weight:800; margin:0;
               letter-spacing:-0.5px; }}
  .header p {{ color:rgba(255,255,255,0.85); font-size:13px; margin:8px 0 0 0; }}
  .body     {{ padding:36px 40px; }}
  .body h2  {{ color:#111827; font-size:20px; font-weight:700; margin:0 0 12px 0; }}
  .body p   {{ color:#4B5563; font-size:15px; line-height:1.7; margin:0 0 16px 0; }}
  .req-box  {{ background:#F5F3FF; border-left:4px solid #4F46E5; border-radius:8px;
               padding:16px 20px; margin:20px 0; }}
  .req-box p{{ color:#111827; font-style:italic; font-size:14px; margin:0; }}
  .btn      {{ display:inline-block;
               background:linear-gradient(135deg,#4F46E5 0%,#7C3AED 100%);
               color:white; text-decoration:none; padding:14px 32px;
               border-radius:10px; font-weight:600; font-size:15px;
               letter-spacing:0.2px; margin:8px 0 24px 0; }}
  .note     {{ color:#9CA3AF; font-size:12px; line-height:1.6; }}
  .footer   {{ background:#F9FAFB; padding:20px 40px;
               border-top:1px solid #E5E7EB; text-align:center; }}
  .footer p {{ color:#9CA3AF; font-size:11px; margin:0; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="header">
      <h1>⚡ LeadFlow</h1>
      <p>Automated Lead Management &amp; Email Tracking</p>
    </div>
    <div class="body">
      <h2>Hi {safe_name},</h2>
      <p>Thank you for reaching out! We have received your enquiry and our
         team will get back to you within <strong>24 hours</strong>.</p>
      <div class="req-box">
        <p>"{safe_requirement}"</p>
      </div>
      <p>In the meantime, feel free to explore more about our services:</p>
      <a href="{trackable_link}" class="btn">Explore Our Services &rarr;</a>
      <p class="note">
        This email was sent to {safe_email}. If you did not submit this request,
        please ignore this message.
      </p>
    </div>
    <div class="footer">
      <p>&copy; 2025 LeadFlow &mdash; Automated Lead Management</p>
    </div>
  </div>
</div>
{tracking_pixel}
</body>
</html>"""


# ── Public API ────────────────────────────────────────────────────────────────

def send_lead_email(lead_id: int, name: str, email: str, requirement: str) -> bool:
    gmail_user     = os.getenv("GMAIL_USER", "").strip()
    gmail_password = os.getenv("GMAIL_PASSWORD", "").strip()
    tracker_base   = os.getenv("TRACKER_BASE", "http://localhost:5000").rstrip("/")

    if not gmail_user or not gmail_password:
        logger.warning(
            "SMTP credentials not configured. Set GMAIL_USER and GMAIL_PASSWORD in .env. "
            "Lead id=%d email NOT sent.", lead_id
        )
        return False

    trackable_link = f"{tracker_base}/click/{lead_id}"
    tracking_pixel = (
        f'<img src="{tracker_base}/open/{lead_id}" '
        f'width="1" height="1" style="display:none;" alt="" />'
    )

    html_body = _build_html(name, requirement, trackable_link, email, tracking_pixel)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Thank you for reaching out, {name}!"
    msg["From"]    = gmail_user
    msg["To"]      = email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, email, msg.as_string())
        logger.info("Email sent: lead_id=%d to=%s", lead_id, email)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check GMAIL_USER / GMAIL_PASSWORD.")
    except smtplib.SMTPRecipientsRefused:
        logger.error("Recipient refused: %s", email)
    except Exception as exc:
        logger.error("Email send error for lead_id=%d: %s", lead_id, exc)
    return False
