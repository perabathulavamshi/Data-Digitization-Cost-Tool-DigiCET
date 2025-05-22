import os
from langchain_huggingface import HuggingFaceEndpoint
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.3",
    task="text-generation",
    temperature=0.5,
    max_new_tokens=512
)

def load_and_split_pdf(file_path):
    loader = PyMuPDFLoader(file_path)
    docs = loader.load()
    if not docs:
        raise ValueError(f"No pages found in the PDF: {file_path}")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    return splitter.split_documents(docs)

def create_vector_store(chunks):
    embeddings = HuggingFaceEmbeddings()
    return FAISS.from_documents(chunks, embeddings)

def create_qa_chain(vector_store):
    return RetrievalQA.from_chain_type(llm=llm, retriever=vector_store.as_retriever())

def answer_from_pdf(filename, question):
    file_path = os.path.join("uploads", filename)
    chunks = load_and_split_pdf(file_path)
    vectordb = create_vector_store(chunks)
    qa_chain = create_qa_chain(vectordb)
    return qa_chain.run(question)

# 👇 Wrap Streamlit interface in a callable function
def run():
    import streamlit as st

    pdf_files = [f for f in os.listdir("uploads") if f.endswith(".pdf")]
    st.markdown("<div class='section-header'>Select a PDF to Summarize:</div>", unsafe_allow_html=True)
    selected_pdf = st.selectbox("", pdf_files, label_visibility="collapsed")

    if st.button("Summarize Selected PDF"):
        with st.spinner("Summarizing... Please wait."):
            try:
                summary = answer_from_pdf(selected_pdf, f"Summarize the contents of {selected_pdf}.")
                st.subheader("📘 Summary")
                if isinstance(summary, dict) and "result" in summary:
                    st.write(summary["result"])
                else:
                    st.write(summary)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
