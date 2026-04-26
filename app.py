"""
USDA Digital Service Effectiveness Dashboard
=============================================
Jan–June 2024 | System-Wide Analysis

Layer 1: System-Wide Descriptive Overview
Layer 2: Digital Service Effectiveness Assessment

Data folder: place all 7 CSVs in ./data/ relative to this file.
Run: streamlit run app.py
"""

import os
import re
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path

# ─── Constants ────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"

GREEN      = "#2E7D32"
GREEN_L    = "#81C784"
GREEN_XL   = "#E8F5E9"
AMBER      = "#F9A825"
AMBER_L    = "#FFE082"
CORAL      = "#D32F2F"
CORAL_L    = "#EF9A9A"
BLUE       = "#1565C0"
BLUE_L     = "#90CAF9"
GRAY       = "#546E7A"
GRAY_L     = "#ECEFF1"

MONTH_ORDER = ["January","February","March","April","May","June"]

LEGACY_WINDOWS = ["7", "8", "8.1", "Vista", "XP"]
LEGACY_BROWSERS = ["Internet Explorer", "IE"]

# ─── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="USDA Web Analytics 2024",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #F1F8E9; }
.kpi-card {
    background: white; border-radius: 10px; padding: 14px 18px;
    border: 1px solid #E0E0E0; margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.kpi-label { font-size: 11px; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #1a1a1a; margin: 4px 0 2px 0; }
.kpi-sub   { font-size: 12px; color: #888; }
.sec-hdr {
    font-size: 16px; font-weight: 700; color: #1a1a1a;
    border-left: 4px solid #2E7D32; padding-left: 10px;
    margin: 1.4rem 0 0.6rem 0;
}
.layer-pill {
    display: inline-block; border-radius: 20px;
    padding: 3px 12px; font-size: 11px; font-weight: 700;
    margin-bottom: 8px; letter-spacing: .3px;
}
.l1 { background: #E8F5E9; color: #2E7D32; }
.l2 { background: #FFF8E1; color: #E65100; }
.friction-high { background: #FFEBEE; border-left: 4px solid #D32F2F; padding: 10px 14px; border-radius: 4px; margin: 6px 0; }
.friction-med  { background: #FFF8E1; border-left: 4px solid #F9A825; padding: 10px 14px; border-radius: 4px; margin: 6px 0; }
.friction-ok   { background: #E8F5E9; border-left: 4px solid #2E7D32; padding: 10px 14px; border-radius: 4px; margin: 6px 0; }
</style>
""", unsafe_allow_html=True)

# ─── Data loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_all():
    files = {
        "device":          "device-1-2024.csv",
        "domain":          "domain-1-2024.csv",
        "download":        "download-1-2024.csv",
        "language":        "language-1-2024.csv",
        "os_browser":      "os-browser-1-2024.csv",
        "traffic_source":  "traffic-source-1-2024.csv",
        "windows_browser": "windows-browser-1-2024.csv",
    }
    dfs = {}
    for key, fname in files.items():
        path = DATA_DIR / fname
        if path.exists():
            df = pd.read_csv(path)
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["month"] = df["date"].dt.month
            df["month_name"] = df["date"].dt.strftime("%B")
            df["week"] = df["date"].dt.isocalendar().week.astype(int)
            dfs[key] = df
    return dfs

dfs = load_all()

def ok(key):
    return key in dfs and not dfs[key].empty

def section(title):
    st.markdown(f'<div class="sec-hdr">{title}</div>', unsafe_allow_html=True)

def kpi(col, label, value, sub="", color="#2E7D32"):
    col.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value" style="color:{color}">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def layer_badge(layer):
    cls = "l1" if layer == 1 else "l2"
    label = "Layer 1 — Descriptive Overview" if layer == 1 else "Layer 2 — Effectiveness Assessment"
    st.markdown(f'<span class="layer-pill {cls}">{label}</span>', unsafe_allow_html=True)

def plotly_defaults(fig, h=380):
    fig.update_layout(
        height=h, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=30, b=10, l=10, r=10),
        font=dict(family="sans-serif", size=12),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F0F0F0", zeroline=False)
    return fig

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌾 USDA Analytics")
    st.markdown("**Jan–June 2024**")
    st.divider()

    loaded = len(dfs)
    if loaded == 7:
        st.success(f"All 7 datasets loaded", icon="✅")
    elif loaded > 0:
        st.warning(f"{loaded}/7 datasets loaded", icon="⚠️")
    else:
        st.error("No data found in ./data/", icon="🚨")
        st.stop()

    st.markdown("#### Global Filters")

    all_months = ["All"] + MONTH_ORDER
    sel_month = st.selectbox("Month", all_months, index=0)

    top_n = st.slider("Top N items", 5, 25, 10)

    st.divider()
    st.caption("Data: USDA / GSA Digital Analytics Program")
    st.caption("Period: January 1 – June 30, 2024")

def filter_month(df):
    if sel_month == "All":
        return df
    return df[df["month_name"] == sel_month]

# ─── Header ───────────────────────────────────────────────────────────────────
c1, c2 = st.columns([1, 11])
c1.markdown("<div style='font-size:52px;padding-top:4px'>🌾</div>", unsafe_allow_html=True)
c2.markdown("## USDA Digital Service Effectiveness Dashboard")
c2.markdown("System-Wide Web Analytics | January – June 2024 | Department of Agriculture")
st.divider()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_overview, tab_traffic, tab_downloads, tab_devices, tab_compat, tab_language = st.tabs([
    "📊 System Overview",
    "🌐 Domain & Traffic Sources",
    "📥 Downloads",
    "📱 Device Analysis",
    "🔧 Compatibility & OS",
    "🌍 Language & Accessibility",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — SYSTEM OVERVIEW
# ════════════════════════════════════════════════════════════════════════════

with tab_overview:
    layer_badge(1)
    st.markdown("*What is happening across USDA's web presence, and how has it changed over time?*")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    section("System-Wide KPIs")
    k1, k2, k3, k4, k5 = st.columns(5)

    if ok("domain"):
        df_d = filter_month(dfs["domain"])
        total_visits = df_d["visits"].sum()
        n_domains = df_d["domain"].nunique()
        kpi(k1, "Total Visits", f"{total_visits/1e6:.2f}M",
            f"Across {n_domains} domains", GREEN)
        top_dom = df_d.groupby("domain")["visits"].sum().idxmax()
        kpi(k2, "Top Domain", top_dom.replace("https://","").replace("http://","")[:22],
            "by total visits", BLUE)

    if ok("device"):
        df_dv = filter_month(dfs["device"])
        total_dv = df_dv["visits"].sum()
        mob = df_dv[df_dv["device"]=="mobile"]["visits"].sum()
        mob_pct = mob/total_dv*100 if total_dv > 0 else 0
        col = CORAL if mob_pct > 40 else AMBER if mob_pct > 28 else GREEN
        kpi(k3, "Mobile Share", f"{mob_pct:.1f}%", "of all visits", col)

    if ok("language"):
        df_l = filter_month(dfs["language"])
        total_l = df_l["visits"].sum()
        non_en = df_l[~df_l["language"].str.lower().str.startswith("en")]["visits"].sum()
        non_en_pct = non_en/total_l*100 if total_l > 0 else 0
        kpi(k4, "Non-English Traffic", f"{non_en_pct:.1f}%", "of language sessions", AMBER)

    if ok("traffic_source"):
        df_ts = filter_month(dfs["traffic_source"])
        social = df_ts[df_ts["has_social_referral"]=="Yes"]["visits"].sum()
        total_ts = df_ts["visits"].sum()
        soc_pct = social/total_ts*100 if total_ts > 0 else 0
        kpi(k5, "Social Referral", f"{soc_pct:.1f}%", "of traffic", BLUE)

    # ── Monthly trend: total visits across all domains ─────────────────────
    section("Monthly Visit Trend — All USDA Domains")

    if ok("domain"):
        df_trend = dfs["domain"].copy()
        monthly = df_trend.groupby(["month","month_name"])["visits"].sum().reset_index()
        monthly = monthly.sort_values("month")
        monthly["month_name"] = pd.Categorical(monthly["month_name"],
                                                categories=MONTH_ORDER, ordered=True)
        monthly = monthly.sort_values("month_name")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["month_name"], y=monthly["visits"],
            mode="lines+markers",
            line=dict(color=GREEN, width=3),
            marker=dict(size=8, color=GREEN),
            fill="tozeroy", fillcolor="rgba(46,125,50,0.08)",
            hovertemplate="<b>%{x}</b><br>Visits: %{y:,.0f}<extra></extra>",
            name="Total visits"
        ))
        fig.update_layout(
            yaxis_title="Total Visits", xaxis_title="",
            height=320, plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(t=20, b=10),
            yaxis=dict(tickformat=",.0f", gridcolor="#F0F0F0"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Multi-metric overview sparklines ──────────────────────────────────
    section("Monthly Breakdown by Dimension")
    col_a, col_b = st.columns(2)

    with col_a:
        if ok("device"):
            df_dv2 = dfs["device"].copy()
            dv_monthly = df_dv2.groupby(["month","month_name","device"])["visits"].sum().reset_index()
            dv_monthly = dv_monthly[dv_monthly["month_name"].isin(MONTH_ORDER)]
            dv_monthly["month_name"] = pd.Categorical(dv_monthly["month_name"],
                                                       categories=MONTH_ORDER, ordered=True)
            dv_monthly = dv_monthly.sort_values("month_name")
            fig = px.line(dv_monthly, x="month_name", y="visits", color="device",
                          color_discrete_map={"desktop": GREEN, "mobile": AMBER, "tablet": BLUE},
                          markers=True,
                          labels={"visits":"Visits","month_name":"","device":"Device"},
                          title="Device Type — Monthly Visits")
            plotly_defaults(fig, 320)
            fig.update_layout(yaxis=dict(tickformat=",.0f", gridcolor="#F0F0F0"))
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if ok("traffic_source"):
            df_ts2 = dfs["traffic_source"].copy()
            # Classify sources into broad buckets
            def classify_source(s):
                s = str(s).lower()
                if s in ["(direct)", "direct"]:
                    return "Direct"
                elif "google" in s or "bing" in s or "yahoo" in s or "duckduckgo" in s:
                    return "Search"
                elif s in ["govdelivery","email"] or "email" in s:
                    return "Email / GovDelivery"
                else:
                    return "Referral / Other"
            df_ts2["source_group"] = df_ts2["source"].apply(classify_source)
            ts_monthly = df_ts2.groupby(["month","month_name","source_group"])["visits"].sum().reset_index()
            ts_monthly = ts_monthly[ts_monthly["month_name"].isin(MONTH_ORDER)]
            ts_monthly["month_name"] = pd.Categorical(ts_monthly["month_name"],
                                                       categories=MONTH_ORDER, ordered=True)
            ts_monthly = ts_monthly.sort_values("month_name")
            colors = {"Search": GREEN, "Direct": BLUE, "Email / GovDelivery": AMBER, "Referral / Other": GRAY}
            fig = px.line(ts_monthly, x="month_name", y="visits",
                          color="source_group",
                          color_discrete_map=colors,
                          markers=True,
                          labels={"visits":"Visits","month_name":"","source_group":"Source"},
                          title="Traffic Source Groups — Monthly Visits")
            plotly_defaults(fig, 320)
            fig.update_layout(yaxis=dict(tickformat=",.0f", gridcolor="#F0F0F0"))
            st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOMAIN & TRAFFIC SOURCES
# ════════════════════════════════════════════════════════════════════════════

with tab_traffic:
    layer_badge(1)
    st.markdown("*Which sub-agency sites are growing, declining, or stagnant?*")

    if ok("domain"):
        df_dom = filter_month(dfs["domain"])

        # ── Top domains bar ────────────────────────────────────────────────
        section("Top USDA Domains by Visits")

        domain_agg = (df_dom.groupby("domain")["visits"]
                      .sum().reset_index()
                      .sort_values("visits", ascending=False)
                      .head(top_n))
        domain_agg["label"] = domain_agg["domain"].str.replace("https://","").str.replace("http://","")

        fig = px.bar(
            domain_agg.sort_values("visits"),
            x="visits", y="label", orientation="h",
            color="visits",
            color_continuous_scale=[[0, GREEN_XL],[0.5, GREEN_L],[1, GREEN]],
            labels={"visits":"Total Visits","label":"Domain"},
        )
        plotly_defaults(fig, max(380, top_n * 34))
        fig.update_layout(coloraxis_showscale=False,
                          yaxis=dict(tickfont=dict(size=11)))
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Visits: %{x:,.0f}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

        # ── Monthly domain heatmap ─────────────────────────────────────────
        section("Domain Traffic Heatmap — Month over Month")
        st.caption("Intensity = total visits. Darker = more traffic. Reveals seasonal surges and declining domains.")

        top_domains = (dfs["domain"].groupby("domain")["visits"]
                       .sum().nlargest(15).index.tolist())
        df_hm = (dfs["domain"][dfs["domain"]["domain"].isin(top_domains)]
                 .groupby(["month_name","domain"])["visits"]
                 .sum().reset_index())
        df_hm["month_name"] = pd.Categorical(df_hm["month_name"],
                                               categories=MONTH_ORDER, ordered=True)
        df_pivot = df_hm.pivot(index="domain", columns="month_name", values="visits").fillna(0)
        df_pivot.index = df_pivot.index.str.replace("https://","").str.replace("http://","")

        fig = px.imshow(
            df_pivot,
            color_continuous_scale=[[0,"white"],[0.3, GREEN_L],[1, GREEN]],
            aspect="auto",
            labels=dict(color="Visits"),
            text_auto=False,
        )
        fig.update_layout(height=460, margin=dict(t=20, b=10),
                          xaxis_title="", yaxis_title="",
                          yaxis=dict(tickfont=dict(size=10)),
                          coloraxis_colorbar=dict(title="Visits", tickformat=",.0f"))
        st.plotly_chart(fig, use_container_width=True)

    # ── Traffic sources ────────────────────────────────────────────────────
    if ok("traffic_source"):
        df_ts = filter_month(dfs["traffic_source"])

        section("Traffic Source Analysis")
        col_src1, col_src2 = st.columns(2)

        with col_src1:
            st.markdown("**Top Traffic Sources (raw)**")
            src_agg = (df_ts.groupby("source")["visits"]
                       .sum().reset_index()
                       .sort_values("visits", ascending=False)
                       .head(top_n))
            fig = px.bar(
                src_agg.sort_values("visits"),
                x="visits", y="source", orientation="h",
                color="visits",
                color_continuous_scale=[[0,"#E3F2FD"],[1, BLUE]],
                labels={"visits":"Visits","source":"Source"},
            )
            plotly_defaults(fig, max(360, top_n * 32))
            fig.update_layout(coloraxis_showscale=False,
                              yaxis=dict(tickfont=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)

        with col_src2:
            st.markdown("**Source Category Breakdown**")
            df_ts2 = filter_month(dfs["traffic_source"]).copy()
            def classify(s):
                s = str(s).lower()
                if s in ["(direct)", "direct"]: return "Direct"
                if any(x in s for x in ["google","bing","yahoo","duckduckgo","search"]): return "Organic Search"
                if "govdelivery" in s or "email" in s: return "Email / GovDelivery"
                if df_ts2.loc[df_ts2["source"]==s, "has_social_referral"].eq("Yes").any(): return "Social"
                return "Referral / Other"
            df_ts2["cat"] = df_ts2["source"].apply(classify)
            cat_agg = df_ts2.groupby("cat")["visits"].sum().reset_index()
            fig = px.pie(cat_agg, values="visits", names="cat",
                         hole=0.44,
                         color="cat",
                         color_discrete_map={
                             "Organic Search": GREEN,
                             "Direct": BLUE,
                             "Email / GovDelivery": AMBER,
                             "Social": CORAL,
                             "Referral / Other": GRAY,
                         })
            fig.update_layout(height=360, margin=dict(t=20,b=20))
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

        # Social referral flag
        section("Social Referral Flag")
        social_pct = df_ts[df_ts["has_social_referral"]=="Yes"]["visits"].sum() / df_ts["visits"].sum() * 100
        if social_pct < 5:
            st.markdown(f'<div class="friction-high">⚠️ <b>Social referral is only {social_pct:.1f}% of traffic</b> — USDA content is not being discovered through social channels. This indicates a discoverability gap that may be limiting reach to younger demographic segments.</div>', unsafe_allow_html=True)
        elif social_pct < 15:
            st.markdown(f'<div class="friction-med">📊 Social referral is {social_pct:.1f}% of traffic — modest but below optimal for a public-service agency.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="friction-ok">✅ Social referral at {social_pct:.1f}% — healthy.</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — DOWNLOADS
# ════════════════════════════════════════════════════════════════════════════

with tab_downloads:
    layer_badge(1)
    st.markdown("*Which content is highest-demand? Are there seasonal surges or policy-driven spikes?*")

    if ok("download"):
        df_dl = filter_month(dfs["download"])

        section("Top Downloaded Content")
        col_dl1, col_dl2 = st.columns([3, 2])

        with col_dl1:
            page_agg = (df_dl.groupby("page_title")["total_events"]
                        .sum().reset_index()
                        .sort_values("total_events", ascending=False)
                        .head(top_n))
            page_agg["short_title"] = page_agg["page_title"].str[:55]
            fig = px.bar(
                page_agg.sort_values("total_events"),
                x="total_events", y="short_title", orientation="h",
                color="total_events",
                color_continuous_scale=[[0,"#E3F2FD"],[1, BLUE]],
                labels={"total_events":"Download Events","short_title":"Page Title"},
            )
            plotly_defaults(fig, max(400, top_n * 36))
            fig.update_layout(coloraxis_showscale=False,
                              yaxis=dict(tickfont=dict(size=10)))
            fig.update_traces(hovertemplate="<b>%{y}</b><br>Downloads: %{x:,.0f}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)

        with col_dl2:
            st.markdown("**Top Download Pages (URLs)**")
            url_agg = (df_dl.groupby("page")["total_events"]
                       .sum().reset_index()
                       .sort_values("total_events", ascending=False)
                       .head(top_n))
            url_agg["domain_short"] = url_agg["page"].apply(
                lambda x: x.split("/")[0] if "/" in str(x) else str(x)[:30]
            )
            domain_dl = url_agg.groupby("domain_short")["total_events"].sum().reset_index()
            fig = px.pie(domain_dl, values="total_events", names="domain_short",
                         hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Greens_r)
            fig.update_layout(height=380, margin=dict(t=20,b=20))
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              textfont=dict(size=10))
            st.plotly_chart(fig, use_container_width=True)

        # ── Monthly download trend ─────────────────────────────────────────
        section("Download Volume — Month over Month")
        st.caption("Spikes indicate seasonal program activity or policy-driven surges (e.g., SNAP enrollment periods, WIC updates).")

        dl_monthly = (dfs["download"]
                      .groupby(["month","month_name"])["total_events"]
                      .sum().reset_index()
                      .sort_values("month"))
        dl_monthly["month_name"] = pd.Categorical(dl_monthly["month_name"],
                                                   categories=MONTH_ORDER, ordered=True)
        dl_monthly = dl_monthly.sort_values("month_name")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dl_monthly["month_name"], y=dl_monthly["total_events"],
            marker_color=BLUE,
            hovertemplate="<b>%{x}</b><br>Downloads: %{y:,.0f}<extra></extra>",
            name="Downloads"
        ))
        fig.update_layout(
            height=300, plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(title="Total Download Events", tickformat=",.0f", gridcolor="#F0F0F0"),
            xaxis_title="",
            margin=dict(t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Download concentration analysis ───────────────────────────────
        section("Content Concentration Analysis")
        st.caption("High concentration means most downloads come from very few pages — signals narrow access points and potential bottlenecks.")

        top5_pct = (page_agg.head(5)["total_events"].sum() /
                    df_dl["total_events"].sum() * 100)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if top5_pct > 60:
                st.markdown(f'<div class="friction-high">⚠️ <b>Top 5 pages account for {top5_pct:.0f}% of all downloads</b> — extremely concentrated. A small number of files are driving nearly all download activity, which may mask accessibility gaps for less-promoted content.</div>', unsafe_allow_html=True)
            elif top5_pct > 40:
                st.markdown(f'<div class="friction-med">📊 Top 5 pages = {top5_pct:.0f}% of downloads — moderately concentrated.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="friction-ok">✅ Top 5 pages = {top5_pct:.0f}% of downloads — well distributed.</div>', unsafe_allow_html=True)

        with col_c2:
            # Lorenz-style: cumulative share
            all_pages = (df_dl.groupby("page_title")["total_events"]
                         .sum().sort_values(ascending=False).reset_index())
            all_pages["cum_pct"] = all_pages["total_events"].cumsum() / all_pages["total_events"].sum() * 100
            all_pages["rank_pct"] = (np.arange(1, len(all_pages)+1)) / len(all_pages) * 100

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=all_pages["rank_pct"], y=all_pages["cum_pct"],
                mode="lines", line=dict(color=BLUE, width=2),
                name="Actual", fill="tozeroy",
                fillcolor="rgba(21,101,192,0.08)"
            ))
            fig.add_trace(go.Scatter(
                x=[0,100], y=[0,100],
                mode="lines", line=dict(color=GRAY, dash="dash", width=1),
                name="Perfect equality"
            ))
            fig.update_layout(
                height=260, plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(t=20,b=10),
                xaxis=dict(title="% of pages (ranked)", gridcolor="#F0F0F0"),
                yaxis=dict(title="Cumulative % of downloads", gridcolor="#F0F0F0"),
                title="Download Concentration Curve",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Download data not available.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — DEVICE ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

with tab_devices:
    layer_badge(2)
    st.markdown("*Which device segments show friction? Are mobile users underserved?*")

    if ok("device"):
        df_dv = filter_month(dfs["device"])
        total_dv = df_dv["visits"].sum()

        # ── KPI row ───────────────────────────────────────────────────────
        section("Device KPIs")
        d1, d2, d3 = st.columns(3)

        desktop_pct = df_dv[df_dv["device"]=="desktop"]["visits"].sum() / total_dv * 100
        mobile_pct  = df_dv[df_dv["device"]=="mobile"]["visits"].sum()  / total_dv * 100
        tablet_pct  = df_dv[df_dv["device"]=="tablet"]["visits"].sum()  / total_dv * 100

        mob_color = CORAL if mobile_pct > 40 else AMBER if mobile_pct > 28 else GREEN
        kpi(d1, "Desktop Share", f"{desktop_pct:.1f}%", "of total visits", GREEN)
        kpi(d2, "Mobile Share",  f"{mobile_pct:.1f}%",  "⚠ High = friction risk", mob_color)
        kpi(d3, "Tablet Share",  f"{tablet_pct:.1f}%",  "of total visits", BLUE)

        col_dv1, col_dv2 = st.columns(2)

        with col_dv1:
            section("Device Mix")
            dev_agg = df_dv.groupby("device")["visits"].sum().reset_index()
            fig = px.pie(dev_agg, values="visits", names="device",
                         color="device",
                         color_discrete_map={"desktop": GREEN, "mobile": AMBER, "tablet": BLUE},
                         hole=0.45)
            fig.update_layout(height=340, margin=dict(t=20,b=20))
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              textfont=dict(size=13))
            st.plotly_chart(fig, use_container_width=True)

        with col_dv2:
            section("Monthly Device Trend")
            dv_mo = (dfs["device"]
                     .groupby(["month","month_name","device"])["visits"]
                     .sum().reset_index())
            dv_mo["month_name"] = pd.Categorical(dv_mo["month_name"],
                                                  categories=MONTH_ORDER, ordered=True)
            dv_mo = dv_mo.sort_values("month_name")
            fig = px.bar(dv_mo, x="month_name", y="visits", color="device",
                         color_discrete_map={"desktop": GREEN, "mobile": AMBER, "tablet": BLUE},
                         barmode="stack",
                         labels={"visits":"Visits","month_name":"","device":"Device"})
            plotly_defaults(fig, 340)
            fig.update_layout(yaxis=dict(tickformat=",.0f", gridcolor="#F0F0F0"))
            st.plotly_chart(fig, use_container_width=True)

        # ── Mobile share trend line ────────────────────────────────────────
        section("Mobile Share Trend — Is it Rising?")
        dv_mob_trend = (dfs["device"]
                        .groupby(["month","month_name","device"])["visits"]
                        .sum().reset_index())
        dv_mob_trend["month_name"] = pd.Categorical(dv_mob_trend["month_name"],
                                                     categories=MONTH_ORDER, ordered=True)
        dv_total_mo = dv_mob_trend.groupby("month_name")["visits"].sum().reset_index()
        dv_total_mo.columns = ["month_name","total"]
        dv_mob_only = dv_mob_trend[dv_mob_trend["device"]=="mobile"]
        dv_mob_pct = dv_mob_only.merge(dv_total_mo, on="month_name")
        dv_mob_pct["mobile_%"] = dv_mob_pct["visits"] / dv_mob_pct["total"] * 100
        dv_mob_pct = dv_mob_pct.sort_values("month_name")

        fig = go.Figure()
        fig.add_hline(y=40, line_dash="dot", line_color=CORAL,
                      annotation_text="40% friction threshold", annotation_position="top right")
        fig.add_trace(go.Scatter(
            x=dv_mob_pct["month_name"], y=dv_mob_pct["mobile_%"],
            mode="lines+markers+text",
            line=dict(color=AMBER, width=3),
            marker=dict(size=9),
            text=dv_mob_pct["mobile_%"].round(1).astype(str)+"%",
            textposition="top center",
            hovertemplate="<b>%{x}</b><br>Mobile: %{y:.1f}%<extra></extra>",
        ))
        fig.update_layout(
            height=300, plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(title="Mobile Share (%)", range=[0,60], gridcolor="#F0F0F0"),
            xaxis_title="",
            margin=dict(t=30, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Friction assessment ────────────────────────────────────────────
        section("Device Friction Assessment")
        if mobile_pct > 40:
            st.markdown(f'<div class="friction-high">🔴 <b>High Mobile Friction Risk ({mobile_pct:.1f}% mobile)</b><br>More than 40% of USDA web traffic is from mobile devices. Pages not optimized for mobile represent a direct barrier to service access for a significant portion of users — including rural populations who may rely on mobile as their primary internet device.</div>', unsafe_allow_html=True)
        elif mobile_pct > 28:
            st.markdown(f'<div class="friction-med">🟡 <b>Moderate Mobile Traffic ({mobile_pct:.1f}% mobile)</b><br>Monitor responsive design compliance on high-traffic pages. Consider auditing top 10 domains for mobile usability.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="friction-ok">🟢 Mobile share ({mobile_pct:.1f}%) is within a manageable range, though continued monitoring is recommended.</div>', unsafe_allow_html=True)
    else:
        st.info("Device data not available.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — COMPATIBILITY & OS
# ════════════════════════════════════════════════════════════════════════════

with tab_compat:
    layer_badge(2)
    st.markdown("*Where are legacy OS/browser combinations creating compatibility friction?*")

    col_os1, col_os2 = st.columns(2)

    # ── OS + Browser treemap ───────────────────────────────────────────────
    with col_os1:
        section("OS + Browser Compatibility Map")
        st.caption("Size = visits. Hover for detail. Legacy combinations appear in lower-traffic cells.")
        if ok("os_browser"):
            df_ob = filter_month(dfs["os_browser"])
            ob_agg = df_ob.groupby(["os","browser"])["visits"].sum().reset_index()
            ob_agg = ob_agg[ob_agg["visits"] > 0]
            fig = px.treemap(
                ob_agg,
                path=["os","browser"],
                values="visits",
                color="visits",
                color_continuous_scale=[[0,"#FFF9C4"],[0.4, GREEN_L],[1, GREEN]],
                title="OS × Browser Traffic Distribution",
            )
            fig.update_layout(height=440, margin=dict(t=40,b=10))
            fig.update_traces(hovertemplate="<b>%{label}</b><br>Visits: %{value:,.0f}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("OS+Browser data not available.")

    # ── OS share bar ──────────────────────────────────────────────────────
    with col_os2:
        section("Operating System Share")
        if ok("os_browser"):
            df_ob2 = filter_month(dfs["os_browser"])
            os_agg = df_ob2.groupby("os")["visits"].sum().reset_index().sort_values("visits", ascending=False)
            total_os = os_agg["visits"].sum()
            os_agg["pct"] = os_agg["visits"] / total_os * 100

            fig = px.bar(
                os_agg.sort_values("visits"),
                x="visits", y="os", orientation="h",
                color="pct",
                color_continuous_scale=[[0, GREEN_XL],[1, GREEN]],
                labels={"visits":"Visits","os":"OS","pct":"Share %"},
                text=os_agg.sort_values("visits")["pct"].apply(lambda x: f"{x:.1f}%"),
            )
            fig.update_traces(textposition="outside")
            plotly_defaults(fig, 380)
            fig.update_layout(coloraxis_showscale=False,
                              yaxis=dict(tickfont=dict(size=11)))
            st.plotly_chart(fig, use_container_width=True)

            # Monthly OS trend
            section("OS Trend Month-over-Month")
            ob_mo = (dfs["os_browser"]
                     .groupby(["month","month_name","os"])["visits"]
                     .sum().reset_index())
            ob_mo["month_name"] = pd.Categorical(ob_mo["month_name"],
                                                  categories=MONTH_ORDER, ordered=True)
            ob_mo = ob_mo.sort_values("month_name")
            top_os = dfs["os_browser"].groupby("os")["visits"].sum().nlargest(5).index.tolist()
            ob_mo_top = ob_mo[ob_mo["os"].isin(top_os)]
            fig = px.line(ob_mo_top, x="month_name", y="visits", color="os",
                          markers=True,
                          labels={"visits":"Visits","month_name":"","os":"OS"})
            plotly_defaults(fig, 300)
            fig.update_layout(yaxis=dict(tickformat=",.0f", gridcolor="#F0F0F0"))
            st.plotly_chart(fig, use_container_width=True)

    # ── Windows version + browser ─────────────────────────────────────────
    section("Windows Version & Browser — Legacy Risk Assessment")
    st.caption("USDA's rural and low-income user base is more likely to be on older infrastructure. Legacy Windows versions signal compatibility and security risk.")

    if ok("windows_browser"):
        df_wb = filter_month(dfs["windows_browser"])

        col_w1, col_w2 = st.columns(2)

        with col_w1:
            win_agg = df_wb.groupby("os_version")["visits"].sum().reset_index().sort_values("visits", ascending=False)
            total_win = win_agg["visits"].sum()
            win_agg["pct"] = win_agg["visits"] / total_win * 100
            win_agg["is_legacy"] = win_agg["os_version"].astype(str).isin(LEGACY_WINDOWS)
            legacy_pct = win_agg[win_agg["is_legacy"]]["pct"].sum()

            colors = [CORAL if v else GREEN for v in win_agg.sort_values("visits")["is_legacy"]]
            fig = px.bar(
                win_agg.sort_values("visits"),
                x="visits", y="os_version", orientation="h",
                text=win_agg.sort_values("visits")["pct"].apply(lambda x: f"{x:.1f}%"),
                labels={"visits":"Visits","os_version":"Windows Version"},
                title="Windows Version Traffic Share",
            )
            fig.update_traces(textposition="outside",
                              marker_color=colors)
            plotly_defaults(fig, 300)
            st.plotly_chart(fig, use_container_width=True)

            if legacy_pct > 10:
                st.markdown(f'<div class="friction-high">🔴 <b>{legacy_pct:.1f}% of Windows traffic uses legacy versions (7/8/8.1)</b> — these users face compatibility risks and may not receive supported security patches, indicating infrastructure gap in USDA\'s user base.</div>', unsafe_allow_html=True)
            elif legacy_pct > 3:
                st.markdown(f'<div class="friction-med">🟡 Legacy Windows versions account for {legacy_pct:.1f}% of traffic — monitor for compatibility issues.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="friction-ok">🟢 Legacy Windows share ({legacy_pct:.1f}%) is low.</div>', unsafe_allow_html=True)

        with col_w2:
            br_agg = df_wb.groupby("browser")["visits"].sum().reset_index().sort_values("visits", ascending=False)
            fig = px.bar(
                br_agg.sort_values("visits"),
                x="visits", y="browser", orientation="h",
                color="visits",
                color_continuous_scale=[[0,"#E3F2FD"],[1, BLUE]],
                labels={"visits":"Visits","browser":"Browser"},
                title="Browser Share (Windows users)",
            )
            plotly_defaults(fig, 300)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

            # Windows version × browser heatmap
            section("Windows Version × Browser Matrix")
            wb_matrix = df_wb.groupby(["os_version","browser"])["visits"].sum().reset_index()
            wb_pivot = wb_matrix.pivot(index="os_version", columns="browser", values="visits").fillna(0)
            fig = px.imshow(
                wb_pivot,
                color_continuous_scale=[[0,"white"],[0.3, AMBER_L],[1, CORAL]],
                aspect="auto",
                text_auto=False,
                labels=dict(color="Visits"),
                title="Visit volume by Windows ver. × Browser",
            )
            fig.update_layout(height=300, margin=dict(t=40,b=10),
                              xaxis_title="Browser", yaxis_title="Windows Version",
                              coloraxis_colorbar=dict(tickformat=",.0f"))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Windows+Browser data not available.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 6 — LANGUAGE & ACCESSIBILITY
# ════════════════════════════════════════════════════════════════════════════

with tab_language:
    layer_badge(2)
    st.markdown("*Are non-English-speaking populations being reached and served equitably?*")

    if ok("language"):
        df_lang = filter_month(dfs["language"])

        # Normalize language codes to readable names
        LANG_NAMES = {
            "en-us": "English (US)", "en-gb": "English (UK)", "en": "English",
            "es": "Spanish", "es-us": "Spanish (US)", "es-419": "Spanish (LatAm)",
            "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
            "fr": "French", "pt": "Portuguese", "pt-br": "Portuguese (Brazil)",
            "vi": "Vietnamese", "ko": "Korean", "tl": "Tagalog",
            "ru": "Russian", "ar": "Arabic", "de": "German",
            "it": "Italian", "ja": "Japanese", "pl": "Polish",
            "ht": "Haitian Creole",
        }
        df_lang["lang_name"] = df_lang["language"].str.lower().map(
            lambda x: LANG_NAMES.get(x, x)
        )
        df_lang["is_english"] = df_lang["language"].str.lower().str.startswith("en")

        total_lang = df_lang["visits"].sum()
        non_en_visits = df_lang[~df_lang["is_english"]]["visits"].sum()
        non_en_pct = non_en_visits / total_lang * 100 if total_lang > 0 else 0
        n_lang = df_lang["language"].nunique()

        # ── KPIs ──────────────────────────────────────────────────────────
        section("Language Access KPIs")
        lk1, lk2, lk3 = st.columns(3)
        kpi(lk1, "Non-English Traffic", f"{non_en_pct:.1f}%",
            "EO 13166 compliance signal",
            CORAL if non_en_pct > 15 else AMBER if non_en_pct > 8 else GREEN)
        kpi(lk2, "Languages Detected", f"{n_lang}",
            "unique browser language codes", BLUE)
        top_non_en = (df_lang[~df_lang["is_english"]]
                      .groupby("lang_name")["visits"]
                      .sum().idxmax() if non_en_visits > 0 else "—")
        kpi(lk3, "Top Non-English Language", top_non_en, "by visits", AMBER)

        col_l1, col_l2 = st.columns(2)

        with col_l1:
            section("Top Languages by Visits")
            lang_agg = (df_lang.groupby("lang_name")["visits"]
                        .sum().reset_index()
                        .sort_values("visits", ascending=False)
                        .head(top_n))
            lang_agg["color"] = lang_agg["lang_name"].apply(
                lambda x: GREEN if "English" in x else AMBER
            )
            fig = px.bar(
                lang_agg.sort_values("visits"),
                x="visits", y="lang_name", orientation="h",
                color="lang_name",
                color_discrete_sequence=[GREEN if "English" in n else AMBER
                                          for n in lang_agg.sort_values("visits")["lang_name"]],
                labels={"visits":"Visits","lang_name":"Language"},
            )
            plotly_defaults(fig, max(400, top_n * 32))
            fig.update_layout(showlegend=False, coloraxis_showscale=False,
                              yaxis=dict(tickfont=dict(size=11)))
            fig.update_traces(hovertemplate="<b>%{y}</b><br>Visits: %{x:,.0f}<extra></extra>",
                              marker_color=[GREEN if "English" in n else AMBER
                                           for n in lang_agg.sort_values("visits")["lang_name"]])
            st.plotly_chart(fig, use_container_width=True)

        with col_l2:
            section("English vs. Non-English Share")
            en_total    = df_lang[df_lang["is_english"]]["visits"].sum()
            non_en_total = df_lang[~df_lang["is_english"]]["visits"].sum()
            fig = px.pie(
                pd.DataFrame({"Group": ["English","Non-English"],
                               "Visits": [en_total, non_en_total]}),
                values="Visits", names="Group", hole=0.45,
                color="Group",
                color_discrete_map={"English": GREEN, "Non-English": CORAL}
            )
            fig.update_layout(height=320, margin=dict(t=20,b=20))
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              textfont=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)

            # Non-English breakdown
            non_en_agg = (df_lang[~df_lang["is_english"]]
                          .groupby("lang_name")["visits"]
                          .sum().reset_index()
                          .sort_values("visits", ascending=False)
                          .head(8))
            fig2 = px.pie(non_en_agg, values="visits", names="lang_name",
                          hole=0.35,
                          color_discrete_sequence=px.colors.sequential.Oranges_r,
                          title="Non-English language breakdown")
            fig2.update_layout(height=300, margin=dict(t=40,b=10))
            fig2.update_traces(textposition="inside", textinfo="percent+label",
                               textfont=dict(size=10))
            st.plotly_chart(fig2, use_container_width=True)

        # ── Monthly language trend ─────────────────────────────────────────
        section("Non-English Traffic Trend — Monthly")
        lang_mo = (dfs["language"]
                   .groupby(["month","month_name","is_english"])["visits"]
                   .sum().reset_index())
        lang_mo["group"] = lang_mo["is_english"].map({True:"English", False:"Non-English"})
        lang_mo["month_name"] = pd.Categorical(lang_mo["month_name"],
                                                categories=MONTH_ORDER, ordered=True)
        lang_mo = lang_mo.sort_values("month_name")

        # Calculate non-English % each month
        total_mo = lang_mo.groupby("month_name")["visits"].sum().reset_index()
        total_mo.columns = ["month_name","total"]
        non_en_mo = lang_mo[lang_mo["group"]=="Non-English"].merge(total_mo, on="month_name")
        non_en_mo["non_en_%"] = non_en_mo["visits"] / non_en_mo["total"] * 100
        non_en_mo = non_en_mo.sort_values("month_name")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=lang_mo[lang_mo["group"]=="English"]["month_name"],
            y=lang_mo[lang_mo["group"]=="English"]["visits"],
            name="English", marker_color=GREEN
        ))
        fig.add_trace(go.Bar(
            x=lang_mo[lang_mo["group"]=="Non-English"]["month_name"],
            y=lang_mo[lang_mo["group"]=="Non-English"]["visits"],
            name="Non-English", marker_color=CORAL
        ))
        fig.add_trace(go.Scatter(
            x=non_en_mo["month_name"],
            y=non_en_mo["non_en_%"],
            mode="lines+markers",
            name="Non-English %",
            yaxis="y2",
            line=dict(color=AMBER, width=2, dash="dot"),
            marker=dict(size=7),
        ))
        fig.update_layout(
            barmode="stack", height=360,
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(t=20, b=10),
            yaxis=dict(title="Visits", tickformat=",.0f", gridcolor="#F0F0F0"),
            yaxis2=dict(title="Non-English %", overlaying="y", side="right",
                        range=[0,30], tickformat=".1f"),
            legend=dict(orientation="h", y=1.08),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── EO 13166 Compliance Signal ─────────────────────────────────────
        section("Executive Order 13166 Compliance Signal")
        st.caption("EO 13166 requires federal agencies to provide meaningful access to LEP (Limited English Proficiency) individuals.")

        top_non_en_langs = (df_lang[~df_lang["is_english"]]
                            .groupby("lang_name")["visits"]
                            .sum().nlargest(5))

        if non_en_pct > 15:
            st.markdown(f'<div class="friction-high">🔴 <b>Non-English traffic is {non_en_pct:.1f}%</b> — this exceeds the typical threshold for triggering EO 13166 translation obligations. The top non-English language groups driving this traffic are: <b>{", ".join(top_non_en_langs.index[:3])}</b>. USDA should audit whether these user segments have access to translated content for high-demand pages.</div>', unsafe_allow_html=True)
        elif non_en_pct > 8:
            st.markdown(f'<div class="friction-med">🟡 Non-English traffic is {non_en_pct:.1f}% — approaching levels that warrant EO 13166 review. Top non-English languages: <b>{", ".join(top_non_en_langs.index[:3])}</b>.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="friction-ok">🟢 Non-English traffic is {non_en_pct:.1f}% — below critical thresholds, but monitor for growth trends in Spanish and other key LEP languages.</div>', unsafe_allow_html=True)

        # Table of non-English languages with EO relevance
        non_en_table = (df_lang[~df_lang["is_english"]]
                        .groupby("lang_name")["visits"]
                        .sum().reset_index()
                        .sort_values("visits", ascending=False)
                        .head(10))
        non_en_table["% of total traffic"] = (non_en_table["visits"] / total_lang * 100).round(2)
        non_en_table["EO 13166 relevance"] = non_en_table["% of total traffic"].apply(
            lambda x: "🔴 High" if x > 2 else "🟡 Medium" if x > 0.5 else "🟢 Low"
        )
        non_en_table.columns = ["Language","Visits","% of Total Traffic","EO 13166 Relevance"]
        st.dataframe(non_en_table.reset_index(drop=True), use_container_width=True, hide_index=True)

    else:
        st.info("Language data not available.")
