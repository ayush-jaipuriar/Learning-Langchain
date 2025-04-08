import os
# Note: No dotenv needed for standard GCP authentication (uses ADC)
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Import Google Vertex AI components
from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
import time

# --- Configuration ---
TARGET_URL = "https://docs.smith.langchain.com/overview" # Same example URL
# Use a different path for Vertex index to avoid conflicts with OpenAI version
FAISS_INDEX_PATH = "faiss_index_vertex"

# Google Cloud Configuration (Replace with your actual project details if needed)
GCP_PROJECT_ID = "langchain-456212"
GCP_LOCATION = "us-central1"

# Embedding and LLM model names
VERTEX_EMBEDDING_MODEL = "text-embedding-004"
VERTEX_LLM_MODEL = "gemini-2.0-flash-lite-001"

def main():
    # --- 1. Setup & Authentication Note ---
    start_time = time.time()
    print("--- Starting Google Vertex AI RAG Pipeline ---")
    print(f"Using GCP Project: {GCP_PROJECT_ID}, Location: {GCP_LOCATION}")
    print("Note: This script relies on Google Cloud Application Default Credentials (ADC).")
    print("Run `gcloud auth application-default login` if running locally and not authenticated.")

    # You might want to add a check for ADC availability here in a production scenario
    # E.g., by trying to list models or using google.auth.default()

    # --- Initialize Google Vertex AI Components ---
    try:
        embeddings = VertexAIEmbeddings(
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION,
            model_name=VERTEX_EMBEDDING_MODEL
        )
        llm = ChatVertexAI(
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION,
            model_name=VERTEX_LLM_MODEL,
            temperature=0.2,
            max_output_tokens=1024
        )
        print(f"✅ Initialized Vertex AI Embeddings ({VERTEX_EMBEDDING_MODEL}) and Chat Model ({VERTEX_LLM_MODEL}).")
    except Exception as e:
        print(f"❌ Error initializing Vertex AI components: {e}")
        print("   Ensure you are authenticated (`gcloud auth application-default login`) and the models/API are enabled in your project.")
        return

    # --- 2. Vector Store Handling (Load or Create) ---
    vectorstore_db = None
    if os.path.exists(FAISS_INDEX_PATH):
        print(f"💾 Loading existing FAISS index from: {FAISS_INDEX_PATH}")
        try:
            vectorstore_db = FAISS.load_local(
                FAISS_INDEX_PATH,
                embeddings, # Use Vertex Embeddings object here
                allow_dangerous_deserialization=True
            )
            print("✅ FAISS index loaded successfully.")
        except Exception as e:
            print(f"⚠️ Warning: Failed to load existing index. Will re-create. Error: {e}")
            vectorstore_db = None

    if vectorstore_db is None:
        print(f"🌐 Ingesting and processing data from: {TARGET_URL}")

        # --- 3. Data Ingestion (WebBaseLoader) ---
        print("   Loading website content...")
        try:
            loader = WebBaseLoader(TARGET_URL)
            docs = loader.load()
            print(f"   Loaded {len(docs)} document(s) from the URL.")
        except Exception as e:
            print(f"❌ Error loading URL {TARGET_URL}: {e}")
            return

        # --- 4. Text Splitting (RecursiveCharacterTextSplitter) ---
        print("   Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunked_documents = text_splitter.split_documents(docs)
        print(f"   Split into {len(chunked_documents)} chunks.")

        # --- 5. Vector Store Creation (FAISS with Vertex Embeddings) ---
        print(f"   Creating FAISS vector store with Vertex AI ({VERTEX_EMBEDDING_MODEL}) embeddings...")
        try:
            vectorstore_db = FAISS.from_documents(
                documents=chunked_documents,
                embedding=embeddings # Pass the VertexAIEmbeddings instance
            )
            print("   ✅ FAISS vector store created.")

            # Save the newly created index
            print(f"   💾 Saving FAISS index to: {FAISS_INDEX_PATH}")
            vectorstore_db.save_local(FAISS_INDEX_PATH)
            print("   ✅ FAISS index saved.")

        except Exception as e:
            print(f"❌ Error creating or saving FAISS index using Vertex AI Embeddings: {e}")
            print("   This might indicate an issue with Vertex AI API access, quotas, or the embedding model.")
            return

    # --- 6. Prompt Template Setup (No Change) ---
    prompt_template_str = """Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}

Answer:"""
    prompt = ChatPromptTemplate.from_template(prompt_template_str)
    print("✅ Prompt template created.")

    # --- 7. Chain Construction (No Change in Logic) ---
    print("🛠️  Building LangChain retrieval chain...")
    document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    retriever = vectorstore_db.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=document_chain)
    print("✅ Retrieval chain created successfully.")

    # --- 8. Chain Invocation (Ask a Question) ---
    print("\n💬 Asking a question to the Vertex AI RAG pipeline...")
    user_question = "What is LangSmith?" # Same example question
    print(f"   Question: {user_question}")

    try:
        invocation_start_time = time.time()
        response = retrieval_chain.invoke({"input": user_question})
        invocation_end_time = time.time()

        print("\n✅ Response received.")
        print("\n--- Generated Answer (via Vertex AI LLM) ---")
        print(response.get("answer", "⚠️ No answer generated."))
        print("-------------------------------------------")

        # Optional: Display retrieved context
        # print("\n--- Context Used ---")
        # ... (context display logic same as before)
        # print("--------------------")

        print(f"⏱️ Answer generation took: {invocation_end_time - invocation_start_time:.2f} seconds")

    except Exception as e:
        print(f"❌ Error during chain invocation with Vertex AI LLM: {e}")

    end_time = time.time()
    print(f"\n🏁 Pipeline finished in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main() 