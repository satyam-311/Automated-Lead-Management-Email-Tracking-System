# ─────────────────────────────────────────────────────────────────────────────
#  app.py — LeadFlow: Automated Lead Management & Email Tracking
# ─────────────────────────────────────────────────────────────────────────────
import re
import os
import logging
import html as _html
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database import init_db, insert_lead, get_all_leads, get_stats, mark_email_sent
from email_service import send_lead_email

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page Config (must be the FIRST Streamlit call) ────────────────────────────
st.set_page_config(
    page_title="LeadFlow — Lead Management System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #F1F5F9; }
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: none !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color: #CBD5E1 !important; }
[data-testid="stSidebarContent"] { padding: 1.5rem 1.2rem 1rem 1.2rem; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #DB2777 100%);
    padding: 2.2rem 2.5rem 1.8rem 2.5rem;
    border-radius: 20px;
    margin-bottom: 1.4rem;
    color: white;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute; top: -55%; right: -6%;
    width: 360px; height: 360px;
    background: rgba(255,255,255,0.06); border-radius: 50%;
}
.hero::after {
    content: '';
    position: absolute; bottom: -45%; right: 14%;
    width: 180px; height: 180px;
    background: rgba(255,255,255,0.04); border-radius: 50%;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    padding: 4px 14px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 1px;
    margin-bottom: 0.75rem;
    border: 1px solid rgba(255,255,255,0.28);
}
.hero h1 {
    font-size: 2rem; font-weight: 800;
    margin: 0 0 0.4rem 0; letter-spacing: -0.5px; line-height: 1.15;
}
.hero p { font-size: 0.98rem; opacity: 0.88; margin: 0; max-width: 520px; }
.hero-chips {
    display: flex; gap: 1.6rem; margin-top: 1.3rem; flex-wrap: wrap;
}
.hero-chip { font-size: 0.78rem; opacity: 0.85; display: flex; align-items: center; gap: 5px; }

/* ── KPI Cards ── */
.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 1.2rem 1.35rem 1rem 1.35rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.04);
    border: 1px solid #E2E8F0;
    transition: transform 0.17s ease, box-shadow 0.17s ease;
    margin-bottom: 0.4rem;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 6px 18px rgba(0,0,0,0.09); }
