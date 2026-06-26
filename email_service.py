import logging
import os
from html import escape

import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


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


def send_lead_email(lead_id: int, name: str, email: str, requirement: str) -> bool:
    api_key      = os.getenv("RESEND_API_KEY", "").strip()
    tracker_base = os.getenv("TRACKER_BASE", "http://localhost:5000").rstrip("/")

    if not api_key:
        logger.warning(
            "RESEND_API_KEY not configured. Set it in .env. "
            "Lead id=%d email NOT sent.", lead_id
        )
        return False

    resend.api_key = api_key

    trackable_link = f"{tracker_base}/click/{lead_id}"
    tracking_pixel = (
        f'<img src="{tracker_base}/open/{lead_id}" '
        f'width="1" height="1" style="display:none;" alt="" />'
    )

    html_body = _build_html(name, requirement, trackable_link, email, tracking_pixel)

    try:
        resend.Emails.send({
            "from":    "onboarding@resend.dev",
            "to":      [email],
            "subject": f"Thank you for reaching out, {name}!",
            "html":    html_body,
        })
        logger.info("Email sent via Resend: lead_id=%d to=%s", lead_id, email)
        return True
    except Exception as exc:
        logger.error("Resend email error for lead_id=%d: %s", lead_id, exc)
        return False
