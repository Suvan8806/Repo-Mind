import streamlit as st
import psutil
import time
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from config import SETTINGS
from langchain.chains.combine_documents import create_stuff_documents_chain

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
    model_choice = st.sidebar.selectbox(
        "Model Engine (Ollama)",
        [SETTINGS["llm_model"], "qwen2.5-coder:7b", "phi3:mini", "llama3.2:1b"],
        index=0,
        help="Pick a model you have pulled (`ollama pull …`). Smaller tags use less RAM.",
    )
    k_val = st.sidebar.slider("Vector Search Depth (k)", 1, 30, 20)

def get_response(user_input):
    with st.status("🚀 Deep Scanning Repository...", expanded=True) as status:
        start_time = time.time()
        
        status.write("🔍 Initializing Local LLM & Embeddings...")
        llm = OllamaLLM(model=model_choice)
        embeddings = OllamaEmbeddings(model=SETTINGS["embed_model"])
        
        status.write("📂 Querying ChromaDB Vector Store...")
        vector_db = Chroma(persist_directory=SETTINGS["db_path"], embedding_function=embeddings)
        
        # --- HYBRID RETRIEVAL LOGIC ---
        # We split the search k-value: half for history, half for source
        k_split = max(k_val // 2, 1)
        
        # 1. Fetch Current Source Code chunks
        status.write("🔍 Fetching Current Source Code...")
        src_docs = vector_db.similarity_search(
            user_input, 
            k=k_split, 
            filter={"hash": "LATEST"}
        )
        
        # 2. Fetch Historical Commit chunks
        status.write("📜 Fetching Historical Git Diffs...")
        hist_docs = vector_db.similarity_search(
            user_input, 
            k=k_split, 
            filter={"hash": {"$ne": "LATEST"}}
        )
        
        # Combine them manually to ensure the LLM sees both
        combined_context = src_docs + hist_docs
        
        # Define the Forensic Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Senior Forensic Auditor. 
            Your context contains two types of data:
            1. 'Current Source Code': The actual code currently in the files (Metadata: hash=LATEST).
            2. 'Historical Diffs': The changes made in past commits (+/- lines).
            
            TASK:
            - Scan the context for 'FILE_PATH' to find the CURRENT implementation.
            - Scan the context for 'COMMIT_ID' to find the HISTORICAL fix.
            - Compare them. Specifically check if the logic from the Historical Diff is present in the Current Source.
            - If the 'Current Source Code' is missing the logic from the 'Historical Diff', report a regression.
            
            Context:
            {context}"""),
            ("human", "{input}")
        ])

        status.write("🧠 Synthesizing Forensic Analysis...")
        # We skip the standard 'retriever' and pass our combined_context directly
        document_chain = create_stuff_documents_chain(llm, prompt)
        
        # Since we aren't using create_retrieval_chain (which handles retrieval for us),
        # we invoke the document chain directly with our manually gathered context.
        response_text = document_chain.invoke({
            "input": user_input,
            "context": combined_context
        })
        
        # Wrap in a dictionary to keep consistency with your UI code
        response = {
            "answer": response_text,
            "context": combined_context
        }
        
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
                # Identify the type of document
                is_source = doc.metadata.get("hash") == "LATEST"
                icon = "📄 [CURRENT SOURCE]" if is_source else "📜 [GIT HISTORY]"
                color = "blue" if is_source else "green"
                
                st.markdown(f"**Source {i+1}: {icon}**")
                st.code(doc.page_content[:800], language="diff" if not is_source else "python")
                st.divider()