.kpi-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.55rem; }
.kpi-label { font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.7px; }
.kpi-icon  { font-size: 1.35rem; opacity: 0.5; }
.kpi-value { font-size: 1.9rem; font-weight: 800; line-height: 1.1; margin-bottom: 0.18rem; }
.kpi-sub   { font-size: 0.73rem; color: #94A3B8; }

/* ── Badges ── */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.2px;
}
.badge-high   { background: #FEE2E2; color: #DC2626; }
.badge-medium { background: #FEF3C7; color: #D97706; }
.badge-low    { background: #D1FAE5; color: #059669; }
.badge-cat    { background: #EDE9FE; color: #6D28D9; }

/* ── AI Insight box ── */
.ai-box {
    background: linear-gradient(135deg, #EDE9FE 0%, #FCE7F3 100%);
    border: 1px solid #DDD6FE; border-radius: 14px;
    padding: 1.15rem 1.5rem; margin: 0.85rem 0;
}
.ai-box-title {
    font-size: 0.72rem; font-weight: 800; color: #6D28D9;
    text-transform: uppercase; letter-spacing: 0.7px; margin-bottom: 0.55rem;
}
.conf-bg { background: rgba(109,40,217,0.14); border-radius: 20px; height: 7px; overflow: hidden; }
.conf-fill { height: 7px; border-radius: 20px; background: linear-gradient(90deg, #4F46E5, #7C3AED, #DB2777); }

/* ── Section header ── */
.sec-hdr {
    font-size: 1.05rem; font-weight: 700; color: #0F172A;
    margin: 0.2rem 0 0.8rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #E2E8F0;
}

/* ── Cards (generic white) ── */
.w-card {
    background: white; border-radius: 14px; padding: 1.2rem 1.4rem;
    border: 1px solid #E2E8F0; margin-bottom: 0.75rem;
}
.w-card-title {
    font-size: 0.72rem; font-weight: 800; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.7px; margin-bottom: 0.6rem;
}

/* ── Form card ── */
.form-card {
    background: white; border-radius: 16px; padding: 2rem 2rem 1.5rem 2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06); border: 1px solid #E2E8F0;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 3px; background: white; padding: 5px;
    border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1px solid #E2E8F0; margin-bottom: 1.3rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; font-weight: 500 !important;
    font-size: 0.86rem !important; padding: 8px 20px !important;
    color: #64748B !important; transition: all 0.14s !important;
}
.stTabs [aria-selected="true"] {
    background: #4F46E5 !important; color: white !important; font-weight: 600 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 0.87rem !important; letter-spacing: 0.15px !important;
    transition: all 0.17s !important;
}

/* ── Divider ── */
.hr { height: 1px; background: #E2E8F0; margin: 1.3rem 0; }

/* ── Status dot ── */
.dot-green { display:inline-block; width:8px; height:8px; border-radius:50%;
             background:#22C55E; margin-right:6px; }
.dot-red   { display:inline-block; width:8px; height:8px; border-radius:50%;
             background:#EF4444; margin-right:6px; }

/* ── Alerts ── */
.stAlert { border-radius: 10px !important; }

/* ── Footer ── */
.app-footer {
    text-align: center; padding: 1.5rem 0 0.5rem 0;
    font-size: 0.75rem; color: #94A3B8;
    border-top: 1px solid #E2E8F0; margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS & HELPERS
# ─────────────────────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_PHONE_RE = re.compile(r'^[\+\d][\d\s\-\(\)\.]{5,}$')

PRIORITY_COLORS = {
    "High":   ("#FEE2E2", "#DC2626"),
    "Medium": ("#FEF3C7", "#D97706"),
    "Low":    ("#D1FAE5", "#059669"),
}

CAT_ICONS = {
    "AI Automation":    "🤖",
    "Web Development":  "🌐",
    "Mobile App":       "📱",
    "Data Science":     "📊",
    "Digital Marketing":"📣",
    "Design":           "🎨",
    "Cloud & DevOps":   "☁️",
    "General Inquiry":  "💬",
}

KPI_META = [
    ("Total Leads",   "total",   "👥",  "#4F46E5", "All captured leads"),
    ("Emails Sent",   "sent",    "📧",  "#7C3AED", "Automated sends"),
    ("Emails Opened", "opened",  "📬",  "#0EA5E9", "Unique opens tracked"),
    ("Open Rate",     "open_rate","📈", "#10B981", "Opens ÷ sends"),
    ("Link Clicks",   "clicked", "🔗",  "#F59E0B", "CTA link clicks"),
    ("Click Rate",    "click_rate","⚡","#EC4899", "Clicks ÷ sends"),
]


def validate_email(v: str) -> bool:
    return bool(_EMAIL_RE.match(v.strip()))


def validate_phone(v: str) -> bool:
    return len(re.sub(r'[^\d]', '', v)) >= 7 and bool(_PHONE_RE.match(v.strip()))


def _time_ago(ts_str: str) -> str:
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        secs = int((datetime.now() - dt).total_seconds())
        if secs < 60:    return "just now"
        if secs < 3600:  return f"{secs // 60}m ago"
        if secs < 86400: return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"
    except Exception:
        return ts_str[:10] if ts_str else ""


def _chart_base() -> dict:
    return dict(
        paper_bgcolor="white", plot_bgcolor="white", font_family="Inter",
        margin=dict(l=8, r=8, t=44, b=8),
        title_font=dict(size=13, color="#0F172A", family="Inter"),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", tickfont=dict(size=10, color="#64748B")),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", tickfont=dict(size=10, color="#64748B")),
        showlegend=False,
    )


def _empty_fig(title: str, note: str = "No data yet — submit your first lead!") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title, **_chart_base())
    fig.add_annotation(
        text=f"<b>{note}</b>", x=0.5, y=0.5,
        xref="paper", yref="paper", showarrow=False,
        font=dict(size=12, color="#94A3B8", family="Inter"),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  AI LEAD CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────
_CATEGORIES: dict[str, tuple[list[str], str]] = {
    "AI Automation": (
        ["chatbot", "ai", "ml", "automation", "bot", "gpt", "llm",
         "artificial intelligence", "machine learning", "nlp", "neural",
         "deep learning", "openai", "langchain", "natural language",
         "computer vision", "predictive", "recommendation"],
        "High",
    ),
    "Web Development": (
        ["website", "web", "landing page", "ecommerce", "shopify", "wordpress",
         "react", "frontend", "backend", "api", "full stack", "django", "fastapi",
         "next.js", "vue", "angular", "html", "css", "javascript", "portal", "saas"],
        "Medium",
    ),
    "Mobile App": (
        ["app", "mobile", "android", "ios", "flutter", "react native",
         "swift", "kotlin", "cross-platform", "play store", "app store", "pwa"],
        "High",
    ),
    "Data Science": (
        ["data", "analytics", "dashboard", "excel", "report", "visualization",
         "bi", "tableau", "power bi", "sql", "database", "pipeline", "etl",
         "data warehouse", "pandas", "statistics", "forecasting", "data science"],
        "Medium",
    ),
    "Digital Marketing": (
        ["seo", "marketing", "social media", "ads", "campaign", "ppc",
         "email marketing", "content", "influencer", "sem", "google ads",
         "facebook ads", "crm", "lead generation", "funnel", "conversion"],
        "Medium",
    ),
    "Design": (
        ["design", "ui", "ux", "logo", "branding", "figma", "prototype",
         "wireframe", "graphic", "illustration", "photoshop", "brand identity",
         "typography", "mockup", "visual"],
        "Low",
    ),
    "Cloud & DevOps": (
        ["cloud", "aws", "azure", "gcp", "devops", "kubernetes", "docker",
         "deployment", "server", "hosting", "microservices", "lambda",
         "serverless", "terraform", "cicd", "infrastructure"],
        "Medium",
    ),
}


def classify_lead(requirement: str) -> tuple[str, str, int]:
    """Return (category, priority, confidence_pct)."""
    text = requirement.lower()
    best_cat, best_pri, best_hit, best_total = "General Inquiry", "Low", 0, 1

    for cat, (kws, pri) in _CATEGORIES.items():
        hits = sum(1 for k in kws if k in text)
        if hits > best_hit:
            best_cat, best_pri, best_hit, best_total = cat, pri, hits, len(kws)

    if best_hit == 0:
        confidence = 35
    elif best_hit == 1:
        confidence = 62
    else:
        confidence = min(96, 68 + int((best_hit / best_total) * 60))

    return best_cat, best_pri, confidence


# ─────────────────────────────────────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────────────────────────────────────
init_db()


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:0.5rem 0 1.5rem 0; border-bottom:1px solid #1E293B;">
        <div style="font-size:1.5rem; font-weight:800; color:#F8FAFC; letter-spacing:-0.5px;">
            ⚡ LeadFlow
        </div>
        <div style="font-size:0.75rem; color:#64748B; margin-top:3px; font-weight:500;">
            Automated Lead Management
        </div>
    </div>
    """, unsafe_allow_html=True)

    # System status
    smtp_ok = bool(os.getenv("GMAIL_USER") and os.getenv("GMAIL_PASSWORD"))
    tracker_ok = bool(os.getenv("TRACKER_BASE"))

    smtp_html    = '<span class="dot-green"></span><span style="color:#94A3B8;font-size:0.78rem;">SMTP Connected</span>'    if smtp_ok    else '<span class="dot-red"></span><span style="color:#94A3B8;font-size:0.78rem;">SMTP Not Set</span>'
    tracker_html = '<span class="dot-green"></span><span style="color:#94A3B8;font-size:0.78rem;">Tracker Active</span>'  if tracker_ok else '<span class="dot-red"></span><span style="color:#94A3B8;font-size:0.78rem;">Tracker Local</span>'

    st.markdown(f"""
    <div style="padding:1.2rem 0 1rem 0; border-bottom:1px solid #1E293B;">
        <p style="font-size:0.68rem;font-weight:700;color:#475569;text-transform:uppercase;
                  letter-spacing:0.8px;margin:0 0 0.6rem 0;">System Status</p>
        <div style="margin-bottom:5px;">{smtp_html}</div>
        <div>{tracker_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # Quick live stats
    _s = get_stats()
    _open_r  = round(_s["opened"]  / _s["sent"] * 100, 1) if _s["sent"]  else 0.0
    _click_r = round(_s["clicked"] / _s["sent"] * 100, 1) if _s["sent"]  else 0.0

    st.markdown(f"""
    <div style="padding:1.2rem 0 1rem 0; border-bottom:1px solid #1E293B;">
        <p style="font-size:0.68rem;font-weight:700;color:#475569;text-transform:uppercase;
                  letter-spacing:0.8px;margin:0 0 0.7rem 0;">Quick Stats</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div style="background:#1E293B;border-radius:10px;padding:10px 12px;">
                <div style="font-size:1.3rem;font-weight:800;color:#A5B4FC;">{_s['total']}</div>
                <div style="font-size:0.68rem;color:#64748B;font-weight:600;">TOTAL LEADS</div>
            </div>
            <div style="background:#1E293B;border-radius:10px;padding:10px 12px;">
                <div style="font-size:1.3rem;font-weight:800;color:#A5B4FC;">{_s['sent']}</div>
                <div style="font-size:0.68rem;color:#64748B;font-weight:600;">EMAILS SENT</div>
            </div>
            <div style="background:#1E293B;border-radius:10px;padding:10px 12px;">
                <div style="font-size:1.3rem;font-weight:800;color:#34D399;">{_open_r}%</div>
                <div style="font-size:0.68rem;color:#64748B;font-weight:600;">OPEN RATE</div>
            </div>
            <div style="background:#1E293B;border-radius:10px;padding:10px 12px;">
                <div style="font-size:1.3rem;font-weight:800;color:#FBBF24;">{_click_r}%</div>
                <div style="font-size:0.68rem;color:#64748B;font-weight:600;">CLICK RATE</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:1.2rem 0 0 0;">
        <p style="font-size:0.68rem;font-weight:700;color:#475569;text-transform:uppercase;
                  letter-spacing:0.8px;margin:0 0 0.7rem 0;">Navigation</p>
        <p style="font-size:0.8rem;color:#64748B;margin:0 0 4px 0;">📋 &nbsp;Capture Lead</p>
        <p style="font-size:0.8rem;color:#64748B;margin:0 0 4px 0;">📊 &nbsp;Analytics Dashboard</p>
        <p style="font-size:0.8rem;color:#64748B;margin:0 0 0 0;">👥 &nbsp;All Leads</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="position:absolute;bottom:1rem;left:1.2rem;right:1.2rem;">
        <p style="font-size:0.7rem;color:#334155;text-align:center;margin:0;">
            LeadFlow v1.0 &nbsp;·&nbsp; Built with Streamlit
        </p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">⚡ PRODUCTION READY</div>
    <h1>LeadFlow Dashboard</h1>
    <p>Automated lead capture · AI classification · Email tracking · Live analytics</p>
    <div class="hero-chips">
        <span class="hero-chip">🤖 AI Classification</span>
        <span class="hero-chip">📧 Email Tracking</span>
        <span class="hero-chip">📊 Live Analytics</span>
        <span class="hero-chip">🔗 Click Tracking</span>
        <span class="hero-chip">📤 CSV Export</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋  Capture Lead", "📊  Analytics", "👥  All Leads"])


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 1 — LEAD CAPTURE
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    col_form, col_info = st.columns([2, 1], gap="large")

    with col_form:
        st.markdown('<div class="form-card">', unsafe_allow_html=True)
        st.markdown('<p class="sec-hdr">Submit a New Lead</p>', unsafe_allow_html=True)

        with st.form("lead_form", clear_on_submit=True):
            name = st.text_input("Full Name *", placeholder="e.g. John Smith")
            email = st.text_input("Email Address *", placeholder="e.g. john@company.com")
            ph_col, co_col = st.columns(2)
            with ph_col:
                phone = st.text_input("Phone Number *", placeholder="+1 555 000 0000")
            with co_col:
                company = st.text_input("Company", placeholder="Acme Inc. (optional)")
            requirement = st.text_area(
                "Requirement / Message *",
                placeholder="Describe your requirement in detail — the more specific, the better our AI classification.",
                height=130,
            )
            submitted = st.form_submit_button("🚀  Submit Lead", use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown("""
        <div class="ai-box" style="margin-top:0;">
            <div class="ai-box-title">🤖 AI Classification Engine</div>
            <p style="font-size:0.83rem;color:#374151;margin:0;line-height:1.65;">
                Every lead is <strong>instantly classified</strong> by category and priority
                using a keyword-intelligence engine. No external API required.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="w-card">
            <div class="w-card-title">Supported Categories</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
                <span class="badge badge-cat">🤖 AI Automation</span>
                <span class="badge badge-cat">🌐 Web Dev</span>
                <span class="badge badge-cat">📱 Mobile App</span>
                <span class="badge badge-cat">📊 Data Science</span>
                <span class="badge badge-cat">📣 Marketing</span>
                <span class="badge badge-cat">🎨 Design</span>
                <span class="badge badge-cat">☁️ Cloud</span>
                <span class="badge badge-cat">💬 General</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="w-card">
            <div class="w-card-title">How It Works</div>
            <ol style="font-size:0.82rem;color:#374151;margin:0;padding-left:1.1rem;">
                <li style="margin-bottom:6px;">Lead submitted &amp; stored securely in DB</li>
                <li style="margin-bottom:6px;">AI scores category, priority &amp; confidence</li>
                <li style="margin-bottom:6px;">Welcome email sent automatically via SMTP</li>
                <li style="margin-bottom:6px;">Tracking pixel records email open</li>
                <li>CTA link click updates the dashboard</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    # ── Submission handler ───────────────────────────────────────────────────
    if submitted:
        errors: list[str] = []
        if not name.strip():
            errors.append("Full Name is required.")
        if not email.strip():
            errors.append("Email Address is required.")
        elif not validate_email(email):
            errors.append("Enter a valid email address (e.g. john@company.com).")
        if not phone.strip():
            errors.append("Phone Number is required.")
        elif not validate_phone(phone):
            errors.append("Enter a valid phone number (min 7 digits).")
        if not requirement.strip():
            errors.append("Requirement / Message is required.")

        if errors:
            for e in errors:
                st.error(f"❌  {e}")
        else:
            category, priority, confidence = classify_lead(requirement)
            bg, tx = PRIORITY_COLORS.get(priority, ("#E2E8F0", "#475569"))
            cat_icon = CAT_ICONS.get(category, "💬")

            st.markdown(f"""
            <div class="ai-box">
                <div class="ai-box-title">🤖 AI Classification Result</div>
                <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:flex-start;">
                    <div>
                        <p style="font-size:0.69rem;color:#6B7280;font-weight:700;margin:0 0 4px 0;">CATEGORY</p>
                        <span class="badge badge-cat">{cat_icon} {category}</span>
                    </div>
                    <div>
                        <p style="font-size:0.69rem;color:#6B7280;font-weight:700;margin:0 0 4px 0;">PRIORITY</p>
                        <span class="badge" style="background:{bg};color:{tx};">{priority}</span>
                    </div>
                    <div style="flex:1;min-width:130px;">
                        <p style="font-size:0.69rem;color:#6B7280;font-weight:700;margin:0 0 5px 0;">
                            CONFIDENCE — {confidence}%
                        </p>
                        <div class="conf-bg">
                            <div class="conf-fill" style="width:{confidence}%;"></div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            lead_id = insert_lead(
                name.strip(), email.strip(), phone.strip(),
                company.strip(), requirement.strip(),
                category, priority, confidence,
            )
            logger.info("Lead #%d created — %s | %s | %s", lead_id, category, priority, email)

            with st.spinner("📧  Sending welcome email…"):
                success = send_lead_email(
                    lead_id, name.strip(), email.strip(), requirement.strip()
                )

            if success:
                mark_email_sent(lead_id)
                st.success(f"✅  Lead **#{lead_id}** saved and welcome email delivered to **{email}**!")
            else:
                st.warning(
                    f"⚠️  Lead **#{lead_id}** saved. Email failed — check SMTP credentials in `.env`."
                )


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 2 — ANALYTICS DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    _rc, _ = st.columns([1, 8])
    with _rc:
        if st.button("🔄  Refresh", use_container_width=True):
            st.rerun()

    stats   = get_stats()
    total, sent, opened, clicked = (
        stats["total"], stats["sent"], stats["opened"], stats["clicked"]
    )
    open_rate  = round(opened  / sent * 100, 1) if sent else 0.0
    click_rate = round(clicked / sent * 100, 1) if sent else 0.0

    kpi_values = {
        "total": total, "sent": sent, "opened": opened,
        "open_rate": f"{open_rate}%", "clicked": clicked, "click_rate": f"{click_rate}%",
    }

    # ── KPI Cards ────────────────────────────────────────────────────────────
    kpi_cols = st.columns(6)
    for col, (label, key, icon, color, sub) in zip(kpi_cols, KPI_META):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-top:3px solid {color};">
                <div class="kpi-row">
                    <span class="kpi-label">{label}</span>
                    <span class="kpi-icon">{icon}</span>
                </div>
                <div class="kpi-value" style="color:{color};">{kpi_values[key]}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    leads_raw = get_all_leads()
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    if not leads_raw:
        st.info("📊  Submit your first lead to unlock live analytics and charts.")
    else:
        df = pd.DataFrame(leads_raw)
        df["submitted_at"] = pd.to_datetime(df["submitted_at"])
        df["date"] = df["submitted_at"].dt.date

        # Row 1
        st.markdown('<p class="sec-hdr">📈  Trends Over Time</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)

        with c1:  # Leads Over Time
            daily = df.groupby("date").size().reset_index(name="Leads")
            fig = px.area(daily, x="date", y="Leads",
                          color_discrete_sequence=["#4F46E5"], template="plotly_white")
            fig.update_traces(fillcolor="rgba(79,70,229,0.10)", line_color="#4F46E5", line_width=2.2)
            fig.update_layout(title="Leads Submitted Over Time", **_chart_base())
            st.plotly_chart(fig, use_container_width=True)

        with c2:  # Email Opens Over Time
            opens_df = df[df["email_opened"] == 1]
            if not opens_df.empty:
                d_op = opens_df.groupby("date").size().reset_index(name="Opens")
                fig = px.bar(d_op, x="date", y="Opens",
                             color_discrete_sequence=["#0EA5E9"], template="plotly_white")
                fig.update_layout(title="Email Opens Over Time", **_chart_base())
            else:
                fig = _empty_fig("Email Opens Over Time", "No opens recorded yet")
            st.plotly_chart(fig, use_container_width=True)

        # Row 2
        st.markdown('<p class="sec-hdr">🗂️  Breakdown</p>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)

        with c3:  # Category donut
            cat_df = df["category"].value_counts().reset_index()
            cat_df.columns = ["Category", "Count"]
            fig = px.pie(cat_df, names="Category", values="Count", hole=0.48,
                         color_discrete_sequence=px.colors.qualitative.Vivid,
                         template="plotly_white")
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              textfont_size=10.5)
            fig.update_layout(
                title="Lead Categories",
                paper_bgcolor="white", font_family="Inter",
                margin=dict(l=8, r=8, t=44, b=8),
                title_font=dict(size=13, color="#0F172A"),
                legend=dict(orientation="v", x=1.0, y=0.5, font=dict(size=10)),
                showlegend=True,
            )
            st.plotly_chart(fig, use_container_width=True)

        with c4:  # Priority horizontal bar
            pri_df = df["priority"].value_counts().reset_index()
            pri_df.columns = ["Priority", "Count"]
            order = ["High", "Medium", "Low"]
            pri_df["Priority"] = pd.Categorical(
                pri_df["Priority"], categories=order, ordered=True
            )
            pri_df = pri_df.sort_values("Priority")
            fig = px.bar(
                pri_df, x="Count", y="Priority", orientation="h",
                color="Priority",
                color_discrete_map={"High": "#DC2626", "Medium": "#D97706", "Low": "#059669"},
                template="plotly_white",
            )
            fig.update_layout(title="Priority Breakdown", **_chart_base())
            st.plotly_chart(fig, use_container_width=True)

        # Row 3
        st.markdown('<p class="sec-hdr">🔗  Engagement</p>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)

        with c5:  # Link Clicks Over Time
            clicks_df = df[df["link_clicked"] == 1]
            if not clicks_df.empty:
                d_cl = clicks_df.groupby("date").size().reset_index(name="Clicks")
                fig = px.bar(d_cl, x="date", y="Clicks",
                             color_discrete_sequence=["#F59E0B"], template="plotly_white")
                fig.update_layout(title="Link Clicks Over Time", **_chart_base())
            else:
                fig = _empty_fig("Link Clicks Over Time", "No link clicks yet")
            st.plotly_chart(fig, use_container_width=True)

        with c6:  # Open Rate Trend
            d_rate = df.groupby("date").agg(
                sent=("email_sent", "sum"),
                opened=("email_opened", "sum"),
            ).reset_index()
            d_rate = d_rate[d_rate["sent"] > 0].copy()
            d_rate["open_rate"] = (d_rate["opened"] / d_rate["sent"] * 100).round(1)
            if not d_rate.empty:
                fig = px.line(d_rate, x="date", y="open_rate",
                              color_discrete_sequence=["#10B981"],
                              markers=True, template="plotly_white")
                fig.update_traces(line_width=2.5, marker_size=7)
                fig.update_layout(title="Open Rate Trend (%)", **_chart_base())
                fig.update_yaxes(range=[0, 105], ticksuffix="%")
            else:
                fig = _empty_fig("Open Rate Trend (%)", "Not enough data yet")
            st.plotly_chart(fig, use_container_width=True)

        # ── Recent Activity Feed ─────────────────────────────────────────────
        st.markdown('<p class="sec-hdr">🕐  Recent Activity</p>', unsafe_allow_html=True)
        recent = leads_raw[:5]
        _AVATAR_COLORS = ["#4F46E5", "#7C3AED", "#0EA5E9", "#10B981", "#F59E0B"]
        feed_items = []
        for i, lead in enumerate(recent):
            parts = lead["name"].strip().split()
            initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
            av_col = _AVATAR_COLORS[i % len(_AVATAR_COLORS)]
            bg_pri, tx_pri = PRIORITY_COLORS.get(lead.get("priority", "Low"), ("#E2E8F0", "#475569"))
            icon = CAT_ICONS.get(lead.get("category", "General Inquiry"), "💬")
            ago = _time_ago(lead.get("submitted_at", ""))
            status = "✅" if lead.get("email_sent") else "⏳"
            safe_name     = _html.escape(str(lead.get("name", "")))
            safe_email    = _html.escape(str(lead.get("email", "")))
            safe_category = _html.escape(str(lead.get("category", "?")))
            safe_priority = _html.escape(str(lead.get("priority", "?")))
            feed_items.append(
                f'<div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #F1F5F9;">'
                f'<div style="width:38px;height:38px;border-radius:50%;background:{av_col};display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:12px;flex-shrink:0;">{initials}</div>'
                f'<div style="flex:1;min-width:0;">'
                f'<p style="margin:0;font-size:0.84rem;font-weight:600;color:#0F172A;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{safe_name} &mdash; {icon} {safe_category}</p>'
                f'<p style="margin:2px 0 0;font-size:0.73rem;color:#94A3B8;">{ago} &nbsp;&middot;&nbsp; {safe_email} &nbsp;{status}</p>'
                f'</div>'
                f'<span style="background:{bg_pri};color:{tx_pri};padding:3px 10px;border-radius:20px;font-size:0.68rem;font-weight:700;white-space:nowrap;flex-shrink:0;">{safe_priority}</span>'
                f'</div>'
            )

        if feed_items:
            feed_content = "".join(feed_items)
        else:
            feed_content = '<p style="color:#94A3B8;font-size:0.85rem;margin:0;">No activity yet.</p>'

        st.markdown(
            f'<div class="w-card" style="padding:1.2rem 1.5rem;">'
            f'<div class="w-card-title">Last {len(recent)} Leads</div>'
            f'{feed_content}'
            f'</div>',
            unsafe_allow_html=True,
        )


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 3 — ALL LEADS
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    leads_raw = get_all_leads()

    if not leads_raw:
        st.info("👥  No leads yet. Go to **Capture Lead** to add your first one!")
    else:
        df_all = pd.DataFrame(leads_raw)

        # ── Filters ──────────────────────────────────────────────────────────
        s_col, cat_col, pri_col = st.columns([3, 1.5, 1.5])
        with s_col:
            search = st.text_input(
                "search", label_visibility="collapsed",
                placeholder="🔍  Search by name, email, or company…"
            )
        with cat_col:
            cats = ["All"] + sorted(df_all["category"].dropna().unique().tolist())
            cat_filter = st.selectbox("cat", cats, label_visibility="collapsed")
        with pri_col:
            pri_filter = st.selectbox(
                "pri", ["All", "High", "Medium", "Low"], label_visibility="collapsed"
            )

        filtered = df_all.copy()
        if search:
            m = (
                filtered["name"].str.contains(search, case=False, na=False)
                | filtered["email"].str.contains(search, case=False, na=False)
                | filtered["company"].fillna("").str.contains(search, case=False, na=False)
            )
            filtered = filtered[m]
        if cat_filter != "All":
            filtered = filtered[filtered["category"] == cat_filter]
        if pri_filter != "All":
            filtered = filtered[filtered["priority"] == pri_filter]

        st.markdown(
            f'<p style="font-size:0.8rem;color:#64748B;margin:0.3rem 0 0.6rem 0;">'
            f'Showing <strong>{len(filtered)}</strong> of <strong>{len(df_all)}</strong> leads</p>',
            unsafe_allow_html=True,
        )

        # ── Format for display ────────────────────────────────────────────────
        disp = filtered.copy()
        disp["email_sent"]   = disp["email_sent"].map({1: "✅ Sent",   0: "⏳ Pending"})
        disp["email_opened"] = disp["email_opened"].map({1: "✅ Opened", 0: "—"})
        disp["link_clicked"] = disp["link_clicked"].map({1: "✅ Clicked", 0: "—"})

        col_order = [
            "id", "name", "email", "phone", "company",
            "category", "priority", "confidence",
            "email_sent", "email_opened", "link_clicked",
            "submitted_at", "requirement",
        ]
        disp = disp[[c for c in col_order if c in disp.columns]]

        st.dataframe(
            disp,
            use_container_width=True,
            hide_index=True,
            height=460,
            column_config={
                "id":           st.column_config.NumberColumn("ID",         width="small"),
                "name":         st.column_config.TextColumn("Name",         width="medium"),
                "email":        st.column_config.TextColumn("Email",        width="medium"),
                "phone":        st.column_config.TextColumn("Phone",        width="small"),
                "company":      st.column_config.TextColumn("Company",      width="medium"),
                "category":     st.column_config.TextColumn("Category",     width="medium"),
                "priority":     st.column_config.TextColumn("Priority",     width="small"),
                "confidence":   st.column_config.ProgressColumn("AI Confidence", min_value=0, max_value=100, width="medium"),
                "email_sent":   st.column_config.TextColumn("Email",        width="small"),
                "email_opened": st.column_config.TextColumn("Opened",       width="small"),
                "link_clicked": st.column_config.TextColumn("Clicked",      width="small"),
                "submitted_at": st.column_config.TextColumn("Submitted",    width="medium"),
                "requirement":  st.column_config.TextColumn("Requirement",  width="large"),
            },
        )

        # ── Export ────────────────────────────────────────────────────────────
        exp_col, _ = st.columns([1, 4])
        with exp_col:
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️  Export CSV",
                data=csv_bytes,
                file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-footer">
    ⚡ <strong>LeadFlow</strong> &nbsp;·&nbsp;
    Built with Streamlit, Flask, SQLite &amp; Plotly &nbsp;·&nbsp;
    Automated Lead Management &amp; Email Tracking System
</div>
""", unsafe_allow_html=True)
