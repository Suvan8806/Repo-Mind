from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from config import SETTINGS

def start_chat():
    # 1. Initialize models
    _b = SETTINGS["ollama_base_url"]
    llm = OllamaLLM(model=SETTINGS["llm_model"], base_url=_b)
    embeddings = OllamaEmbeddings(model=SETTINGS["embed_model"], base_url=_b)

    # 2. Load the Memory
    vector_db = Chroma(
        persist_directory=SETTINGS["db_path"], 
        embedding_function=embeddings
    )
    # 'k': 6 tells the AI to grab the 6 most relevant pieces of your doc
    retriever = vector_db.as_retriever(search_kwargs={"k": 6})

    # 3. Define the Prompt (This is the modern way)
    system_prompt = (
        "You are a professional assistant. You MUST answer the question using ONLY the provided context."
        "If the answer is not contained within the context, strictly say 'I do not have enough information in the documents to answer that.'"
        "Do not use outside knowledge about companies or people."
        "\n\n"
        "CONTEXT:\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    # 4. Create the modern chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    print("\n--- 🤖 MODERN AI AGENT READY ---")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]: break

        print("Thinking...")
        # The modern chain uses 'input' as the key
        response = rag_chain.invoke({"input": user_input})
        
        print(f"\nAI: {response['answer']}")
        
        # Show sources
        sources = set([doc.metadata.get('source', 'Unknown') for doc in response['context']])
        print(f"(Sources: {list(sources)})")

if __name__ == "__main__":
    start_chat()