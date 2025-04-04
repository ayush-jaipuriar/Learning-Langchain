# Get the basic tools ready (now with OpenAI)
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import os

print("Got all the basic tools imported, ready for OpenAI Embeddings!")

# --- Phase 1: Getting Set Up and Loading Data ---

# 1. Set Up Your OpenAI API Key
# Method 1: Load from environment variable (Recommended)
# Make sure you have OPENAI_API_KEY set in your system/terminal environment
# Example (don't put your actual key directly in code like this for real projects):
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE"

# Check if the key is loaded
if "OPENAI_API_KEY" not in os.environ:
    print("\nWARNING: OPENAI_API_KEY environment variable not set!")
    print("Please set the OPENAI_API_KEY environment variable before running.")
    # You might want to add code here to prompt the user or exit,
    # but for now, we'll let it proceed and potentially fail later.
else:
    print("\nOpenAI API Key found in environment variables.")


# 2. Load Your Text Data
# Ensure a file named 'customer_data.csv' exists in the same directory
# For demonstration, let's create a dummy file if it doesn't exist
SPEECH_FILE_PATH = "customer_data.csv"
if not os.path.exists(SPEECH_FILE_PATH):
    print(f"\n'{SPEECH_FILE_PATH}' not found. Creating a dummy file.")
    with open(SPEECH_FILE_PATH, "w") as f:
        f.write("Name,Phone,Address,Interest,Notes\n")
        f.write("Alice Smith,555-0101,123 Oak St Anytown,automobile insurance,Interested in a new policy for her sedan.\n")
        f.write("Bob Johnson,555-0102,456 Maple Ave Springfield,car financing,Looking for loan options for a used vehicle.\n")
        f.write("Charlie Brown,555-0103,789 Pine Ln Gotham,vehicle maintenance,\"Needs schedule for regular car check-ups, oil change.\"\n")
        f.write("Diana Prince,555-0104,101 Birch Rd Metropolis,motorcycle gear,Looking for helmets and jackets.\n")
        f.write("Ethan Hunt,555-0105,202 Cedar Blvd Star City,auto parts,\"Needs new tires for his truck, specifically all-terrain.\"\n")
        f.write("Fiona Glenanne,555-0106,303 Elm St Central City,automobile repair,Complaining about engine noise in her convertible car.\n")
        f.write("George Costanza,555-0107,404 Spruce St Smallville,classic cars,Owns a vintage automobile, looking for restoration experts.\n")
        f.write("Hannah Abbott,555-0108,505 Willow Way Riverdale,electric vehicles,Considering purchase of an EV, asking about charging infrastructure.\n")
        f.write("Ian Malcolm,555-0109,606 Redwood Dr Sunnydale,car detailing,Wants premium cleaning service for his luxury automobile.\n")
        f.write("Jane Doe,555-0110,707 Aspen Ct Fairview,driving lessons,Beginner driver looking for local instructors.\n")

# Point to your text file
loader = TextLoader(SPEECH_FILE_PATH)
# Load the document content
documents = loader.load()

print(f"\nLoaded the document '{SPEECH_FILE_PATH}'. It has {len(documents)} part(s) initially.")

# 3. Split the Document into Chunks
# Initialize the splitter
# Use a smaller chunk size and overlap for better granularity with CSV-like data
text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=50, separator="\n")
# Split the loaded document
docs = text_splitter.split_documents(documents)

print(f"Split the document into {len(docs)} chunks.")

# --- Phase 2: Creating Embeddings and the Vector Store ---

# 4. Initialize Embeddings
# Get the OpenAI embedding engine ready
# It will automatically look for the OPENAI_API_KEY environment variable
embeddings = OpenAIEmbeddings()
print("\nOpenAI Embeddings engine is ready.")

