import os
import io
import base64
import streamlit as st
st.set_page_config(page_title="Digitization Cost Estimator", layout="wide")

import base64

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.error(f"❌ Background image not found: {image_path}")
        return ""

# 🎛️ Sidebar toggle (Only keeping usable themes)
theme_choice = st.sidebar.radio(
    "🎨 Choose Theme",
    ["🌐 Abstract Blur", "🌞 Light Glass"]
)

# Theme logic (simplified)
if theme_choice == "🌐 Abstract Blur":
    bg_image = get_base64_image("abstract.png")
    background_style = f"""
        background-image: url("data:image/png;base64,{bg_image}");
        background-size: cover;
        background-attachment: fixed;
        background-repeat: no-repeat;
        background-position: center;
        color: #222;
    """
elif theme_choice == "🌞 Light Glass":
    background_style = """
        background-color: #f5f6fa;
        color: #222;
    """

# ✅ Inject dynamic theme style
st.markdown(f"""
<style>
html, body, .stApp {{
    font-family: 'Segoe UI', sans-serif;
    {background_style}
}}
section.main > div {{
    backdrop-filter: blur(10px);
    background-color: rgba(255, 255, 255, 0.7);
    padding: 1rem;
    border-radius: 10px;
}}

h1 {{
    font-size: 2.8rem !important;
    text-align: center !important;
    margin-bottom: 0.5rem !important;
}}

.home-description p {{
    text-align: center !important;
}}

table.compact-table {{
    margin-left: 0 !important;
    width: 70% !important;
    table-layout: fixed;
    border-collapse: collapse;
}}

table.compact-table th, table.compact-table td {{
    border: 1px solid #ccc !important;
    padding: 6px 10px !important;
    word-wrap: break-word;
}}

table.compact-table th:first-child,
table.compact-table td:first-child {{
    display: none !important;
}}

h2, h3, .stSubheader {{
    margin-top: 1rem !important;
    color: #2c3e50;
}}

div[data-testid="stTable"] {{
    display: flex;
    justify-content: flex-start;
    text-align: left;
    margin-left: 0 !important;
}}

.section-header {{
    font-size: 17px;
    font-weight: 600;
    color: #2c3e50;
    margin: 15px 0 8px 0;
}}

div[data-testid="stTable"] table {{
    width: fit-content !important;
    min-width: 300px !important;
    font-size: 14px !important;
    margin-left: 0 !important;
    margin-right: auto !important;
    background-color: rgba(255, 255, 255, 0.8) !important;
    border-radius: 6px;
    padding: 8px;
}}

input, textarea, select {{
    background-color: rgba(255,255,255,0.9) !important;
}}
</style>
""", unsafe_allow_html=True)


import pandas as pd
from Cost_Estimator import cost_estimation_ui, handle_file_input, calculate_all_provider_costs, get_recommended_provider
from Cost_Estimator import(
    cost_estimation_ui,
    handle_file_input,
    calculate_all_provider_costs,
    OCR_COST_PER_PAGE,
    SCANNING_COST_PER_PAGE,
    SOFTWARE_LICENSE_COSTS,
    manpower_multiplier,
    display_clean_table
)
from Summarize_PDF import answer_from_pdf, run
from Visualizer import render_visualizations
from Reports_Generator import (
    generate_cost_report_pdf,
    generate_history_report_pdf,
    export_filtered_data_to_csv,
    export_filtered_data_to_pdf
)
from project_knowledge import answer_from_project_and_pdfs

# Load master history/costs
MASTER_HISTORY_CSV = "history/master_history.csv"
MASTER_COST_CSV = "history/master_cost_breakdown.csv"

#st.set_page_config(page_title="Digitization Cost Estimator", layout="wide")
st.title("📂 Smart Tool for Data Digitization (Cloud Cost Estimator)")


#---------------------Select Features Logic---------------------------------
selected_feature = st.sidebar.selectbox("Choose Feature", ["Home", "Cost Estimation", "Summarize PDFs", "Visualizations", "Reports", "Project Assistant"])

if selected_feature == "Summarize PDFs":
    run()  # from Summarize_PDF

elif selected_feature == "Home":
    st.markdown("""
    <div class='home-description' style='margin-top: 100px;'>
        <p style='font-size: 1.1rem; margin-top: 10px; color: #444444;'>
            Welcome to <strong>Smart Archiver</strong>, a modern tool to estimate digitization costs, summarize large PDF reports,
            and visualize storage scenarios across multiple cloud providers.
        </p>
        <p style='font-size: 1.1rem; color: #444444;'>
            From cost predictions to auto-generated reports, everything is handled – just upload your documents and let Smart Archiver guide you.
        </p>
    </div>
""", unsafe_allow_html=True)

    pass

