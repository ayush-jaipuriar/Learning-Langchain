# LangChain Learning Project

This project demonstrates the setup and usage of LangChain, LangSmith, and LangServe for building AI-powered applications.

## Setup Instructions

1. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Add your API keys:
  - OpenAI API key from [OpenAI Platform](https://platform.openai.com)
  - LangSmith API key from [LangSmith](https://smith.langchain.com)

4. Verify installation:
```bash
python app.py
```

## Project Structure

```
project/
│
├── .env                # Environment variables
├── requirements.txt    # Dependencies
├── app.py             # Main application file
├── notebooks/         # Jupyter notebooks
└── data/             # Datasets and files
```

## Features

- LangChain integration for LLM-based applications
- LangSmith monitoring and debugging
- LangServe deployment capabilities
- OpenAI API integration
- Vertex AI-only LangGraph chatbot (SuperBot) demonstrating reducers and streaming

## Development

To start development:

1. Launch Jupyter Notebook:
```bash
jupyter notebook
```

2. Open notebooks in the `notebooks/` directory for examples and experiments.

## Monitoring

Use LangSmith dashboard to monitor your application:
1. Log in to [LangSmith](https://smith.langchain.com)
2. View traces, debug issues, and analyze performance

## OpenAI Embeddings and FAISS Example

This project includes an example script `openai_faiss_pipeline.py` that demonstrates how to:

1.  **Load Data:** Reads text data from a file (currently `customer_data.csv`, containing synthetic customer information).
2.  **Split Data:** Uses `CharacterTextSplitter` to break the loaded text into smaller chunks suitable for embedding.
3.  **Generate Embeddings:** Utilizes `OpenAIEmbeddings` to convert text chunks into vector embeddings using OpenAI's API.
4.  **Build Vector Store:** Creates a `FAISS` vector store from the documents and their embeddings, allowing for efficient similarity searches.
5.  **Query Data:** Shows examples of querying the vector store using various methods (`similarity_search`, `as_retriever`, `similarity_search_with_score`, `similarity_search_by_vector`).
6.  **Save/Load Index:** Demonstrates how to save the created FAISS index locally and load it back for later use.

### Running the Example

1.  Ensure you have installed all dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Set your OpenAI API key as an environment variable:
    ```bash
    # Windows (Command Prompt)
    set OPENAI_API_KEY=your_api_key_here
    
    # Windows (PowerShell)
    $env:OPENAI_API_KEY="your_api_key_here"
    
    # macOS/Linux
    export OPENAI_API_KEY=your_api_key_here
    ```
    *Alternatively, manage keys using a `.env` file and the `python-dotenv` package if preferred.*

3.  Run the script:
    ```bash
    python openai_faiss_pipeline.py
    ```

    The script will process `customer_data.csv` (creating a dummy file if it doesn't exist), build the FAISS index, perform sample queries, and save the index to the `faiss_index_openai` folder.

## Next Steps

1. Explore LangChain components:
   - Prompt Templates
   - Models
   - Output Parsers
2. Build sample applications
3. Deploy with LangServe 

## SuperBot Vertex LangGraph Chatbot

1. Copy `configs/superbot.env.example` to `.env` and populate your `GCP_PROJECT_ID`, `GCP_LOCATION`, and preferred `VERTEX_MODEL` (ADC authentication is required; run `gcloud auth application-default login`).
2. Install dependencies if you have not already done so: `pip install -r requirements.txt`.
3. Run a one-shot conversation from the terminal:
   ```bash
   python super_bot.py --prompt "Hello SuperBot!"
   ```
4. Explore streaming behavior:
   ```bash
   python super_bot.py --mode stream --stream-mode values --prompt "Explain reducer semantics"
   ```
5. Open `notebooks/chatbot.ipynb` for a guided walkthrough covering state schema, graph wiring, invoke, and streaming modes.