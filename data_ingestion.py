"""
Data Ingestion with LangChain

This script demonstrates how to use various document loaders in LangChain
to ingest data from different sources.
"""

from dotenv import load_dotenv
import os
import sys
from typing import List

# Import document loaders
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    WebBaseLoader,
    WikipediaLoader,
    ArxivLoader
)
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def load_text_file(file_path: str) -> List[Document]:
    """Load content from a text file."""
    print(f"\n📄 Loading text file: {file_path}")
    loader = TextLoader(file_path)
    docs = loader.load()
    print(f"  ✅ Loaded {len(docs)} document(s)")
    return docs


def load_pdf_file(file_path: str) -> List[Document]:
    """Load content from a PDF file."""
    print(f"\n📚 Loading PDF file: {file_path}")
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    print(f"  ✅ Loaded {len(docs)} document(s) (pages)")
    return docs


def load_web_page(url: str) -> List[Document]:
    """Load content from a web page."""
    print(f"\n🌐 Loading web page: {url}")
    loader = WebBaseLoader(url)
    docs = loader.load()
    print(f"  ✅ Loaded {len(docs)} document(s)")
    return docs


def load_wikipedia_article(query: str) -> List[Document]:
    """Load content from Wikipedia."""
    print(f"\n📖 Loading Wikipedia article for: {query}")
    loader = WikipediaLoader(query=query, load_max_docs=1)
    try:
        docs = loader.load()
        print(f"  ✅ Loaded {len(docs)} document(s)")
        return docs
    except Exception as e:
        print(f"  ❌ Error loading Wikipedia article: {e}")
        return []


def load_arxiv_paper(paper_id: str) -> List[Document]:
    """Load content from arXiv."""
    print(f"\n📝 Loading arXiv paper: {paper_id}")
    loader = ArxivLoader(query=paper_id, load_max_docs=1)
    try:
        docs = loader.load()
        print(f"  ✅ Loaded {len(docs)} document(s)")
        return docs
    except Exception as e:
        print(f"  ❌ Error loading arXiv paper: {e}")
        return []


def split_documents(docs: List[Document], chunk_size: int = 1000) -> List[Document]:
    """Split documents into smaller chunks."""
    print(f"\n✂️ Splitting {len(docs)} document(s) into chunks of size {chunk_size}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=200,
        length_function=len
    )
    split_docs = text_splitter.split_documents(docs)
    print(f"  ✅ Created {len(split_docs)} chunks")
    return split_docs


def print_document_sample(doc: Document) -> None:
    """Print a sample of the document content and metadata."""
    print("\n📑 Document Sample:")
    print(f"  Content (first 200 chars): {doc.page_content[:200]}...")
    print(f"  Metadata: {doc.metadata}")


def main():
    # Load environment variables
    load_dotenv()
    
    # Verify environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Warning: OPENAI_API_KEY not set in environment")
    
    # Check for text file
    text_file_path = "data/text/speech.txt"
    if os.path.exists(text_file_path):
        # Load text file
        text_docs = load_text_file(text_file_path)
        if text_docs:
            print_document_sample(text_docs[0])
            
            # Demonstrate splitting
            split_docs = split_documents(text_docs)
            if split_docs:
                print_document_sample(split_docs[0])
    else:
        print(f"⚠️ Text file not found: {text_file_path}")
    
    # Example of loading a web page
    try:
        web_docs = load_web_page("https://python.langchain.com/docs/modules/data_connection/")
        if web_docs:
            print_document_sample(web_docs[0])
    except Exception as e:
        print(f"❌ Error loading web page: {e}")
    
    # Example of loading Wikipedia (requires internet)
    try:
        wiki_docs = load_wikipedia_article("Generative AI")
        if wiki_docs:
            print_document_sample(wiki_docs[0])
    except Exception as e:
        print(f"❌ Error loading Wikipedia: {e}")
    
    print("\n✅ Data ingestion examples completed")


if __name__ == "__main__":
    main() 