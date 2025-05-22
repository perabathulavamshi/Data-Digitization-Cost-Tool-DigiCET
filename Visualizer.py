import streamlit as st
import pandas as pd
import altair as alt
import os

def render_visualizations():
    cost_df_path = os.path.join("history", "master_cost_breakdown.csv")
    history_df_path = os.path.join("history", "master_history.csv")

    # Load cost breakdown
    if os.path.exists(cost_df_path):
        cost_df = pd.read_csv(cost_df_path)
        cost_df = cost_df[cost_df["Cost Component"] != "Total Estimated"]
        cost_df["Amount ($)"] = cost_df["Amount ($)"].astype(float)
    else:
        st.warning("📉 No master cost data available.")
        return

    # Load history
    history_df = pd.read_csv(history_df_path) if os.path.exists(history_df_path) else pd.DataFrame()

    tabs = st.tabs([
        "📊 Bar Chart - Cost Breakdown",
        "🍩 Donut Chart - Cost Distribution",
        "📈 Line Chart - Cost Trend",
        "🏢 Storage Provider Usage",
        "📃 Total Pages Trend",
        "💾 Total Storage Size Trend",
        "📉 Cost Comparison Across Providers",
        "🌐 Multi-Provider Cost Comparison"
    ])

    with tabs[0]:
        st.altair_chart(alt.Chart(cost_df).mark_bar().encode(
            x=alt.X("Amount ($):Q"),
            y=alt.Y("Cost Component:N", sort="-x"),
            tooltip=["Cost Component", "Amount ($)"]
        ).properties(title="Cost Breakdown per Component"), use_container_width=True)

    with tabs[1]:
        st.altair_chart(alt.Chart(cost_df).mark_arc(innerRadius=50).encode(
            theta="Amount ($):Q",
            color="Cost Component:N",
            tooltip=["Cost Component", "Amount ($)"]
        ).properties(title="Cost Distribution"), use_container_width=True)

    with tabs[2]:
        st.altair_chart(alt.Chart(cost_df).mark_line(point=True).encode(
            x="Cost Component:N",
            y="Amount ($):Q",
            tooltip=["Cost Component", "Amount ($)"]
        ).properties(title="Cost Trend"), use_container_width=True)

    if not history_df.empty:
        with tabs[3]:
            st.altair_chart(alt.Chart(history_df).mark_bar().encode(
                x="Provider:N",
                y="Total ($):Q",
                color="Provider:N",
                tooltip=["Provider", "Total ($)"]
            ).properties(title="Storage Provider Cost Comparison"), use_container_width=True)

        with tabs[4]:
            st.altair_chart(alt.Chart(history_df.reset_index()).mark_line(point=True).encode(
                x=alt.X("index:Q", title="Entry"),
                y="Pages:Q",
                tooltip=["Pages"]
            ).properties(title="Trend of Pages Over Time"), use_container_width=True)

        with tabs[5]:
            st.altair_chart(alt.Chart(history_df.reset_index()).mark_area(opacity=0.3).encode(
                x=alt.X("index:Q", title="Entry"),
                y="Size (GB):Q",
                tooltip=["Size (GB)"]
            ).properties(title="Storage Size Trend"), use_container_width=True)

        with tabs[6]:
            st.altair_chart(alt.Chart(history_df).mark_bar().encode(
                x=alt.X("Provider:N", title="Storage Provider"),
                y=alt.Y("Total ($):Q", title="Estimated Cost ($)"),
                color="Provider:N",
                tooltip=["Provider", "Total ($)", "Pages", "Retention (mo)"]
            ).properties(title="Estimated Cost Comparison Across Cloud Providers"), use_container_width=True)

        with tabs[7]:
            if "multi_provider_comparison" in st.session_state:
                df = pd.DataFrame(st.session_state["multi_provider_comparison"])
                st.altair_chart(alt.Chart(df).mark_bar().encode(
                    x=alt.X("Provider:N", title="Cloud Provider"),
                    y=alt.Y("Total ($):Q", title="Estimated Total Cost ($)"),
                    color="Provider:N",
                    tooltip=["Provider", "Total ($)", "Storage ($)", "OCR ($)", "Scanning ($)", "Manpower ($)", "License ($)"]
                ).properties(title="Multi-Provider Total Cost Comparison"), use_container_width=True)

    else:
        for i in range(4, 8):
            with tabs[i]:
                st.info("📌 No master history data available for this chart.")

    
