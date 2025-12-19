import streamlit as st
import psutil
import time
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from config import SETTINGS
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

st.set_page_config(page_title="Repo-Mind | Forensic AI", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for a Dark Engineering Theme ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 10px; border: 1px solid #30363d; }
    .stProgress > div > div > div > div { background-color: #238636; }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar with Live Gauges ---
with st.sidebar:
    st.title("📟 System Monitor")
    
    # CPU Usage Bar
    cpu_usage = psutil.cpu_percent()
    st.write(f"CPU Usage: {cpu_usage}%")
    st.progress(cpu_usage / 100)
    
    # RAM Usage Bar
    ram_stats = psutil.virtual_memory()
    st.write(f"RAM Usage: {ram_stats.percent}%")
    st.progress(ram_stats.percent / 100)
    st.caption(f"Used: {ram_stats.used / (1024**3):.1f}GB / Total: {ram_stats.total / (1024**3):.1f}GB")
    
    st.divider()
    model_choice = st.sidebar.selectbox("Model Engine", [SETTINGS["llm_model"], "phi3"], index=0)
    k_val = st.sidebar.slider("Vector Search Depth (k)", 1, 15, 10)

# --- RAG Logic with Thinking Animation ---
def get_response(user_input):
    with st.status("🚀 Deep Scanning Repository...", expanded=True) as status:
        start_time = time.time()
        
        status.write("🔍 Initializing Local LLM & Embeddings...")
        llm = OllamaLLM(model=model_choice)
        embeddings = OllamaEmbeddings(model=SETTINGS["embed_model"])
        
        status.write("📂 Querying ChromaDB Vector Store...")
        vector_db = Chroma(persist_directory=SETTINGS["db_path"], embedding_function=embeddings)
        retriever = vector_db.as_retriever(search_kwargs={"k": k_val})

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Senior Software Engineer. Explain the fix using the provided Git context.
            Always highlight 'CODE_CHANGES:' and explain the '+/-' lines clearly.
            Context: {context}"""),
            ("human", "{input}")
        ])

        status.write("🧠 Synthesizing Forensic Analysis...")
        chain = create_retrieval_chain(retriever, create_stuff_documents_chain(llm, prompt))
        response = chain.invoke({"input": user_input})
        
        end_time = time.time()
        status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
        
    duration = end_time - start_time
    tokens = len(response["answer"]) / 4 
    throughput = tokens / duration if duration > 0 else 0
    
    return response, duration, throughput

# --- Main UI ---
st.title("🧠 Repo-Mind")
st.caption("Local RAG Forensic Tool for Git History Analysis")

if prompt := st.chat_input("Analyze the Proxy-Authorization fix..."):
    # User Message
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Assistant Message
    with st.chat_message("assistant"):
        res, duration, throughput = get_response(prompt)
        
        # --- Simulated Streaming Effect ---
        placeholder = st.empty()
        full_response = ""
        for word in res["answer"].split(" "):
            full_response += word + " "
            placeholder.markdown(full_response + "▌")
            time.sleep(0.02) # Adjust for typing speed
        placeholder.markdown(full_response)
        
        # --- Performance Dashboard ---
        st.write("")
        m1, m2, m3 = st.columns(3)
        m1.metric("Latency", f"{duration:.2f}s")
        m2.metric("Throughput", f"{throughput:.1f} tok/s")
        m3.metric("Context Chunks", f"{len(res['context'])}")
        
        # --- Source Evidence ---
        with st.expander("🛠️ View Historical Source Diffs"):
            for i, doc in enumerate(res["context"]):
                st.markdown(f"**Source {i+1}:** `{doc.metadata.get('hash', 'N/A')}`")
                st.code(doc.page_content[:600], language="diff")
                st.divider()