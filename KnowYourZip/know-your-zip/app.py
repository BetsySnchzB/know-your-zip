import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk

# ------------------
# Page config
# ------------------
st.set_page_config(page_title="Know Your Zip", page_icon="📍", layout="wide")
st.title("Know Your Zip")
st.markdown("Explore zip code facilities, income, and your custom score.")

# ------------------
# Load data
# ------------------
zip_summary = pd.read_csv("data/zip_summary.csv")
facilities_points = pd.read_csv("data/facilities_points.csv")

zip_summary["ZIP"] = zip_summary["ZIP"].astype(str).str[:5].str.zfill(5)
facilities_points["ZIP"] = facilities_points["ZIP"].astype(str).str[:5].str.zfill(5)

# ------------------
# Sidebar
# ------------------
st.sidebar.header("Search Parameters")
user_zip = st.sidebar.text_input("Enter ZIP Code", placeholder="e.g., 33155")
radius_km = st.sidebar.number_input("Radius (km)", min_value=0, max_value=50, value=0)
# (Radius not used yet; we’ll wire proximity next.)

# ------------------
# Filter data
# ------------------
zip_key = (user_zip or "").strip()[:5]
zip_data = zip_summary[zip_summary["ZIP"] == zip_key]
fac_data = facilities_points[facilities_points["ZIP"] == zip_key]

# ------------------
# KPIs
# ------------------
st.subheader("📈 Key Performance Indicators")
k1, k2, k3 = st.columns(3)

def safe_get(df, col, default="—"):
    return df[col].iloc[0] if (not df.empty and col in df.columns) else default

pop = safe_get(zip_data, "Population", "—")
income = safe_get(zip_data, "INCOME", "—")
score = safe_get(zip_data, "FACILITY_SCORE_WEIGHTED", "—")

with k1:
    st.metric("Population", f"{int(pop):,}" if pop != "—" else "—")
with k2:
    st.metric("Median Income", f"${income:,.0f}" if income != "—" else "—")
with k3:
    st.metric("Facility Score", f"{int(score):,}" if score != "—" else "—")

# ------------------
# Charts
# ------------------
st.subheader("📊 Charts")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # A) Facilities by type in this ZIP
    if not fac_data.empty:
        counts = fac_data["FACILITY_TYPE"].value_counts().reset_index()
        counts.columns = ["FACILITY_TYPE", "count"]
        fig = px.bar(counts, x="FACILITY_TYPE", y="count", title="Facilities by Type")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Enter a ZIP to see facility mix.")

with chart_col2:
    # B) Income distribution across all ZIPs (highlight chosen ZIP)
    if "INCOME" in zip_summary.columns and zip_summary["INCOME"].notna().any():
        fig2 = px.histogram(zip_summary, x="INCOME", nbins=30, title="Income Distribution (All ZIPs)")
        if not zip_data.empty:
            fig2.add_vline(x=float(zip_data["INCOME"].iloc[0]), line_width=2)
        st.plotly_chart(fig2, use_container_width=True)

# ------------------
# Map
# ------------------
st.subheader("🗺️ Map")
if not fac_data.empty and {"latitude", "longitude"}.issubset(fac_data.columns):
    m = fac_data.dropna(subset=["latitude", "longitude"])
    if not m.empty:
        view = pdk.ViewState(
            latitude=float(m["latitude"].mean()),
            longitude=float(m["longitude"].mean()),
            zoom=10,
        )
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=m,
            get_position='[longitude, latitude]',
            get_radius=60,
            pickable=True,
        )
        st.pydeck_chart(
            pdk.Deck(layers=[layer], initial_view_state=view, tooltip={"text": "{NAME}\n{FACILITY_TYPE}"})
        )
    else:
        st.info("No coordinates available for this ZIP’s facilities.")
else:
    st.info("Enter a ZIP to see the map.")

# ------------------
# Table + Download
# ------------------
st.subheader("📋 Facilities in this ZIP")
if not fac_data.empty:
    show_cols = [c for c in ["NAME", "FACILITY_TYPE", "ZIP", "latitude", "longitude"] if c in fac_data.columns]
    st.dataframe(fac_data[show_cols].reset_index(drop=True), use_container_width=True)

    @st.cache_data
    def _csv_bytes(df):
        return df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download current list (CSV)",
        data=_csv_bytes(fac_data),
        file_name=f"facilities_{zip_key}.csv",
        mime="text/csv",
    )
else:
    st.info("Enter a ZIP to see the facility list.")