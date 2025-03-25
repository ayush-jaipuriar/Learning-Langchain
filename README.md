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

## Next Steps

1. Explore LangChain components:
   - Prompt Templates
   - Models
   - Output Parsers
2. Build sample applications
3. Deploy with LangServe 