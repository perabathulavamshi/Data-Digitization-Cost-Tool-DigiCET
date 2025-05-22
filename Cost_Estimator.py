import os
import requests
import pandas as pd
import streamlit as st
import fitz  # PyMuPDF
from datetime import datetime


# Constants
AVG_PAGE_SIZE_KB = 350
OCR_COST_PER_PAGE = 0.001
SCANNING_COST_PER_PAGE = 0.002
SOFTWARE_LICENSE_COSTS = {
    "Amazon S3": 50,
    "Google Cloud Storage": 40,
    "Microsoft Azure": 40
}
manpower_multiplier = {"Low": 0.03, "Medium": 0.05, "High": 0.08}

AWS_REGIONS = [
    "US East (N. Virginia)", "US West (Oregon)", "EU (Ireland)", "Asia Pacific (Singapore)"
]
AZURE_REGIONS = ["eastus", "westeurope", "southeastasia", "australiaeast"]
GCP_REGIONS = ["us", "eu", "asia"]

def format_metadata(value):
    return value.strip().title() if value else "N/A"

def format_creation_date(date_str):
    if date_str and date_str.startswith("D:"):
        try:
            date_str = date_str[2:].split("+")[0]
            return datetime.strptime(date_str, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return "Invalid Date Format"
    return "N/A"

def handle_file_input():
    st.markdown("<div class='section-header'>📥 Select Input Method:</div>", unsafe_allow_html=True)
    option = st.radio("", ["Upload PDFs", "Enter Manually"], label_visibility="collapsed")

    total_pages = 0
    total_size_kb = 0
    file_info = []
    pdf_metadata_dict = {}
    uploaded_filenames = set()

    if option == "Upload PDFs":
        st.markdown("<div class='section-header'>Upload PDF files</div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")


        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name in uploaded_filenames:
                    st.warning(f"⚠️ File '{uploaded_file.name}' is already uploaded and will be skipped.")
                    continue

                uploaded_filenames.add(uploaded_file.name)
                upload_path = os.path.join("uploads", uploaded_file.name)
                with open(upload_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                size_kb = os.path.getsize(upload_path) / 1024
                total_size_kb += size_kb

                with fitz.open(upload_path) as doc:
                    pages = len(doc)
                    total_pages += pages
                    meta = doc.metadata

                    pdf_metadata_dict[uploaded_file.name] = {
                        "Title": format_metadata(meta.get('title', 'N/A')),
                        "Author": format_metadata(meta.get('author', 'N/A')),
                        "Creation Date": format_creation_date(meta.get('creationDate', 'N/A')),
                        "Subject": format_metadata(meta.get('subject', 'N/A'))
                    }

                file_info.append([uploaded_file.name, f"{size_kb:.2f}", pages])

            size_gb = (total_size_kb / 1024) / 1024
            #st.write(f"📏 DEBUG: total_pages={total_pages}, total_size_kb={total_size_kb}, size_gb={size_gb}")

            st.markdown("<div class='section-header'>📂 Uploaded File Summary</div>", unsafe_allow_html=True)
            uploaded_file_df = pd.DataFrame(file_info, columns=["File Name", "Size (KB)", "Pages"])
            df = uploaded_file_df.reset_index(drop=True)
            df.index = [''] * len(df)  # Set empty index
            display_clean_table(df)

            st.markdown("<div class='section-header'>📊 Combined File Details</div>", unsafe_allow_html=True)
            combined_file_df = pd.DataFrame({
                "Property": ["Total Pages", "Total Size (KB)", "Total Size (GB)", "Type"],
                "Value": [str(total_pages), f"{total_size_kb:.2f}", f"{size_gb:.2f}", "PDF"]
            })
            df = combined_file_df.reset_index(drop=True)
            df.index = [''] * len(df)  # Set empty index
            display_clean_table(df)

            st.markdown("<div class='section-header'>📊 Select PDF to View Metadata</div>", unsafe_allow_html=True)
            selected_file = st.selectbox("", list(pdf_metadata_dict.keys()),label_visibility="collapsed")
            if selected_file:
                metadata_df = pd.DataFrame({
                    "Property": list(pdf_metadata_dict[selected_file].keys()),
                    "Value": list(pdf_metadata_dict[selected_file].values())
                })
                df = metadata_df.reset_index(drop=True)
                df.index = [''] * len(df)  # Set empty index
                display_clean_table(df)

    elif option == "Enter Manually":
        total_pages = st.number_input("Enter Total Number of Pages:", min_value=1, step=1)
        total_size_kb = total_pages * AVG_PAGE_SIZE_KB
        size_gb = (total_size_kb / 1024) / 1024

        st.subheader(" 📂 Manual Entry Details")
        manual_df = pd.DataFrame({
            "Property": ["Total Pages", "Estimated Total Size (GB)", "Type"],
            "Value": [str(total_pages), f"{size_gb:.2f}", "Manual"]
        })
        df = manual_df.reset_index(drop=True)
        df.index = [''] * len(df)  # Set empty index
        display_clean_table(df)

    return total_pages, total_size_kb

# Cloud API pricing
@st.cache_data(ttl=3600)
def get_gcp_storage_price(region_code="us"):
    try:
        url = "https://cloudpricingcalculator.appspot.com/static/data/pricelist.json"
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data["CP-STORAGE-MULTI-REGIONAL"][region_code]["USD"])
    except:
        return None

@st.cache_data(ttl=3600)
def get_aws_storage_price(region_name="US East (N. Virginia)"):
    try:
        url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/index.json"
        response = requests.get(url, timeout=10)
        data = response.json()
        terms = data.get("terms", {}).get("OnDemand", {})
        products = data.get("products", {})

        for sku, product in products.items():
            attr = product.get("attributes", {})
            if attr.get("storageClass") == "Standard" and attr.get("location") == region_name:
                sku_terms = terms.get(sku, {})
                if sku_terms:
                    price_dimensions = next(iter(sku_terms.values()))
                    price_per_gb = list(price_dimensions["priceDimensions"].values())[0]["pricePerUnit"]["USD"]
                    return float(price_per_gb)
    except:
        return None

@st.cache_data(ttl=3600)
def get_azure_storage_price(region_code="eastus"):
    try:
        url = (
            f"https://prices.azure.com/api/retail/prices"
            f"?$filter=serviceName eq 'Storage' and armRegionName eq '{region_code}'"
            f" and skuName eq 'Hot LRS' and meterName eq 'Data Stored'"
        )
        response = requests.get(url, timeout=10)
        data = response.json()
        items = data.get("Items", [])
        if items:
            return float(items[0]["retailPrice"])
    except:
        return None


def cost_estimation_ui(total_pages, size_gb):
    # Select Cloud Provider
    st.markdown("<div class='section-header'>Select Cloud Storage Provider</div>", unsafe_allow_html=True)
    storage_provider = st.selectbox("", ["Amazon S3", "Google Cloud Storage", "Microsoft Azure"],label_visibility="collapsed")


    # Region selection and cost
    if storage_provider == "Amazon S3":
        st.markdown("<div class='section-header'>Select AWS Region</div>", unsafe_allow_html=True)
        region = st.selectbox("", AWS_REGIONS,label_visibility="collapsed")
        STORAGE_COST_PER_GB = get_aws_storage_price(region)
    elif storage_provider == "Google Cloud Storage":
        st.markdown("<div class='section-header'>Select GCP Region</div>", unsafe_allow_html=True)
        region = st.selectbox("", GCP_REGIONS,label_visibility="collapsed")
        STORAGE_COST_PER_GB = get_gcp_storage_price(region)
    elif storage_provider == "Microsoft Azure":
        st.markdown("<div class='section-header'>Select Azure Region</div>", unsafe_allow_html=True)
        region = st.selectbox("", AZURE_REGIONS,label_visibility="collapsed")
        STORAGE_COST_PER_GB = get_azure_storage_price(region)

    if STORAGE_COST_PER_GB is not None:
        st.success(f"Live Pricing for {storage_provider}: ${STORAGE_COST_PER_GB:.2f} per GB/month")
    else:
        fallback = {"Amazon S3": 0.023, "Google Cloud Storage": 0.020, "Microsoft Azure": 0.020}
        st.warning("⚠️ Using fallback storage rate.")
        STORAGE_COST_PER_GB = fallback[storage_provider]

    # Define license cost and other inputs
    license_cost = SOFTWARE_LICENSE_COSTS[storage_provider]

    st.markdown("<div class='section-header'>Enter Retention Period (months):</div>", unsafe_allow_html=True)
    retention_period = st.number_input("", min_value=1, step=1,label_visibility="collapsed")
    st.markdown("<div class='section-header'>Select Manpower Effort Level</div>", unsafe_allow_html=True)
    manpower_effort = st.selectbox("", ["Low", "Medium", "High"],label_visibility="collapsed")

    # Custom Pricing
    use_custom = st.checkbox("🔧 Enable Custom Pricing")
    if use_custom:
        st.markdown("<div class='section-header'>🛠️ Custom Pricing Inputs</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Storage Cost ($/GB/month):</div>", unsafe_allow_html=True)
        STORAGE_COST_PER_GB = st.number_input("", value=STORAGE_COST_PER_GB, step=0.001,label_visibility="collapsed")
        st.markdown("<div class='section-header'>OCR Cost ($/page):</div>", unsafe_allow_html=True)
        ocr_cost = st.number_input("", value=OCR_COST_PER_PAGE, step=0.0001,label_visibility="collapsed")
        st.markdown("<div class='section-header'>Scanning Cost ($/page):</div>", unsafe_allow_html=True)
        scanning_cost = st.number_input("", value=SCANNING_COST_PER_PAGE, step=0.0001,label_visibility="collapsed")
        st.markdown("<div class='section-header'>Software License Cost ($):</div>", unsafe_allow_html=True)
        license_cost = st.number_input("", value=float(license_cost), step=1.0,label_visibility="collapsed")

        manpower_multiplier["Low"] = st.slider("Low Effort Multiplier:", 0.0, 0.1, manpower_multiplier["Low"], step=0.001)
        manpower_multiplier["Medium"] = st.slider("Medium Effort Multiplier:", 0.0, 0.1, manpower_multiplier["Medium"], step=0.001)
        manpower_multiplier["High"] = st.slider("High Effort Multiplier:", 0.0, 0.1, manpower_multiplier["High"], step=0.001)
    else:
        ocr_cost = OCR_COST_PER_PAGE
        scanning_cost = SCANNING_COST_PER_PAGE

    # Perform Cost Estimation
    if st.button("🚀 Estimate Cost"):
        storage_cost = size_gb * STORAGE_COST_PER_GB * retention_period
        ocr_total = total_pages * ocr_cost
        manpower_total = total_pages * manpower_multiplier[manpower_effort]
        scanning_total = total_pages * scanning_cost
        subtotal = storage_cost + ocr_total + manpower_total + scanning_total
        final_total = subtotal + license_cost

        st.markdown("<div class='section-header'>💰 Cost Breakdown</div>", unsafe_allow_html=True)
        cost_df = pd.DataFrame({
            "Cost Component": ["Storage", "OCR Processing", "Manpower", "Scanning", "Total Estimated"],
            "Amount ($)": [f"{storage_cost:.2f}", f"{ocr_total:.2f}", f"{manpower_total:.2f}", f"{scanning_total:.2f}", f"{subtotal:.2f}"]
        })

        st.session_state["cost_df"] = cost_df
        st.markdown(f"🔐 **Software License Cost:** ${license_cost:.2f}")
        display_clean_table(cost_df)
        st.session_state["cost_df"] = cost_df

        # ✅ Save to master history (all-time, across sessions)
        history_dir = "history"
        os.makedirs(history_dir, exist_ok=True)

        # Add timestamp for tracking
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append to master_history.csv
        entry_with_time = {
            "Timestamp": timestamp,
            "Pages": total_pages,
            "Size (GB)": round(size_gb, 2),
            "Provider": storage_provider,
            "Retention (mo)": retention_period,
            "Total ($)": round(final_total, 2)
        }

        # ✅ Save to session history
        current_entry = {
            "Pages": total_pages,
            "Size (GB)": round(size_gb, 2),
            "Provider": storage_provider,
            "Retention (mo)": retention_period,
            "Total ($)": round(final_total, 2)
        }

        if "history" not in st.session_state:
            st.session_state.history = []

        if current_entry not in st.session_state.history:
            st.session_state.history.append(current_entry)

        # ✅ Save to CSV file
        history_df = pd.DataFrame(st.session_state.history)
        os.makedirs("history", exist_ok=True)
        history_df.to_csv(os.path.join("history", "session_history.csv"), index=False)

        history_path = os.path.join(history_dir, "master_history.csv")
        history_df = pd.DataFrame([entry_with_time])
        history_df.to_csv(history_path, mode="a", header=not os.path.exists(history_path), index=False)

        # Append to master_cost_breakdown.csv
        if cost_df is not None:
            cost_df["Provider"] = storage_provider
            cost_df["Timestamp"] = timestamp
            cost_path = os.path.join(history_dir, "master_cost_breakdown.csv")
            cost_df.to_csv(cost_path, mode="a", header=not os.path.exists(cost_path), index=False)


        multi_provider_results = calculate_all_provider_costs(
            total_pages=total_pages,
            size_gb=size_gb,
            retention_period=retention_period,
            manpower_effort=manpower_effort,
            ocr_cost=ocr_cost,
            scanning_cost=scanning_cost,
            manpower_multiplier=manpower_multiplier,
            software_license_costs=SOFTWARE_LICENSE_COSTS,
            fallback_prices={"Amazon S3": 0.023, "Google Cloud Storage": 0.020, "Microsoft Azure": 0.020}
        )

        # Store in session for later use (visualization/reporting)
        st.session_state["multi_provider_comparison"] = multi_provider_results


        return current_entry

def calculate_all_provider_costs(total_pages, size_gb, retention_period, manpower_effort, ocr_cost, scanning_cost, manpower_multiplier, software_license_costs, fallback_prices):
    provider_costs = []

    for provider in ["Amazon S3", "Google Cloud Storage", "Microsoft Azure"]:
        if provider == "Amazon S3":
            storage_price = get_aws_storage_price("US East (N. Virginia)") or fallback_prices["Amazon S3"]
        elif provider == "Google Cloud Storage":
            storage_price = get_gcp_storage_price("us") or fallback_prices["Google Cloud Storage"]
        elif provider == "Microsoft Azure":
            storage_price = get_azure_storage_price("eastus") or fallback_prices["Microsoft Azure"]

        storage_cost = size_gb * storage_price * retention_period
        ocr_total = total_pages * ocr_cost
        scanning_total = total_pages * scanning_cost
        manpower_total = total_pages * manpower_multiplier[manpower_effort]
        license_cost = software_license_costs[provider]
        total = storage_cost + ocr_total + scanning_total + manpower_total + license_cost

        provider_costs.append({
            "Provider": provider,
            "Storage ($)": round(storage_cost, 2),
            "OCR ($)": round(ocr_total, 2),
            "Scanning ($)": round(scanning_total, 2),
            "Manpower ($)": round(manpower_total, 2),
            "License ($)": round(license_cost, 2),
            "Total ($)": round(total, 2)
        })

    return provider_costs
    
def get_recommended_provider(results_df: pd.DataFrame):
    if results_df.empty:
        st.warning("No provider results available for recommendation.")
        return

    min_cost = results_df["Total ($)"].min()
    recommended = results_df[results_df["Total ($)"] == min_cost]

    if len(recommended) > 1:
        st.markdown(f"💡 Multiple providers offer the lowest cost of **${min_cost:.2f}**:")
        for _, row in recommended.iterrows():
            st.markdown(f"- ✅ {row['Provider']}")
    else:
        provider = recommended.iloc[0]
        st.markdown(f"💡 Recommended Provider: **{provider['Provider']}** with estimated cost **${provider['Total ($)']:.2f}**")

def display_clean_table(df):
    df = df.dropna(axis=1, how='all')  
    df = df.loc[:, ~(df == '').all()]  
    df = df.reset_index(drop=True)
    df.index = [''] * len(df)  
    st.table(df)

