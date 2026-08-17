# Customer Insights Platform – AI Customer Intelligence Platform

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Streamlit%201.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-Enterprise-green.svg)]()

**Customer Insights Platform** is an enterprise-grade AI customer intelligence platform designed for high-performance retail analytics, predictive customer modeling, and executive decision-making.

---

## ⚡ Quick Start

### 1. Clone & Install Dependencies
```bash
git clone <repo-url>
cd "customer insights platform AI"
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
cp .env.example .env
```

### 3. Launch Application
```bash
streamlit run app.py
```

---

## 🔐 Default Access Accounts

| Role | Username | Default Password | Permissions |
|------|----------|------------------|-------------|
| **Admin** | `admin` | `Admin@2026` | Full platform access, user management, audit logs, system stats |
| **Analyst** | `analyst` | `analyst123` | Datasets, analytics, ML predictions, and exportable reports |
| **Manager** | `manager` | `manager123` | Executive dashboards, sales performance, category trends |

---

## 📂 Enterprise Project Structure

```text
customer_insights_platform/
│
├── app.py                      # Main entry point: routing & session initialization
├── requirements.txt            # Production Python dependencies
├── .env                        # Local environment configuration
├── .env.example                # Environment variables template
├── README.md                   # Platform documentation
├── validation_test.py          # Core system test & health verification suite
│
├── config/                     # Central Configuration Package
│   ├── __init__.py             # Unified exports
│   ├── settings.py             # Filesystem paths, environment configs, OAuth
│   └── constants.py            # Palettes, taxonomy, roles & permissions, icons
│
├── database/                   # Data Persistence Layer
│   ├── __init__.py
│   ├── db.py                   # High-performance SQLite, indexing & WAL mode
│   └── insightpulse.db         # Auto-generated database file
│
├── services/                   # Business Logic & Analytics Services
│   ├── __init__.py
│   ├── analytics_service.py    # Plotly visualization builders & AI insights engine
│   ├── filter_service.py       # Global sidebar filtering & aggregation
│   ├── ml_service.py           # Machine learning models & prediction pipelines
│   └── report_service.py       # PDF, Excel, and CSV report generators
│
├── pages/                      # Application Page Controllers
│   ├── __init__.py
│   ├── auth.py                 # Multi-tab authentication & login approval queue
│   ├── dashboard.py            # Role-adaptive executive & analyst dashboards
│   ├── upload.py               # Universal CSV/Excel ingestion & auto-cleaner
│   ├── customer_profiles.py    # Customer 360 view, loyalty & AI recommendations
│   ├── segmentation.py         # RFM K-Means clustering with business labels
│   ├── product_analytics.py    # Product & brand revenue velocity
│   ├── sales_analytics.py      # Sales revenue, geography, & payment breakdowns
│   ├── inventory.py            # Stock risk scoring & reorder alert engine
│   ├── machine_learning.py     # Churn classifier, CLV regressor, sales forecast
│   ├── reports_page.py         # Multi-format report builder & data exports
│   ├── admin.py                # User administration, login approval, & audit logs
│   ├── customer_portal.py      # Self-service customer portal & recommendations
│   └── settings.py             # User preferences & dark/light theme toggle
│
├── components/                 # Reusable UI & Visual Atoms
│   ├── __init__.py
│   ├── sidebar.py              # Navigation hierarchy, brand header, role badges
│   ├── topbar.py               # Top bar, notifications & user profile chip
│   └── kpi_cards.py            # Glassmorphism metric cards & AI insight tiles
│
├── utils/                      # Processing & Data Utilities
│   ├── __init__.py
│   ├── data_cleaning.py        # Universal schema standardizer & data cleaner
│   ├── data_generator.py       # Vectorized synthetic retail transaction generator
│   ├── formatters.py           # Currency, percentage, & delta formatters
│   └── preprocessing.py        # RFM feature extraction & time-series resamplers
│
├── assets/                     # Styles & Media
│   └── css/
│       └── theme.css           # Cosmic Aurora Glassmorphism Design System
│
├── uploads/                    # User-uploaded dataset storage
├── exports/                    # Generated PDF/Excel reports storage
├── sample_data/                # Sample datasets for demos
└── models/                     # Serialized ML model cache directory
```

---

## 🌟 Key Platform Capabilities

1. **AI Automated Insights** – Real-time anomaly detection, revenue concentration warnings, and actionable recommendations.
2. **Predictive ML Hub** – Churn probability scoring, 12-month CLV forecasting, and multi-month Ridge revenue regression.
3. **Universal Data Ingestion** – Ingests any CSV or Excel file, automatically standardizes column aliases, handles missing values, and enriches with RFM metrics.
4. **Role-Based Security** – Strict RBAC with admin approval queues for non-admin accounts.
5. **Ultra-Low Latency** – Built-in multi-tier caching (`st.cache_data`, SQLite WAL indexing, vectorized NumPy operations).

---

## 🛠️ Verification & Test Suite

Run the full system validation suite to verify all services and database connectivity:

```bash
python validation_test.py
```
