# MacroCoach Development Guide

## Quick Start

### Prerequisites
- Python 3.12+
- Poetry (package manager) or pip
- Git

### Setup

1. **Clone and install:**
```bash
git clone <your-repo-url>
cd macrocoach

# Option 1: With Poetry (recommended)
poetry install

# Option 2: With pip (alternative)
pip install fastapi uvicorn pydantic sqlalchemy streamlit pandas numpy python-multipart aiofiles python-dotenv plotly requests pytest pytest-asyncio pytest-cov httpx openai
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Initialize pre-commit hooks (if using Poetry):**
```bash
poetry run pre-commit install
```

4. **Run the quick test:**
```bash
python quick_test.py
```

### Development Commands

**Windows (PowerShell):**
```powershell
.\make.ps1 install    # Install dependencies
.\make.ps1 dev        # Start API server
.\make.ps1 streamlit  # Start dashboard
.\make.ps1 test       # Run tests
```

**Linux/Mac:**
```bash
make install    # Install dependencies
make dev        # Start API server
make streamlit  # Start dashboard
make test       # Run tests
```

### Project Structure

```
macrocoach/
├── src/macrocoach/
│   ├── agents/           # Main business logic agents
│   │   ├── state_store_agent.py    # Data persistence
│   │   ├── planner_agent.py        # Nutrition planning
│   │   ├── meal_gen_agent.py       # Meal generation
│   │   └── chat_ui_agent.py        # Chat interface
│   ├── connectors/       # Health data connectors
│   │   ├── healthkit.py            # Apple HealthKit
│   │   └── base.py                 # Base connector
│   ├── core/            # Core models and utilities
│   │   ├── models.py               # Pydantic models
│   │   └── context.py              # Application context
│   ├── ui/              # User interfaces
│   │   └── dashboard.py            # Streamlit dashboard
│   └── main.py          # FastAPI application
├── tests/               # Test files
├── scripts/             # Utility scripts
└── docs/               # Documentation
```

## Recent Improvements (v0.1.1)

✅ **Modern FastAPI Implementation**
- Updated from deprecated `@app.on_event` to modern `lifespan` context manager
- Improved application startup and shutdown handling
- Better dependency injection and error handling

✅ **Fixed Test Infrastructure**
- All 8 tests now passing (100% success rate)
- Fixed async fixture configuration with `@pytest_asyncio.fixture`
- Added missing test fixtures and improved test coverage (38%)

✅ **Enhanced Reliability**
- Application starts reliably and responds to all API endpoints
- Proper OpenAI client initialization and error handling
- Better environment variable configuration

✅ **API Endpoints Fully Functional**
- `/health` - Health check endpoint
- `/` - Root endpoint with API information  
- `/chat` - Chat interface for nutrition coaching
- `/meal-image` - Image analysis for meal macros
- `/docs` - Interactive API documentation

### Testing

Run the test suite:
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_state_store.py -v
```

### Starting the Application

```bash
# Start the server
uvicorn src.macrocoach.main:app --reload

# Or using Python module
python -m uvicorn src.macrocoach.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

### API Endpoints

- `GET /` - Basic info
- `GET /health` - Health check
- `POST /chat` - Chat interface
- `GET /api/status/{user_id}` - User status

### Chat Commands

- `/status` - Today's summary
- `/plan` - Tomorrow's meal plan
- `/add <data>` - Log metrics
- `/swap <meal_id>` - Replace meal
- `/help` - Show commands

### Testing

```bash
# Run all tests
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html

# Specific test file
poetry run pytest tests/test_state_store.py -v
```

### Database Schema

**health_metrics** - Normalized health data
**user_profiles** - User preferences and goals
**daily_plans** - Generated nutrition plans
**chat_messages** - Chat interactions

### Adding New Features

1. **New Agent:** Create in `src/macrocoach/agents/`
2. **New Model:** Add to `src/macrocoach/core/models.py`
3. **New Connector:** Inherit from `BaseConnector`
4. **New Test:** Add to `tests/`

### Environment Variables

```bash
OPENAI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./macrocoach.db
LOG_LEVEL=INFO
DEBUG=true
```

### Docker Development

```bash
# Full demo
docker-compose up

# API only
docker build -t macrocoach .
docker run -p 8000:8000 macrocoach

# Dashboard only
docker build -f Dockerfile.streamlit -t macrocoach-dashboard .
docker run -p 8501:8501 macrocoach-dashboard
```

### Troubleshooting

**Import errors:** Make sure you're in the project root and poetry shell is activated

**Database errors:** Delete macrocoach.db and restart

**API connection issues:** Check that the server is running on port 8000

**Missing dependencies:** Run `poetry install` again
