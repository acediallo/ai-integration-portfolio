# Social Media Generator

Generate social media content with AI (OpenAI) and manage usage within a daily budget.

## Features

- AI-powered content generation via OpenAI (e.g. gpt-4o-mini)
- Configurable model, daily budget, and cost-per-token settings
- Environment-based configuration with validation
- Structured project layout (templates, data, logs, tests)
- Streamlit-based UI (when implemented)

## Setup

1. **Clone and enter the project**
   ```bash
   cd ai-integration-portfolio/social-media-generator
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   - Copy `.env.example` to `.env`
   - Set `OPENAI_API_KEY` to your OpenAI API key
   - Adjust `MODEL_NAME`, `DAILY_BUDGET`, `LOG_LEVEL` if needed

## Usage

- Run the Streamlit app (when implemented):
  ```bash
  streamlit run app.py
  ```
- Or run the main module:
  ```bash
  python -m app
  ```

Ensure `.env` exists and `OPENAI_API_KEY` is set before making API calls.

## Project structure

```
social-media-generator/
├── templates/     # Content or UI templates
├── src/           # Package code
├── data/          # Generated data, DBs, CSVs (gitignored as specified)
├── logs/          # Application logs (gitignored as specified)
├── tests/         # Pytest tests
├── app.py         # Application entrypoint
├── config.py      # Configuration and env loading
├── .env.example   # Example environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

## Architecture

- **config.py**: Loads `.env` with python-dotenv, defines paths (data, logs), model name, token costs, and daily budget. Validates API key when the app runs.
- **app.py**: Entrypoint (Streamlit or CLI); calls config validation and drives content generation.
- **src/**: Reusable logic (e.g. OpenAI client, budget tracking) as the project grows.
- Data and logs are written under `data/` and `logs/` with configurable paths.
