# ⚡ LeadFlow — Automated Lead Management & Email Tracking System

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?style=flat-square&logo=streamlit)
![Flask](https://img.shields.io/badge/Flask-3.0-black?style=flat-square&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?style=flat-square&logo=sqlite)
![Plotly](https://img.shields.io/badge/Plotly-5.18-purple?style=flat-square&logo=plotly)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

> A production-ready CRM-style system that captures leads, auto-classifies them with AI, sends tracked HTML emails, and visualises engagement in a real-time dashboard.

---

## 📌 Project Overview

LeadFlow is a full-stack automation tool built for agencies, freelancers, and small businesses to:

- **Capture** inbound leads through a clean web form
- **Classify** them instantly using a rule-based AI engine (no API key required)
- **Send** personalised HTML emails automatically via Gmail SMTP
- **Track** email opens (tracking pixel) and link clicks (redirect tracking)
- **Visualise** all metrics in a live Streamlit dashboard with Plotly charts
- **Export** lead data to CSV for CRM imports

---

## ✨ Features

| Feature | Description |
|---|---|
| 📋 Lead Capture Form | Validated form with email regex & phone checks |
| 🤖 AI Classification | Auto-assigns category, priority & confidence score |
| 📧 Email Automation | Sends branded HTML welcome emails via Gmail SMTP |
| 📬 Open Tracking | 1×1 GIF pixel tracks when emails are opened |
| 🔗 Click Tracking | Redirect-based link tracking updates the DB live |
| 📊 Analytics Dashboard | 6 KPI cards + 5 interactive Plotly charts |
| 🕐 Activity Feed | Live feed of the 5 most recent leads |
| 🔍 Search & Filter | Filter leads by name, email, category, or priority |
| 📤 CSV Export | One-click export of filtered leads |
| 🌐 Deployment Ready | `render.yaml` included for one-click Render deploy |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        BROWSER / USER                            │
└─────────────┬────────────────────────────────┬───────────────────┘
              │  visits dashboard               │  opens email / clicks link
              ▼                                 ▼
┌─────────────────────────┐       ┌─────────────────────────────────┐
│   Streamlit Dashboard   │       │     Flask Tracker Server        │
│       app.py            │       │         tracker.py              │
│   Port: 8501 (Render)   │       │   /open/<id>  → pixel GIF       │
│                         │       │   /click/<id> → redirect        │
│  ┌─────────────────┐    │       │   /health     → status JSON     │
│  │  Lead Capture   │    │       └──────────────┬──────────────────┘
│  │  AI Classifier  │    │                      │
│  │  Analytics      │    │                      │ writes
│  │  All Leads      │    │                      │
│  └────────┬────────┘    │                      │
└───────────┼─────────────┘                      │
            │ reads / writes                      │
            └──────────────────┬─────────────────┘
                               ▼
              ┌────────────────────────────────┐
              │    SQLite Database             │
              │       leads.db                 │
              │                                │
              │  id · name · email · phone     │
              │  company · requirement         │
              │  submitted_at · category       │
              │  priority · confidence         │
              │  email_sent · email_opened     │
              │  link_clicked                  │
              └────────────────────────────────┘
                               │
                               │ SMTP
                               ▼
              ┌────────────────────────────────┐
              │      Gmail SMTP Server         │
              │  Sends branded HTML email with │
              │  tracking pixel + tracked link │
              └────────────────────────────────┘
```

---

## 🗄️ Database Design

```sql
CREATE TABLE leads (
    id            INTEGER  PRIMARY KEY AUTOINCREMENT,
    name          TEXT     NOT NULL,
    email         TEXT     NOT NULL,
    phone         TEXT     NOT NULL,
    company       TEXT,
    requirement   TEXT,
    submitted_at  TEXT,                        -- "YYYY-MM-DD HH:MM:SS"
    email_sent    INTEGER  DEFAULT 0,          -- 0 / 1
    email_opened  INTEGER  DEFAULT 0,          -- set by tracking pixel
    link_clicked  INTEGER  DEFAULT 0,          -- set by redirect tracker
    category      TEXT     DEFAULT 'General Inquiry',
    priority      TEXT     DEFAULT 'Medium',
    confidence    INTEGER  DEFAULT 0           -- AI confidence 0-100
);
```

See `supabase_schema.sql` to migrate to PostgreSQL / Supabase.

---

## 📧 Email Tracking Flow

```
1. Lead submits form
        ↓
2. insert_lead() → SQLite
        ↓
3. send_lead_email() builds HTML with:
   • Tracking pixel  →  <img src="TRACKER_BASE/open/<id>" />
   • Tracked CTA     →  <a href="TRACKER_BASE/click/<id>">
        ↓
4. Gmail SMTP sends email
        ↓
5. Lead opens email
   → Email client loads pixel
   → GET /open/<id>  →  mark_email_opened()  →  DB updated
        ↓
6. Lead clicks CTA button
   → GET /click/<id>  →  mark_link_clicked()  →  redirect to site
        ↓
7. Dashboard refreshes  →  open_rate & click_rate update live
```

---

## 🤖 AI Classification Flow

```
Input: requirement text
        ↓
Lowercase + keyword scan across 7 category banks:
  • AI Automation    (18 keywords)  → Priority: High
  • Web Development  (20 keywords)  → Priority: Medium
  • Mobile App       (12 keywords)  → Priority: High
  • Data Science     (19 keywords)  → Priority: Medium
  • Digital Marketing(16 keywords)  → Priority: Medium
  • Design           (15 keywords)  → Priority: Low
  • Cloud & DevOps   (16 keywords)  → Priority: Medium
        ↓
Count keyword hits per category → pick highest score
        ↓
Confidence scoring:
  0 hits  → 35%  (General Inquiry)
  1 hit   → 62%
  2+ hits → min(96%, 68% + hits/total × 60%)
        ↓
Output: (category, priority, confidence_pct)
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.10+
- Gmail account with **App Password** enabled

### 1. Clone & install

```bash
git clone https://github.com/yourusername/leadflow.git
cd leadflow
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Gmail credentials and tracker URL
```

### 3. Run the tracker server (terminal 1)

```bash
python tracker.py
# Running on http://localhost:5000
```

### 4. Run the Streamlit dashboard (terminal 2)

```bash
streamlit run app.py
# Opens http://localhost:8501
```

---

## ☁️ Deploy on Render (Free Tier)

This repo includes a `render.yaml` that defines **two services**:

| Service | Type | Purpose |
|---|---|---|
| `leadflow-dashboard` | Web Service | Streamlit UI |
| `leadflow-tracker` | Web Service | Flask tracker (pixel + clicks) |

### Steps

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New Blueprint Instance**.
3. Connect your GitHub repo → Render reads `render.yaml` automatically.
4. Set the environment variables below in each service.
5. After `leadflow-tracker` deploys, **copy its URL** and paste it as `TRACKER_BASE` in `leadflow-dashboard`'s env vars.
6. Redeploy `leadflow-dashboard`.

> **Note on SQLite:** Render free tier uses ephemeral storage — data resets on redeploy. For persistent storage, use Render PostgreSQL (free) or Supabase. See `supabase_schema.sql`.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GMAIL_USER` | ✅ | Your Gmail address |
| `GMAIL_PASSWORD` | ✅ | Gmail App Password (16 chars) |
| `TRACKER_BASE` | ✅ | Base URL of the tracker server |
| `CLICK_REDIRECT_URL` | ⬜ | Where users land after clicking the email CTA |
| `TRACKER_PORT` | ⬜ | Tracker server port (default: 5000) |
| `DATABASE_URL` | ⬜ | PostgreSQL URL (Supabase / Render PG) |

---

## 📸 Screenshots

> _Run the app locally and take screenshots — place them in a `/screenshots` folder._

| Screen | Description |
|---|---|
| `screenshots/capture.png` | Lead capture form with AI result |
| `screenshots/analytics.png` | KPI cards + Plotly charts |
| `screenshots/leads-table.png` | Searchable leads table with export |
| `screenshots/email.png` | Branded HTML email template |

---

## 🔮 Future Improvements

- [ ] PostgreSQL / Supabase integration (persistent data)
- [ ] Role-based access (admin login)
- [ ] Webhook support (Slack / Zapier notifications on new lead)
- [ ] Lead scoring with OpenAI / Gemini API
- [ ] Bulk email campaigns with open/click tracking
- [ ] PDF analytics report download
- [ ] WhatsApp notification via Twilio
- [ ] Lead pipeline board (Kanban view)
- [ ] Mobile-responsive companion app

---

## 📁 Project Structure

```
leadflow/
├── app.py               # Streamlit dashboard (main UI)
├── tracker.py           # Flask tracking server (pixel + clicks)
├── database.py          # SQLite data layer
├── email_service.py     # Gmail SMTP + HTML email builder
├── requirements.txt     # Python dependencies
├── render.yaml          # Render.com deployment config
├── supabase_schema.sql  # PostgreSQL schema (optional)
├── .env.example         # Environment variable template
├── .gitignore           # Excludes .env, leads.db, venv/
└── README.md            # This file
```

---

## 👤 Author

**Satyam Mishra**
- Built as a technical assessment project demonstrating full-stack automation, email tracking, and AI classification.

---

## 📄 License

MIT License — see `LICENSE` for details.
