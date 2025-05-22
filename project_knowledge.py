import os
import json
import fitz  # PyMuPDF
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

PROJECT_INFO_PATH = "project_info.json"
UPLOADS_FOLDER = "uploads"
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_data
def load_project_info():
    if os.path.exists(PROJECT_INFO_PATH):
        with open(PROJECT_INFO_PATH, "r") as f:
            return json.load(f)
    return {}

@st.cache_data
def extract_text_chunks_from_pdfs():
    text_chunks = []
    if os.path.exists(UPLOADS_FOLDER):
        for filename in os.listdir(UPLOADS_FOLDER):
            if filename.lower().endswith(".pdf"):
                path = os.path.join(UPLOADS_FOLDER, filename)
                try:
                    with fitz.open(path) as doc:
                        for i, page in enumerate(doc):
                            text = page.get_text().strip()
                            if text:
                                text_chunks.append({
                                    "filename": filename,
                                    "page": i + 1,
                                    "text": text
                                })
                except Exception as e:
                    text_chunks.append({
                        "filename": filename,
                        "page": 0,
                        "text": f"[ERROR] Could not read file: {e}"
                    })
    return text_chunks

def semantic_pdf_search(query, top_k=3):
    chunks = extract_text_chunks_from_pdfs()
    if not chunks:
        return []

    chunk_texts = [chunk["text"] for chunk in chunks]
    chunk_embeddings = MODEL.encode(chunk_texts)
    query_embedding = MODEL.encode([query])

    similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        chunk = chunks[idx]
        score = similarities[idx]
        snippet = chunk["text"][:500].replace("\n", " ")
        results.append(f"📄 **{chunk['filename']}** (Page {chunk['page']}):\n\"{snippet}...\" \n(Similarity Score: {score:.2f})")
    return results

def answer_from_project_and_pdfs(user_query):
    user_query = user_query.lower()
    project_info = load_project_info()

    # Check project info first
    if "feature" in user_query or "functionality" in user_query:
        return "🔧 Key Features:\n- " + "\n- ".join(project_info.get("features", []))
    elif "about project" in user_query or "what is this project" in user_query:
        return f"📘 **About the Project**:\n{project_info.get('description', 'No description found.')}"
    elif "tech stack" in user_query or "technologies" in user_query:
        return "🛠️ Tech Stack:\n- " + "\n- ".join(project_info.get("tech_stack", []))
    elif "target users" in user_query or "who is this for" in user_query:
        return "🎯 Target Users:\n- " + "\n- ".join(project_info.get("target_users", []))
    elif "future" in user_query or "next" in user_query:
        return "🚀 Future Scope:\n- " + "\n- ".join(project_info.get("future_scope", []))

    # Otherwise perform semantic PDF search
    matches = semantic_pdf_search(user_query)
    if matches:
        #with st.spinner("Analyzing... Please wait."):
        return "\n\n".join(matches)
    return "🤖 I couldn't find a direct match. Try rephrasing or ask about the project details."
