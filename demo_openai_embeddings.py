import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter # Corrected import
from langchain_community.vectorstores import Chroma

# --- Phase 1: Setting the Stage ---

# 3 & 5: Load the API Key into Your Script
print("Loading environment variables...")
# Use find_dotenv to locate the .env file automatically
loaded = load_dotenv(find_dotenv())
if not loaded:
    print("Warning: .env file not found. Ensure OPENAI_API_KEY is set in your environment.")
else:
    print(".env file loaded successfully.")

# Check if the key is actually loaded
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment variables.")
    print("Please ensure it is set in your .env file or environment.")
    print("Proceeding without API key - some steps might fail.")

# Input document file
document_path = "speech.txt"

if not os.path.exists(document_path):
    print(f"Error: Input file '{document_path}' not found.")
    print("Please create the file or ensure it's in the correct directory.")
    exit()

# --- Phase 2: Coding Time - Embedding with OpenAI ---

# 6: Initialize the OpenAI Embeddings Model
print("\nInitializing OpenAI Embeddings model...")
# Using the model and dimensions mentioned in the example
model_name = "text-embedding-3-large"
dims = 1024
embeddings = None # Initialize to None
if api_key: # Only try if API key was found
    try:
        embeddings = OpenAIEmbeddings(model=model_name, dimensions=dims)
        print(f"Using model: {model_name} with dimensions: {dims}")
    except Exception as e:
        print(f"Error initializing OpenAIEmbeddings: {e}")
        print("Check your OpenAI API key and model availability.")
else:
    print("Skipping embedding model initialization as API key is missing.")

# 7: Test Embedding a Single Piece of Text (Optional)
if embeddings: # Only run if embeddings object was created
    print("\nTesting embedding on a single query...")
    test_text = "This is a test sentence for OpenAI embeddings."
    try:
        query_vector = embeddings.embed_query(test_text)
        print(f"Successfully embedded test query.")
        print(f"Vector Dimension: {len(query_vector)}")
        # print(f"First 5 vector elements: {query_vector[:5]}")
    except Exception as e:
        print(f"Error embedding test query: {e}")
else:
    print("\nSkipping embedding test as model was not initialized.")

# --- Phase 3: Putting it all Together ---

# 8: Load and Split Your Document
print(f"\nLoading document: {document_path}...")
loader = TextLoader(document_path)
documents = loader.load()
print(f"Loaded {len(documents)} document(s). Initially has {len(documents[0].page_content)} characters.")

print("Splitting document into chunks...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
final_documents = text_splitter.split_documents(documents)
print(f"Document split into {len(final_documents)} chunks.")
# print("First chunk content:")
# print(final_documents[0].page_content)

# 9: Embed Chunks and Store in Vector Database (ChromaDB)
# Note: ChromaDB will store data in memory by default.
# To persist, add: persist_directory="./chroma_db_openai"
if embeddings and final_documents: # Only run if we have embeddings and documents
    print("\nCreating Chroma vector store (in-memory)... This may take a moment.")
    try:
        db = Chroma.from_documents(
            documents=final_documents,
            embedding=embeddings # Pass the initialized embedding object
        )
        print("Chroma vector store created successfully.")
    except Exception as e:
        print(f"Error creating Chroma database: {e}")
else:
    print("\nSkipping Chroma DB creation due to missing embeddings or documents.")

# 10: Query Your Vector Store
db = None # Initialize db variable
if embeddings and final_documents: # Only query if we have embeddings and documents
    query = "What did Brutus say about Caesar?" # Example query
    print(f"\nPerforming similarity search for: '{query}'")

    try:
        retrieved_results = db.similarity_search(query)
        print(f"Found {len(retrieved_results)} results.")

        # Print the content of the retrieved documents
        print("\nRetrieved Results:")
        if not retrieved_results:
            print("No relevant documents found.")
        else:
            for i, doc in enumerate(retrieved_results):
                print(f"--- Result {i+1} ---")
                print(doc.page_content)
                print("-" * 20)

    except Exception as e:
        print(f"Error during similarity search: {e}")
else:
    print("\nSkipping similarity search as Chroma DB was not created.")

print("\n--- End of OpenAI Embedding Demonstration ---") 