# 5. Create the FAISS Vector Store
print("\nCreating the FAISS vector store using OpenAI Embeddings...")
# Create the vector store by embedding the chunks (via OpenAI API) and indexing them with FAISS
# This step requires the API key to be valid and have quota.
try:
    db = FAISS.from_documents(docs, embeddings)
    print("FAISS vector store created successfully!")

    # --- Phase 3: Querying Your Data ---

    # 6. Basic Similarity Search
    """
    Example Queries and Expected Matches:
    - 'Who needs parts for a motorcycle?'     → Matches: Diana, Xavier
    - 'Customers interested in SUV'           → Matches: Bob, Quinn, Yara
    - 'Looking for truck accessories'         → Matches: Ethan, Sam
    - 'Who asked about insurance?'            → Matches: Alice, Diana, Wendy
    - 'Interest in vintage vehicles'          → Matches: George, Xavier
    - 'Needs repairs'                         → Matches: Fiona, Laura
    - 'Alternative to car ownership'          → Matches: Ursula
    - 'Which customers are from Scranton?'    → Matches: Michael, Oscar
    """
    query = "Which customers are from Scranton?"
    print(f"\nQuerying the vector store with: '{query}' (using OpenAI for query embedding)")
    results = db.similarity_search(query)
    print(f"Found {len(results)} relevant chunks.")
    if results:
        print("\n--- Most Relevant Chunk ---")
        print(results[0].page_content)
        print("---------------------------")

    # 7. Using a Retriever
    retriever = db.as_retriever()
    print("\nConverted FAISS DB to a retriever.")
    retriever_results = retriever.invoke(query)
    print(f"Retriever found {len(retriever_results)} relevant chunks.")
    if retriever_results:
        print("\n--- Most Relevant Chunk (via Retriever) ---")
        print(retriever_results[0].page_content)
        print("-------------------------------------------")

    # 8. Similarity Search with Score
    results_with_scores = db.similarity_search_with_score(query)
    print(f"\nFound {len(results_with_scores)} chunks with scores.")
    if results_with_scores:
        print("\n--- Most Relevant Chunk & Score ---")
        doc, score = results_with_scores[0]
        print(f"Score: {score:.4f} (Lower is better, L2 distance)")
        print(f"Content: {doc.page_content}")
        print("------------------------------------")

    # 9. Similarity Search by Vector
    embedding_vector = embeddings.embed_query(query)
    print("\nGenerated the OpenAI embedding vector for the query.")
    results_by_vector = db.similarity_search_by_vector(embedding_vector)
    print(f"\nFound {len(results_by_vector)} relevant chunks using vector search.")
    if results_by_vector:
        print("\n--- Most Relevant Chunk (via Vector Search) ---")
        print(results_by_vector[0].page_content)
        print("-----------------------------------------------")

    # --- Phase 4: Saving and Loading Your FAISS Index ---

    # 10. Save the Index Locally
    FAISS_INDEX_PATH = "faiss_index_openai"
    db.save_local(FAISS_INDEX_PATH)
    print(f"\nFAISS index (created with OpenAI embeddings) saved locally to folder: '{FAISS_INDEX_PATH}'")

    # 11. Load the Index from Local
    # Get the SAME TYPE of embeddings engine ready again (OpenAI)
    embeddings_for_loading = OpenAIEmbeddings()
    print(f"\nLoading FAISS index from folder: '{FAISS_INDEX_PATH}'")
    # Load the index, making sure to use OpenAIEmbeddings and allow deserialization
    new_db = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings_for_loading, # Must be OpenAIEmbeddings instance
        allow_dangerous_deserialization=True # Necessary for loading FAISS index
    )
    print("FAISS index (created with OpenAI) loaded successfully!")

    # Test the loaded index
    print("\nTesting the loaded index with the same query:")
    loaded_results = new_db.similarity_search(query)
    if loaded_results:
        print("\n--- Most Relevant Chunk (from loaded DB) ---")
        print(loaded_results[0].page_content)
        print("---------------------------------------------")
    else:
        print("Couldn't find results with the loaded index.")

except Exception as e:
    print(f"\nAn error occurred: {e}")
    print("This might be due to a missing/invalid OpenAI API key or network issues.") 