from mftool import Mftool
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# Initialize Mutual Fund Tool
mf = Mftool()

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Mutual Funds Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar Styling ---
st.sidebar.markdown("## 📊 Mutual Funds Dashboard", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Fetch Scheme Codes for Dropdown
Scheme_names = {v: k for k, v in mf.get_scheme_codes().items()}

# --- Sidebar Menu ---
option = st.sidebar.radio(
    "Choose an Action",
    ["View Available Schemes", "Scheme Details", "Historical NAV",
     "Compare NAV", "Average AUM", "Performance Heatmap", "Risk & Volatility Analysis", "Current NAV"]
)

# --- View Available Schemes ---
if option == "View Available Schemes":
    st.title("📋 View Available Schemes")
    amc = st.sidebar.text_input("Enter AMC Name", "ICICI")
    schemes = mf.get_available_schemes(amc)

    if schemes:
        df_schemes = pd.DataFrame(schemes.items(), columns=["Scheme Code", "Scheme Name"])
        st.dataframe(df_schemes, use_container_width=True)
    else:
        st.warning("No schemes found for the given AMC.")

# --- Scheme Details ---
elif option == "Scheme Details":
    st.title("🔍 Scheme Details")
    scheme_name = st.sidebar.selectbox("Select a Scheme", list(Scheme_names.keys()))
    scheme_code = Scheme_names[scheme_name]

    details = mf.get_scheme_details(scheme_code)

    if details:
        df_details = pd.DataFrame(details.items(), columns=["Attribute", "Value"])
        st.table(df_details)
    else:
        st.error("Scheme details not found.")

# --- Historical NAV ---
elif option == "Historical NAV":
    st.title("📈 Historical NAV")
    scheme_name = st.sidebar.selectbox("Select a Scheme", list(Scheme_names.keys()))
    scheme_code = Scheme_names[scheme_name]

    nav_data = mf.get_scheme_historical_nav(scheme_code, as_Dataframe=True)

    if not nav_data.empty:
        nav_data = nav_data.reset_index().rename(columns={"index": "date"})
        nav_data["date"] = pd.to_datetime(nav_data["date"], dayfirst=True)
        nav_data.set_index("date", inplace=True)
        st.line_chart(nav_data["nav"], use_container_width=True)

    else:
        st.warning("No historical NAV data available.")

# --- Compare NAV ---
elif option == "Compare NAV":
    st.title("📊 Compare NAV")
    selected_schemes = st.sidebar.multiselect("Select Schemes", list(Scheme_names.keys()))

    if selected_schemes:
        comparison_df = pd.DataFrame()

        for scheme in selected_schemes:
            scheme_code = Scheme_names[scheme]
            data = mf.get_scheme_historical_nav(scheme_code, as_Dataframe=True)

            if not data.empty:
                data = data.reset_index().rename(columns={"index": "date"})
                data["date"] = pd.to_datetime(data["date"], dayfirst=True)
                comparison_df[scheme] = data.set_index("date")["nav"]

        fig = px.line(comparison_df, title="NAV Comparison", labels={"value": "NAV", "index": "date"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select at least one scheme.")

# --- Average AUM ---
elif option == "Average AUM":
    st.title("💰 Average AUM")
    aum_data = mf.get_average_aum("July - September 2024", False)

    if aum_data:
        df_aum = pd.DataFrame(aum_data)
        df_aum["Total AUM"] = df_aum[["AAUM Overseas", "AAUM Domestic"]].astype(float).sum(axis=1)
        st.dataframe(df_aum[["Fund Name", "Total AUM"]], use_container_width=True)
    else:
        st.warning("No AUM Data Available.")

# --- Performance Heatmap ---
elif option == "Performance Heatmap":
    st.header("🔥 Performance Heatmap")
    scheme_code = Scheme_names[st.sidebar.selectbox("Select a Scheme", Scheme_names.keys())]
    nav_data = mf.get_scheme_historical_nav(scheme_code, as_Dataframe=True)

    if not nav_data.empty:
        nav_data = nav_data.reset_index().rename(columns={"index": "date"})
        nav_data["date"] = pd.to_datetime(nav_data["date"], dayfirst=True)
        nav_data["Month"] = nav_data["date"].dt.month
        nav_data["nav"] = nav_data["nav"].astype(float)

        heatmap_data = nav_data.groupby("Month")["nav"].mean().reset_index()
        heatmap_data["Month"] = heatmap_data["Month"].apply(lambda x: pd.to_datetime(str(x), format="%m").strftime("%B"))

        fig = px.density_heatmap(heatmap_data, x="Month", y="nav", title="NAV Performance Heatmap", color_continuous_scale="Viridis")
        st.plotly_chart(fig)

    else:
        st.warning("No historical NAV data available.")

# --- Risk & Volatility Analysis ---
elif option == "Risk & Volatility Analysis":
    st.header("Risk and Volatility Analysis")
    scheme_name = st.sidebar.selectbox("Select a Scheme", Scheme_names.keys())
    scheme_code = Scheme_names[scheme_name]
    nav_data = mf.get_scheme_historical_nav(scheme_code, as_Dataframe=True)

    if not nav_data.empty:
        nav_data = nav_data.reset_index().rename(columns={"index": "date"})
        nav_data["date"] = pd.to_datetime(nav_data["date"], dayfirst=True)
        nav_data["nav"] = pd.to_numeric(nav_data["nav"], errors="coerce")
        nav_data.dropna(subset=["nav"], inplace=True)
        nav_data["returns"] = nav_data["nav"].pct_change()
        nav_data.dropna(subset=["returns"], inplace=True)

        annualized_volatility = nav_data["returns"].std() * np.sqrt(252)
        annualized_return = (1 + nav_data["returns"].mean()) ** 252 - 1
        risk_free_rate = 0.06
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility

        st.write(f"### Metrics for {scheme_name}")
        st.metric("Annualized Volatility", f"{annualized_volatility:.2%}")
        st.metric("Annualized Return", f"{annualized_return:.2%}")
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")

        fig = px.scatter(nav_data, x="date", y="returns", title=f"Risk-Return Scatter for {scheme_name}", labels={"returns": "Daily Returns", "date": "Date"})
        st.plotly_chart(fig)

# --- Current NAV ---
elif option == "Current NAV":
    st.title("📅 Current NAV")
    scheme_name = st.sidebar.selectbox("Select a Scheme", list(Scheme_names.keys()))
    scheme_code = Scheme_names[scheme_name]

    today_nav = mf.get_scheme_quote(scheme_code)

    if today_nav:
        st.write(f"### NAV for {scheme_name} on {datetime.date.today().strftime('%Y-%m-%d')}")
        st.metric(label="Current NAV", value=today_nav["nav"])
    else:
        st.error("Current NAV not available.")
