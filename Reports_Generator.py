from fpdf import FPDF
import os
import pandas as pd
from datetime import datetime
import streamlit as st

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "Digitization Report", ln=True, align='C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, title, ln=True)
        self.ln(2)

    def chapter_body(self, data, col1, col2):
        self.set_font('Arial', '', 10)
        for row in data:
            self.cell(80, 8, str(row[col1]), border=1)
            self.cell(40, 8, str(row[col2]), border=1, ln=True)

# ----------------- PDF Generators --------------------
def generate_cost_report_pdf(cost_df, save_path="reports"):
    os.makedirs(save_path, exist_ok=True)
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title("Cost Breakdown")

    if cost_df is not None:
        data = cost_df.to_dict(orient="records")
        pdf.chapter_body(data, "Cost Component", "Amount ($)")
        filename = f"cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        full_path = os.path.join(save_path, filename)
        pdf.output(full_path)
        return full_path
    return None

def generate_history_report_pdf(history_df, save_path="reports"):
    os.makedirs(save_path, exist_ok=True)
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title("Estimate History")

    headers = list(history_df.columns)
    pdf.set_font('Arial', '', 10)
    for h in headers:
        pdf.cell(40, 8, h, border=1)
    pdf.ln()

    for _, row in history_df.iterrows():
        for h in headers:
            pdf.cell(40, 8, str(row[h]), border=1)
        pdf.ln()

    filename = f"history_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    full_path = os.path.join(save_path, filename)
    pdf.output(full_path)
    return full_path

# ----------------- Filtered Export Logic --------------------
def export_filtered_data_to_csv(filtered_df, *, save_path="downloads"):
    os.makedirs(save_path, exist_ok=True)
    filename = f"filtered_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    full_path = os.path.join(save_path, filename)
    filtered_df.to_csv(full_path, index=False)
    return full_path


def export_filtered_data_to_pdf(filtered_df, *, save_path="reports"):
    os.makedirs(save_path, exist_ok=True)
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title("Filtered Estimate Export")

    headers = list(filtered_df.columns)
    pdf.set_font('Arial', '', 10)
    for h in headers:
        pdf.cell(40, 8, h, border=1)
    pdf.ln()

    for _, row in filtered_df.iterrows():
        for h in headers:
            pdf.cell(40, 8, str(row[h]), border=1)
        pdf.ln()

    filename = f"filtered_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    full_path = os.path.join(save_path, filename)
    pdf.output(full_path)
    return full_path