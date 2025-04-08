import os
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
import time # To measure time taken

# --- Configuration ---
TARGET_URL = "https://docs.smith.langchain.com/overview" # Example URL, relevant to LangSmith
FAISS_INDEX_PATH = "faiss_index_web" # Folder to save/load the index

def main():
    # --- 1. Setup: Load Environment Variables ---
    start_time = time.time()
    load_dotenv()
    print("--- Starting Website RAG Pipeline ---")

    # Verify OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please configure it in your .env file or environment.")
        return
    else:
        print("✅ OpenAI API Key found.")

    # --- Initialize OpenAI Components ---
    embeddings = OpenAIEmbeddings()
    llm = ChatOpenAI(model="gpt-4o-mini") # Using a cost-effective model
    print(f"✅ Initialized OpenAI Embeddings and Chat Model ({llm.model_name}).")


    # --- 2. Vector Store Handling (Load or Create) ---
    vectorstore_db = None
    if os.path.exists(FAISS_INDEX_PATH):
        print(f"💾 Loading existing FAISS index from: {FAISS_INDEX_PATH}")
        try:
            vectorstore_db = FAISS.load_local(
                FAISS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True # Required for FAISS loading
            )
            print("✅ FAISS index loaded successfully.")
        except Exception as e:
            print(f"⚠️ Warning: Failed to load existing index. Will re-create. Error: {e}")
            vectorstore_db = None # Ensure it's None if loading failed

    if vectorstore_db is None:
        print(f"🌐 Ingesting and processing data from: {TARGET_URL}")

        # --- 3. Data Ingestion (WebBaseLoader) ---
        print("   Loading website content...")
        loader = WebBaseLoader(TARGET_URL)
        docs = loader.load()
        print(f"   Loaded {len(docs)} document(s) from the URL.")

        # --- 4. Text Splitting (RecursiveCharacterTextSplitter) ---
        print("   Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunked_documents = text_splitter.split_documents(docs)
        print(f"   Split into {len(chunked_documents)} chunks.")

        # --- 5. Vector Store Creation (FAISS) ---
        print("   Creating FAISS vector store with OpenAI embeddings...")
        try:
            vectorstore_db = FAISS.from_documents(
                documents=chunked_documents,
                embedding=embeddings
            )
            print("   ✅ FAISS vector store created.")

            # Save the newly created index
            print(f"   💾 Saving FAISS index to: {FAISS_INDEX_PATH}")
            vectorstore_db.save_local(FAISS_INDEX_PATH)
            print("   ✅ FAISS index saved.")

        except Exception as e:
            print(f"❌ Error creating or saving FAISS index: {e}")
            return # Cannot proceed without a vector store

    # --- 6. Prompt Template Setup ---
    prompt_template_str = """Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}

Answer:"""
    prompt = ChatPromptTemplate.from_template(prompt_template_str)
    print("✅ Prompt template created.")

    # --- 7. Chain Construction ---
    print("🛠️  Building LangChain retrieval chain...")
    # Create the document chain (stuffs context into prompt)
    document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

    # Create the retriever from the vector store
    retriever = vectorstore_db.as_retriever()

    # Create the final retrieval chain
    retrieval_chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=document_chain)
    print("✅ Retrieval chain created successfully.")

    # --- 8. Chain Invocation (Ask a Question) ---
    print("\n💬 Asking a question to the RAG pipeline...")
    user_question = "What is LangSmith?" # Example question relevant to the URL
    print(f"   Question: {user_question}")

    try:
        invocation_start_time = time.time()
        response = retrieval_chain.invoke({"input": user_question})
        invocation_end_time = time.time()

        print("\n✅ Response received.")
        print("\n--- Generated Answer ---")
        print(response.get("answer", "⚠️ No answer generated."))
        print("------------------------")

        # Optional: Display retrieved context
        # print("\n--- Context Used ---")
        # context_docs = response.get("context", [])
        # if context_docs:
        #     for i, doc in enumerate(context_docs):
        #         print(f"Chunk {i+1} (Source: {doc.metadata.get('source', 'N/A')}):\n{doc.page_content}\n---")
        # else:
        #     print("   No context documents were retrieved.")
        # print("--------------------")

        print(f"⏱️ Answer generation took: {invocation_end_time - invocation_start_time:.2f} seconds")

    except Exception as e:
        print(f"❌ Error during chain invocation: {e}")

    end_time = time.time()
    print(f"\n🏁 Pipeline finished in {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    main() 