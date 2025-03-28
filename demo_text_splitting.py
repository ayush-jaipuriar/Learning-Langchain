"""
Demo Text Splitting

This script demonstrates text splitting functionality from the LangChain library.
Run this to see how documents are divided into smaller chunks.
"""

from text_splitting import (
    load_pdf_document,
    load_text_document,
    split_documents,
    split_text,
    print_document_chunks
)
import os


def main():
    print("=" * 50)
    print("Text Splitting Demo")
    print("=" * 50)
    
    # Check paths
    pdf_path = "data/pdf/attention.pdf"
    text_path = "data/text/speech.txt"
    
    # Demo 1: PDF Splitting
    if os.path.exists(pdf_path):
        print("\n📚 Demo 1: Splitting a PDF Document")
        print("-" * 50)
        
        # Load PDF document
        pdf_docs = load_pdf_document(pdf_path)
        
        # Split with 500 character chunks and 50 character overlap
        pdf_chunks = split_documents(pdf_docs, chunk_size=500, chunk_overlap=50)
        
        # Show results
        print_document_chunks(pdf_chunks)
    else:
        print(f"\n⚠️ PDF file not found: {pdf_path}")
        print("Download a sample PDF using: curl -o data/pdf/attention.pdf https://arxiv.org/pdf/1706.03762.pdf")
    
    # Demo 2: Text Splitting
    if os.path.exists(text_path):
        print("\n📄 Demo 2: Splitting a Text File")
        print("-" * 50)
        
        # Load text file
        speech_text = load_text_document(text_path)
        
        # Split with 100 character chunks and 20 character overlap
        text_chunks = split_text(speech_text, chunk_size=100, chunk_overlap=20)
        
        # Show results
        print_document_chunks(text_chunks)
    else:
        print(f"\n⚠️ Text file not found: {text_path}")
    
    print("\n✅ Demo completed. Check TEXT_SPLITTING.md for more information.")


if __name__ == "__main__":
    main() 