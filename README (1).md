# USDA Digital Service Effectiveness Dashboard
### Jan–June 2024 | MGMT 389 Group Project

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Place your data files
Create a `data/` folder next to `app.py` and copy all 7 CSVs from Google Drive into it:

```
usda_dashboard/
├── app.py
├── requirements.txt
├── README.md
└── data/
    ├── device-1-2024.csv
    ├── domain-1-2024.csv
    ├── download-1-2024.csv
    ├── language-1-2024.csv
    ├── os-browser-1-2024.csv
    ├── traffic-source-1-2024.csv
    └── windows-browser-1-2024.csv
```

### 3. Run the dashboard
```bash
streamlit run app.py
```

---

## Dashboard Structure

### Layer 1 — System-Wide Descriptive Overview
| Tab | What it shows |
|-----|--------------|
| 📊 System Overview | Total visit KPIs, monthly trend line, device & source sparklines |
| 🌐 Domain & Traffic Sources | Top 86 domains ranked, MoM heatmap, traffic source breakdown, social referral flag |
| 📥 Downloads | Top content by download events, MoM volume bars, content concentration curve |

### Layer 2 — Digital Service Effectiveness Assessment
| Tab | What it shows |
|-----|--------------|
| 📱 Device Analysis | Desktop/mobile/tablet split, mobile share trend with friction threshold line |
| 🔧 Compatibility & OS | OS×browser treemap, Windows version legacy risk, Win×Browser matrix |
| 🌍 Language & Accessibility | Language distribution, English vs non-English, EO 13166 compliance signal table |

---

## Column Reference (confirmed from Colab exploration)

| Dataset | Key columns | Metric |
|---------|------------|--------|
| device | date, device (desktop/mobile/tablet) | visits |
| domain | date, domain (86 hostnames) | visits |
| download | date, page, page_title, event_label | total_events |
| language | date, language (68 codes) | visits |
| os_browser | date, os, browser | visits |
| traffic_source | date, source, has_social_referral | visits |
| windows_browser | date, os_version, browser | visits |

All datasets cover **January 1 – June 30, 2024** (175 unique dates).
