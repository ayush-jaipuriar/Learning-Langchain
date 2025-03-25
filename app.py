from dotenv import load_dotenv
import os
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def main():
    # Load environment variables
    load_dotenv()
    
    # Verify environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    langchain_project = os.getenv("LANGCHAIN_PROJECT")
    
    print("\nEnvironment Configuration:")
    print(f"OpenAI API Key configured: {'Yes' if openai_api_key else 'No'}")
    print(f"LangSmith API Key configured: {'Yes' if langchain_api_key else 'No'}")
    print(f"LangChain Project: {langchain_project}")
    
    # Test LangChain setup
    if openai_api_key:
        try:
            # Initialize LLM
            llm = OpenAI(temperature=0.7)
            
            # Create a simple prompt template
            prompt = PromptTemplate.from_template("Tell me a short joke about {topic}.")
            
            # Create a chain
            chain = prompt | llm | StrOutputParser()
            
            # Test the chain
            print("\nTesting LangChain:")
            response = chain.invoke({"topic": "programming"})
            print(f"Response: {response}")
            
            print("\n✅ LangChain setup successful!")
            
        except Exception as e:
            print(f"\n❌ Error testing LangChain: {str(e)}")
    else:
        print("\n❌ Please configure your OpenAI API key in the .env file")

if __name__ == "__main__":
    main() 