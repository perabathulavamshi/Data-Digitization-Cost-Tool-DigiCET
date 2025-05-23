# 📄 Data Digitization Cost Tool – DigiCET

An AI-powered Streamlit application to **estimate document digitization costs** with cloud pricing APIs, PDF metadata analysis, and real-time dashboards. Developed for the City of Stockton as a Capstone Project in the Master of Data Science program at the University of the Pacific.

---

## 📌 Key Features

- 📤 Upload PDF files or enter document details manually.
- 🔍 Automatic metadata extraction: page count, size, title, and more.
- 💲 Real-time cost estimation using cloud storage APIs from **AWS**, **Azure**, and **GCP**.
- 📊 Dynamic charts and dashboards with Altair visualizations.
- 📄 Exportable cost reports in **PDF** and **CSV** formats.
- 🧠 Smart PDF summarization using **LangChain** + **Mistral-7B**.
- 🤖 Built-in chatbot powered by **MiniLM** for guidance.
- 📁 Session history and multi-provider cost comparison.
- ⚙️ Fully customizable pricing overrides and region selection.

---

## 🔧 Tech Stack

| Component       | Technology Used                      |
|-----------------|--------------------------------------|
| Frontend        | Streamlit, Altair                    |
| Backend         | Python, PyMuPDF (Fitz), Pandas       |
| AI/ML           | LangChain, Mistral-7B, MiniLM        |
| Visualization   | Altair, Matplotlib                   |
| Reporting       | FPDF                                 |
| Cloud APIs      | AWS S3, GCP Cloud, Azure Blob APIs   |
| Deployment      | Docker, GitHub                       |

---

## 📂 Folder Structure
├── Cost_Estimator.py # Core logic for cost calculation

├── Summarize_PDF.py # Mistral-7B-based summarization module

├── Visualizer.py # Dashboard rendering

├── Reports_Generator.py # Report (PDF/CSV) creation

├── app.py # Main Streamlit app

├── Dockerfile # Docker setup

├── downloads/, history/, reports/ # Output & session tracking




---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/perabathulavamshi/Data-Digitization-Cost-Tool-DigiCET.git
cd Data-Digitization-Cost-Tool-DigiCET

### 2. Install Dependencies
We recommend using conda or venv for environment isolation.
pip install -r requirements.txt

### 3. Run the Application
streamlit run app.py

📦 Docker Support
You can also run the entire tool using Docker:
docker build -t digitool .
docker run -p 8501:8501 digitool

##📄 Sample Reports
PDF & CSV Output: Cost breakdown, session history, multi-provider comparison

Viewable under the /reports folder once estimation is complete

##📘 Documentation
Refer to the full Capstone Project report for detailed breakdowns of:

Cloud pricing logic

Manpower cost calculations

Technical limitations and enhancements

Use cases across public departments
📄 Report: Data Digitization Cost Estimator Report.pdf

##📥 Contributions
This project was developed as a Capstone Project for:
City of Stockton in collaboration with
University of the Pacific – Master of Data Science Program
Guided by: Prof. Arshad Khan

👥 Team:

Purva Mugdiya

Usha Pavani Thopalle

Sahana Reddy

Vamshi Krishna Perabathula

Chaitanya Vishnu Radhakrishna

Chen-Li Lee

##📬 Contact
For implementation support, clarification, or deployment inquiries:
📧 Vamshi Krishna Perabathula



