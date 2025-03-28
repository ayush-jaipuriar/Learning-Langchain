"""
Text Splitting with LangChain

This script demonstrates how to use text splitters in LangChain
to divide documents into smaller chunks for better processing by LLMs.
"""

from dotenv import load_dotenv
import os
import sys
from typing import List

# Import document loaders
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def load_pdf_document(file_path: str) -> List[Document]:
    """Load content from a PDF file."""
    print(f"\n📚 Loading PDF file: {file_path}")
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    print(f"  ✅ Loaded {len(docs)} document(s) (pages)")
    return docs


def load_text_document(file_path: str) -> str:
    """Load content from a text file as a single string."""
    print(f"\n📄 Loading text file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"  ✅ Loaded text file with {len(text)} characters")
    return text


def split_documents(docs: List[Document], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Document]:
    """Split documents into smaller chunks using RecursiveCharacterTextSplitter."""
    print(f"\n✂️ Splitting {len(docs)} document(s) into chunks")
    print(f"  - Chunk size: {chunk_size} characters")
    print(f"  - Chunk overlap: {chunk_overlap} characters")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    split_docs = text_splitter.split_documents(docs)
    print(f"  ✅ Created {len(split_docs)} chunks")
    return split_docs


def split_text(text: str, chunk_size: int = 100, chunk_overlap: int = 20) -> List[Document]:
    """Split text into smaller chunks and convert to Document objects."""
    print(f"\n✂️ Splitting text into chunks")
    print(f"  - Chunk size: {chunk_size} characters")
    print(f"  - Chunk overlap: {chunk_overlap} characters")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    documents = text_splitter.create_documents([text])
    print(f"  ✅ Created {len(documents)} chunks")
    return documents


def print_document_chunks(chunks: List[Document], num_to_print: int = 2) -> None:
    """Print details about document chunks to demonstrate chunking and overlap."""
    print("\n📑 Document Chunks Sample:")
    
    for i in range(min(num_to_print, len(chunks))):
        print(f"\n  Chunk {i+1}:")
        print(f"  - Content length: {len(chunks[i].page_content)} characters")
        print(f"  - Content preview: {chunks[i].page_content[:100]}...")
        print(f"  - Metadata: {chunks[i].metadata}")
    
    # If we have at least two chunks, demonstrate the overlap
    if len(chunks) >= 2:
        chunk1 = chunks[0].page_content
        chunk2 = chunks[1].page_content
        
        # Find the overlap (the end of chunk1 should match the start of chunk2)
        for i in range(min(100, len(chunk1))):
            overlap_len = len(chunk1) - i
            if chunk2.startswith(chunk1[-overlap_len:]):
                print(f"\n  ✅ Found overlap of {overlap_len} characters between chunks 1 and 2")
                print(f"  - Overlapping text: '{chunk1[-overlap_len:overlap_len+50]}...'")
                break


def main():
    # Load environment variables
    load_dotenv()
    
    # Example 1: Splitting a PDF document
    pdf_path = "data/pdf/attention.pdf"
    if os.path.exists(pdf_path):
        # Load PDF
        pdf_docs = load_pdf_document(pdf_path)
        
        # Split PDF documents with default settings (chunk_size=500, chunk_overlap=50)
        pdf_chunks = split_documents(pdf_docs)
        
        # Print sample chunks
        if pdf_chunks:
            print_document_chunks(pdf_chunks)
    else:
        print(f"⚠️ PDF file not found: {pdf_path}")
    
    # Example 2: Splitting a text file
    text_path = "data/text/speech.txt"
    if os.path.exists(text_path):
        # Load text as a single string
        speech_text = load_text_document(text_path)
        
        # Split text with smaller chunk size (chunk_size=100, chunk_overlap=20)
        text_chunks = split_text(speech_text, chunk_size=100, chunk_overlap=20)
        
        # Print sample chunks
        if text_chunks:
            print_document_chunks(text_chunks)
    else:
        print(f"⚠️ Text file not found: {text_path}")
    
    print("\n✅ Text splitting examples completed")


if __name__ == "__main__":
    main() 