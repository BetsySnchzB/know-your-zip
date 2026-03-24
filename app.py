import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from services.chatbot import ask_about_zip

# ------------------
# Page config
# ------------------
st.set_page_config(page_title="Know Your Zip", page_icon="📍", layout="wide")

# ------------------
# Custom CSS
# ------------------
st.markdown("""
<style>
    .stApp { background-color: #f5f5f0; }
    .header-bar {
        background-color: #2cbdac;
        padding: 1rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .header-bar h1 { color: white; margin: 0; font-size: 1.8rem; font-weight: 600; }
    .header-bar p { color: #a8eeea; margin: 0; font-size: 0.9rem; }
    .kpi-card {
        background: white;
        border-radius: 8px;
        padding: 1.2rem;
        border-left: 4px solid #2cbdac;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .kpi-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #1a1a1a; line-height: 1.1; }
    .kpi-sub { font-size: 0.8rem; color: #aaa; margin-top: 2px; }
    .section-header {
        background: white;
        border-radius: 8px 8px 0 0;
        padding: 0.8rem 1.2rem;
        border-bottom: 2px solid #2cbdac;
        font-weight: 600;
        color: #2cbdac;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-high { background: #e8f5e9; color: #2e7d32; padding: 4px 14px; border-radius: 99px; font-size: 0.85rem; font-weight: 600; }
    .badge-medium { background: #fff8e1; color: #f57f17; padding: 4px 14px; border-radius: 99px; font-size: 0.85rem; font-weight: 600; }
    .badge-low { background: #ffebee; color: #c62828; padding: 4px 14px; border-radius: 99px; font-size: 0.85rem; font-weight: 600; }
    .chat-response {
        background: #e8faf8;
        border-left: 4px solid #2cbdac;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        font-size: 0.95rem;
        color: #1a1a1a;
        line-height: 1.6;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# ------------------
# Load data
# ------------------
# Run pipeline if data doesn't exist
from pathlib import Path
if not Path("data/processed/zip_summary.csv").exists():
    from ingestion.process_data import run_pipeline
    run_pipeline()

@st.cache_data
def load_data():
    zip_summary = pd.read_csv("data/processed/zip_summary.csv")
    facilities_points = pd.read_csv("data/processed/facilities_points.csv")
    zip_summary["ZIP"] = zip_summary["ZIP"].astype(str).str[:5].str.zfill(5)
    facilities_points["ZIP"] = facilities_points["ZIP"].astype(str).str[:5].str.zfill(5)
    return zip_summary, facilities_points

zip_summary, facilities_points = load_data()

# ------------------
# Header
# ------------------
st.markdown("""
<div class="header-bar">
    <h1>Know Your Zip</h1>
    <p>Explore zip code insights powered by live Census data and AI</p>
</div>
""", unsafe_allow_html=True)

# ------------------
# Sidebar
# ------------------
st.sidebar.header("Search")
user_zip = st.sidebar.text_input("Enter ZIP Code", placeholder="e.g., 33186")
st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown("Data sourced from U.S. Census Bureau ACS 2022 and Miami-Dade County open data.")

# ------------------
# Filter data
# ------------------
zip_key = (user_zip or "").strip()[:5]
zip_data = zip_summary[zip_summary["ZIP"] == zip_key]
fac_data = facilities_points[facilities_points["ZIP"] == zip_key]

def safe_get(df, col, default=None):
    return df[col].iloc[0] if (not df.empty and col in df.columns) else default

# ------------------
# Landing state
# ------------------
if not user_zip:
    st.info("Enter a ZIP code in the sidebar to explore your neighborhood!")
    st.markdown("### Try these Miami-Dade ZIP codes:")
    cols = st.columns(4)
    for i, z in enumerate(["33186", "33101", "33139", "33155"]):
        cols[i].code(z)
    st.stop()

if zip_data.empty:
    st.error(f"ZIP code {zip_key} not found. Please try another.")
    st.stop()

# ------------------
# Get values
# ------------------
pop       = safe_get(zip_data, "Population")
income    = safe_get(zip_data, "INCOME")
score     = safe_get(zip_data, "FACILITY_SCORE_WEIGHTED")
rating    = safe_get(zip_data, "WEIGHTED_RATING")
med_age   = safe_get(zip_data, "MEDIAN_AGE")
bachelors = safe_get(zip_data, "BACHELORS_DEGREE")

# ------------------
# ZIP title + badge
# ------------------
badge_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(str(rating), "badge-medium")
st.markdown(f"""
<div style="display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem;">
    <h2 style="margin:0; font-size:2rem;">ZIP {zip_key}</h2>
    <span class="{badge_class}">{rating} rated</span>
</div>
""", unsafe_allow_html=True)

# ------------------
# KPI Row
# ------------------
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Population</div>
        <div class="kpi-value">{int(pop):,}</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Median income</div>
        <div class="kpi-value">${income:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Median age</div>
        <div class="kpi-value">{med_age}</div>
        <div class="kpi-sub">years</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">College educated</div>
        <div class="kpi-value">{int(bachelors):,}</div>
        <div class="kpi-sub">bachelor's degrees</div>
    </div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Facility score</div>
        <div class="kpi-value">{int(score)}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------
# Map
# ------------------
st.markdown('<div class="section-header">Map</div>', unsafe_allow_html=True)
if not fac_data.empty and {"latitude", "longitude"}.issubset(fac_data.columns):
    m = fac_data.dropna(subset=["latitude", "longitude"])
    if not m.empty:
        view = pdk.ViewState(latitude=float(m["latitude"].mean()), longitude=float(m["longitude"].mean()), zoom=12)
        layer = pdk.Layer("ScatterplotLayer", data=m, get_position='[longitude, latitude]',
                          get_radius=80, get_fill_color=[26, 122, 110, 180], pickable=True)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view,
                                  tooltip={"text": "{NAME}\n{FACILITY_TYPE}"}))

st.markdown("<br>", unsafe_allow_html=True)

# ------------------
# Charts
# ------------------
st.markdown('<div class="section-header">Demographics & Economics</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    fig = px.histogram(zip_summary[zip_summary["INCOME"] > 0], x="INCOME", nbins=40,
                       title="Income distribution — all ZIPs", color_discrete_sequence=["#2cbdac"])
    fig.add_vline(x=float(income), line_width=2, line_color="#e53935",
                  annotation_text=f"ZIP {zip_key}", annotation_position="top right")
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                      xaxis_title="Median income", yaxis_title="Number of ZIPs", title_font_size=13)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    if not fac_data.empty:
        counts = fac_data["FACILITY_TYPE"].value_counts().reset_index()
        counts.columns = ["FACILITY_TYPE", "count"]
        fig2 = px.bar(counts, x="count", y="FACILITY_TYPE", orientation="h",
                      title=f"Facilities in ZIP {zip_key}", color_discrete_sequence=["#2cbdac"])
        fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                           xaxis_title="Count", yaxis_title="", title_font_size=13)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------
# Facilities table
# ------------------
st.markdown('<div class="section-header">Facilities in this ZIP</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if not fac_data.empty:
    show_cols = [c for c in ["NAME", "FACILITY_TYPE", "ZIP", "latitude", "longitude"] if c in fac_data.columns]
    st.dataframe(fac_data[show_cols].reset_index(drop=True), use_container_width=True, height=300)

    @st.cache_data
    def _csv_bytes(df):
        return df.to_csv(index=False).encode("utf-8")

    st.download_button("Download facility list (CSV)", data=_csv_bytes(fac_data),
                       file_name=f"facilities_{zip_key}.csv", mime="text/csv")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------
# Chatbot
# ------------------
st.markdown('<div class="section-header">Ask AI About This ZIP</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

question = st.text_input("Ask anything about this ZIP code",
                         placeholder="e.g. Is this a good ZIP for families?")
if question:
    with st.spinner("Analyzing..."):
        zip_dict = zip_data.iloc[0].to_dict()
        answer = ask_about_zip(question, zip_dict)
        st.markdown(f'<div class="chat-response">{answer}</div>', unsafe_allow_html=True)