elif selected_feature == "Cost Estimation":
    total_pages, total_size_kb = handle_file_input()
    # ✅ Convert properly before calling estimator
    size_gb = (total_size_kb / 1024) / 1024
    # ✅ Now call the estimator with clean values
    entry = cost_estimation_ui(total_pages, size_gb)

    # If estimation succeeded, calculate for all providers too
    if entry:
        st.session_state["last_estimate_entry"] = entry

    
    # Button to trigger multi-provider cost comparison
    if st.button("📊 Compare All Providers") and "last_estimate_entry" in st.session_state:
        entry = st.session_state["last_estimate_entry"]
        retention_period = entry["Retention (mo)"]
        manpower_effort = st.session_state.get("manpower_effort", "Medium")

        # Use custom or fallback pricing values
        custom = st.session_state.get("custom_pricing", {})
        ocr_cost = custom.get("ocr_cost", OCR_COST_PER_PAGE)
        scanning_cost = custom.get("scanning_cost", SCANNING_COST_PER_PAGE)
        multipliers = custom.get("multipliers", manpower_multiplier)
        fallback_prices = {
            "Amazon S3": 0.023,
            "Google Cloud Storage": 0.020,
            "Microsoft Azure": 0.020
        }

        # 🧠 Perform comparison
        results = calculate_all_provider_costs(
            total_pages=total_pages,
            size_gb=size_gb,
            retention_period=retention_period,
            manpower_effort=manpower_effort,
            ocr_cost=ocr_cost,
            scanning_cost=scanning_cost,
            manpower_multiplier=multipliers,
            software_license_costs=SOFTWARE_LICENSE_COSTS,
            fallback_prices=fallback_prices
        )

        comparison_df = pd.DataFrame(results)
        st.session_state["multi_provider_comparison"] = comparison_df
        st.markdown("<div class='section-header'>🌐 Multi-Provider Cost Comparison</div>", unsafe_allow_html=True)
        display_clean_table(comparison_df)


        # 🔍 Smart Recommendation
        get_recommended_provider(comparison_df)


elif selected_feature == "Visualizations":
    render_visualizations()

elif selected_feature == "Reports":
    st.subheader("📄 Report Generation")

    if os.path.exists(MASTER_COST_CSV) and st.button("📄 Download Cost Breakdown Report PDF"):
        cost_df = pd.read_csv(MASTER_COST_CSV)
        path = generate_cost_report_pdf(cost_df)
        with open(path, "rb") as f:
            st.download_button("⬇️ Download Cost Report", data=f, file_name=os.path.basename(path), mime="application/pdf")
        csv_buffer = io.StringIO()
        cost_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="⬇️ Download Cost Report as CSV",
            data=csv_buffer.getvalue(),
            file_name="cost_breakdown_report.csv",
            mime="text/csv"
        )

    if os.path.exists(MASTER_HISTORY_CSV) and st.button("📘 Download Full History Report PDF"):
        history_df = pd.read_csv(MASTER_HISTORY_CSV)
        path = generate_history_report_pdf(history_df)
        with open(path, "rb") as f:
            st.download_button("⬇️ Download Full History Report", data=f, file_name=os.path.basename(path), mime="application/pdf")
        csv_buffer = io.StringIO()
        history_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="⬇️ Download History Report as CSV",
            data=csv_buffer.getvalue(),
            file_name="history_report.csv",
            mime="text/csv"
        )

    if os.path.exists(MASTER_HISTORY_CSV):
        history_df = pd.read_csv(MASTER_HISTORY_CSV)
        st.markdown("📂 Export Filtered Session History")
        providers = history_df["Provider"].unique().tolist()
        selected_providers = st.multiselect("Select Provider(s):", providers, default=providers)

        min_pages = int(history_df["Pages"].min())
        max_pages = int(history_df["Pages"].max())
        if min_pages == max_pages:
            page_range = (min_pages, max_pages)
            st.info(f"Only one unique page count found: {min_pages} pages")
        else:
            page_range = st.slider("Page Range", min_pages, max_pages, (min_pages, max_pages))

        min_cost = float(history_df["Total ($)"].min())
        max_cost = float(history_df["Total ($)"].max())
        if min_cost == max_cost:
            cost_range = (min_cost, max_cost)
            st.info(f"Only one unique estimated cost: ${min_cost}")
        else:
            cost_range = st.slider("Estimated Cost Range ($)", min_cost, max_cost, (min_cost, max_cost), step=0.5)

        filtered_df = history_df[
            (history_df["Provider"].isin(selected_providers)) &
            (history_df["Pages"].between(*page_range)) &
            (history_df["Total ($)"].between(*cost_range))
        ]

        st.dataframe(filtered_df)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬇️ Export Filtered History to CSV"):
                csv_path = export_filtered_data_to_csv(filtered_df)
                with open(csv_path, "rb") as f:
                    st.download_button("📄 Download CSV", data=f, file_name=os.path.basename(csv_path), mime="text/csv")
        with col2:
            if st.button("📝 Export Filtered History to PDF"):
                pdf_path = export_filtered_data_to_pdf(filtered_df)
                with open(pdf_path, "rb") as f:
                    st.download_button("📄 Download PDF", data=f, file_name=os.path.basename(pdf_path), mime="application/pdf")

    else:
        st.warning("📭 No historical data found in master history to export.")

elif selected_feature == "Project Assistant":
    st.markdown("### 🤖 Ask me anything about the project or uploaded PDFs")
    user_query = st.text_input("Type your question here:")
    if user_query:
        response = answer_from_project_and_pdfs(user_query)
        st.markdown("**Answer:**")
        st.write(response)





