# Text Splitting with LangChain

This document explains how to use LangChain's text splitters to divide documents into smaller chunks for better processing by Large Language Models (LLMs).

## Why Split Text?

LLMs have a limited context window (maximum token size they can process):
- GPT-3.5: ~4,096 tokens
- GPT-4: ~8,192 tokens (or more in newer versions)
- Claude: ~100,000 tokens

When dealing with long documents, we need to split them into smaller chunks that fit within these limits. This process is called "chunking" or "text splitting."

## RecursiveCharacterTextSplitter

LangChain provides several text splitters, but the most versatile is `RecursiveCharacterTextSplitter`. This splitter:

1. Attempts to split on a list of separators in order of preference: `["\n\n", "\n", " ", ""]`
2. Preserves the most semantic meaning by keeping related text together
3. Allows configuring chunk size and overlap

## Installation

```bash
# Install the text splitters package
pip install langchain-text-splitters

# Or, install from requirements.txt
pip install -r requirements.txt
```

## Basic Usage

### Splitting Documents

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

# 1. Load the document
loader = PyPDFLoader("attention.pdf")
docs = loader.load()

# 2. Initialize the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Maximum characters per chunk
    chunk_overlap=50,  # Characters that overlap between chunks
)

# 3. Split the documents
split_docs = text_splitter.split_documents(docs)

# 4. View results
print(f"Original documents: {len(docs)}")
print(f"Split into chunks: {len(split_docs)}")
print(f"First chunk: {split_docs[0].page_content[:100]}...")
```

### Splitting Plain Text

For plain text input:

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. Load text
with open("speech.txt", "r") as f:
    speech = f.read()

# 2. Initialize the text splitter (smaller chunks for this example)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20
)

# 3. Convert text into document chunks
text_chunks = text_splitter.create_documents([speech])

# 4. View results
print(f"Original text length: {len(speech)} characters")
print(f"Split into {len(text_chunks)} chunks")
```

## Key Parameters

- **chunk_size**: Maximum size of each chunk in characters
  - Smaller chunks (100-200) for shorter texts
  - Larger chunks (500-1000) for longer documents

- **chunk_overlap**: Number of characters that overlap between consecutive chunks
  - Typically 10-20% of chunk_size
  - Ensures that no information is lost at chunk boundaries
  - Helps maintain context between chunks

- **separators**: List of characters to use as separators when splitting text
  - Default: `["\n\n", "\n", " ", ""]`
  - Tries each separator in order until the chunk is small enough

## Understanding Overlapping Chunks

Overlapping ensures that context isn't lost between chunks:

```
Chunk 1: "The University of Toronto is known for its research..."
Chunk 2: "Toronto is known for its research in artificial intelligence..."
```

The phrase "Toronto is known for its research" appears in both chunks, maintaining context.

## Visualizing the Splitting Process

```
Original Text: "The quick brown fox jumps over the lazy dog. This is a second sentence."

With chunk_size=20, chunk_overlap=5:

Chunk 1: "The quick brown fox"
Chunk 2: "brown fox jumps over"
Chunk 3: "jumps over the lazy"
Chunk 4: "the lazy dog. This"
Chunk 5: "dog. This is a"
Chunk 6: "is a second sentence."
```

## Advanced Techniques

### Custom Separators

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n## ", "\n### ", "\n#### ", "\n", " ", ""]
)
```

This is particularly useful for Markdown documents to split on headings.

### Length Function

You can customize how the length of text is calculated:

```python
# Count tokens instead of characters
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,  # now in tokens rather than characters
    chunk_overlap=50,
    length_function=lambda text: len(tokenizer.encode(text))
)
```

## Next Steps

After splitting documents:

1. Convert chunks to embeddings using an embedding model
2. Store in a vector database for efficient retrieval
3. Implement a retrieval system to fetch relevant chunks based on queries

## Resources

- [Text Splitting Script](text_splitting.py) in this project
- [LangChain Text Splitters Documentation](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [Jupyter Notebooks](notebooks/05_Text_Splitting.ipynb) in this project 