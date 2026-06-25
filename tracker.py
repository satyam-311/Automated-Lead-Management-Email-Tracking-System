import io
import logging
from flask import Flask, redirect, send_file, jsonify, request
from dotenv import load_dotenv
import os
from database import init_db, mark_email_opened, mark_link_clicked, get_stats

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("tracker")

app = Flask(__name__)

# 1×1 transparent GIF (standard tracking pixel)
_PIXEL = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00"
    b"!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
    b"\x00\x00\x02\x02D\x01\x00;"
)

CLICK_REDIRECT_URL = os.getenv("CLICK_REDIRECT_URL", "https://github.com")


@app.route("/open/<int:lead_id>")
def track_open(lead_id: int):
    try:
        mark_email_opened(lead_id)
        logger.info("Email opened  | lead_id=%-4d  ip=%s", lead_id, request.remote_addr)
    except Exception as exc:
        logger.error("track_open error for lead_id=%d: %s", lead_id, exc)
    return send_file(io.BytesIO(_PIXEL), mimetype="image/gif", max_age=0)


@app.route("/click/<int:lead_id>")
def track_click(lead_id: int):
    try:
        mark_link_clicked(lead_id)
        logger.info("Link clicked  | lead_id=%-4d  ip=%s", lead_id, request.remote_addr)
    except Exception as exc:
        logger.error("track_click error for lead_id=%d: %s", lead_id, exc)
    return redirect(CLICK_REDIRECT_URL)


@app.route("/health")
def health():
    try:
        stats = get_stats()
        return jsonify({"status": "ok", "stats": stats}), 200
    except Exception as exc:
        return jsonify({"status": "error", "detail": str(exc)}), 500


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("TRACKER_PORT", 5000))
    logger.info("Tracker server starting on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
