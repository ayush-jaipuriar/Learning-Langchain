import json
import requests
import os
from langchain_text_splitters import RecursiveJsonSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv

# Load environment variables (optional, for API keys)
load_dotenv()

# --- Step 1: Get Tools Ready (Imports are above) ---

# --- Step 2: Fetch the JSON Data from the API ---

# Using OpenAI's models endpoint as an example.
# NOTE: This requires an API key set as an environment variable OPENAI_API_KEY
# or passed in headers. If not configured, the request might fail.
api_url = "https://api.openai.com/v1/models"
api_key = os.getenv("OPENAI_API_KEY")
headers = {
    "Authorization": f"Bearer {api_key}"
}

print(f"Fetching data from: {api_url}")
try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    json_data = response.json()
    print("Successfully fetched and parsed JSON data.")
    # print("Full JSON data:")
    # print(json.dumps(json_data, indent=2)) # Optional: print the full data

except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    print("Proceeding with sample JSON data for demonstration purposes.")
    # Fallback sample data if API fails
    json_data = {
        "object": "list",
        "data": [
            {"id": "gpt-4", "object": "model", "created": 1677610602, "owned_by": "openai"},
            {"id": "text-davinci-003", "object": "model", "created": 1669599635, "owned_by": "openai-internal"},
            {"id": "gpt-3.5-turbo", "object": "model", "created": 1677610602, "owned_by": "openai"},
            {"id": "dalle", "object": "model", "created": 1677610602, "owned_by": "openai"},
            {"id": "whisper-1", "object": "model", "created": 1677610602, "owned_by": "openai-internal"},
            # Potentially many more entries...
             {"id": "text-embedding-ada-002", "object": "model", "created": 1677610602, "owned_by": "openai-internal", "long_description": "This is a very long description string designed to potentially exceed the chunk size by itself, demonstrating that the splitter does not split long string values, only the JSON structure around them. It keeps going and going and going to ensure it's sufficiently long for testing purposes across various chunk sizes. Adding more text just in case. Still more text needed. Almost there perhaps. Okay, this should be enough text now to make the point clear about string values not being split internally."},

        ]
    }


# --- Step 3: Initialize the JSON Splitter ---
print("\n--- Initializing RecursiveJsonSplitter ---")
json_splitter = RecursiveJsonSplitter(max_chunk_size=300)
print(f"Splitter configured with max_chunk_size={json_splitter.max_chunk_size}")

# --- Step 4: Split the JSON (Method 1: Get Raw JSON Chunks) ---
print("\n--- Method 1: Splitting into Raw JSON Chunks (split_json) ---")
# This returns Python dictionaries/lists
json_chunks = json_splitter.split_json(json_data=json_data)

print(f"Original JSON resulted in {len(json_chunks)} JSON chunks.")
print("First 3 JSON chunks:")
for i, chunk in enumerate(json_chunks):
    if i < 3:
        print(f"--- Chunk {i+1} ---")
        # Use json.dumps for pretty printing the dictionary/list chunk
        print(json.dumps(chunk, indent=2))
    else:
        break

# --- Step 5: Split the JSON (Method 2: Get LangChain Documents) ---
print("\n--- Method 2: Splitting into LangChain Documents ---")
# First, get the text chunks using split_text (demonstrated in Step 6, known to work)
texts_for_docs = json_splitter.split_text(json_data=json_data)

# Now, manually create Document objects from these text chunks
docs = [Document(page_content=chunk) for chunk in texts_for_docs]


print(f"Original JSON resulted in {len(docs)} Document objects.")
print("First 3 Documents:")
for i, doc in enumerate(docs):
    if i < 3:
        print(f"--- Document {i+1} ---")
        print(doc) # Document object has a nice __repr__
    else:
        break

# --- Step 6: Split the JSON (Method 3: Get Raw Text Strings) ---
print("\n--- Method 3: Splitting into Text Strings (split_text) ---")
# This returns strings, where each string is a JSON chunk
texts = json_splitter.split_text(json_data=json_data)

print(f"Original JSON resulted in {len(texts)} text chunks.")
print("First 3 Text chunks:")
for i, text_chunk in enumerate(texts):
    if i < 3:
        print(f"--- Text Chunk {i+1} ---")
        print(text_chunk)
    else:
        break

# --- Step 7: Conclusion ---
print("\n--- End of Demonstration ---")
print("Finished demonstrating RecursiveJsonSplitter methods.") 