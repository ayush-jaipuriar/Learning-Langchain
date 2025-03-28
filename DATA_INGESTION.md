# Data Ingestion with LangChain

This document explains how to use LangChain's document loaders to ingest data from various sources.

## Overview

LangChain provides a wide variety of document loaders that can read data from different sources and convert them into a common format for further processing. This is an essential step for any LLM-based application that needs to work with external data.

## Key Concepts

### Document Structure

In LangChain, a document consists of:
- **page_content**: The actual text content
- **metadata**: Information about the document (source, page number, etc.)

This structure helps track the origin of information, especially when working with multiple sources.

### Document Loaders

LangChain provides loaders for many data sources:

1. **TextLoader**: For plain text files
2. **PyPDFLoader**: For PDF documents
3. **WebBaseLoader**: For web pages
4. **ArxivLoader**: For research papers
5. **WikipediaLoader**: For Wikipedia articles
6. **Many more**: CSVs, Databases, APIs, etc.

## Examples

### Loading Text Files

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("data/text/speech.txt")
documents = loader.load()
```

### Loading PDF Files

```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("data/pdf/sample.pdf")
documents = loader.load()  # Each page becomes a separate document
```

### Loading Web Pages

```python
from langchain_community.document_loaders import WebBaseLoader
from bs4 import SoupStrainer

# Basic loading
loader = WebBaseLoader("https://example.com")

# Advanced with specific element extraction
advanced_loader = WebBaseLoader(
    web_paths=["https://example.com"],
    bs_kwargs={"parse_only": SoupStrainer(["h1", "h2", "p"])}
)
documents = loader.load()
```

### Loading Research Papers

```python
from langchain_community.document_loaders import ArxivLoader

loader = ArxivLoader(query="1706.03762", load_max_docs=1)
documents = loader.load()
```

### Loading Wikipedia Articles

```python
from langchain_community.document_loaders import WikipediaLoader

loader = WikipediaLoader(query="Generative AI", load_max_docs=1)
documents = loader.load()
```

## Next Steps

After loading documents, you typically want to:

1. **Split text into chunks**: Documents are often too large for direct LLM processing
   ```python
   from langchain.text_splitter import RecursiveCharacterTextSplitter
   
   text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
   split_docs = text_splitter.split_documents(documents)
   ```

2. **Create embeddings**: Convert text chunks into vector representations
   ```python
   from langchain_openai import OpenAIEmbeddings
   
   embeddings = OpenAIEmbeddings()
   document_embeddings = embeddings.embed_documents([doc.page_content for doc in split_docs])
   ```

3. **Store in vector database**: For efficient retrieval
   ```python
   from langchain_community.vectorstores import Chroma
   
   vectorstore = Chroma.from_documents(split_docs, embeddings)
   ```

## Resources

- [LangChain Documentation](https://python.langchain.com/docs/modules/data_connection/)
- [Jupyter Notebooks](notebooks/04_Data_Ingestion.ipynb) in this project
- [Script Examples](data_ingestion.py) in this project 