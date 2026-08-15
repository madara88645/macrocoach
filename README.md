# MACROCOACH v0.1

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![GitHub](https://img.shields.io/badge/GitHub-madara88645%2Fmacrocoach-blue?logo=github)

🤖 **AI-powered nutrition coaching system** with Turkish cuisine focus and privacy-first design.

> 🔗 **Repository**: https://github.com/madara88645/macrocoach

An open-source coaching service that pulls real-time health metrics and provides adaptive nutrition + training recommendations.

## 🔑 Features

- **Multi-Platform Health Data**: Integrates with Apple HealthKit (iOS), Android Health Connect, and Xiaomi Smart Band 9
- **Macro Tracking**: Compares dietary intake with science-based daily targets
- **Adaptive Recommendations**: Generates personalized nutrition and training plans
- **Conversational Interface**: Chat-based UI for easy interaction
- **Privacy-First**: All user data stored locally (GDPR compliant)
- **Plate-Cam**: Optional vision module to log meals using your camera

## 🏗️ Architecture

The system consists of 5 main agents:

1. **DataConnectorAgent**: Pulls health metrics from various sources
2. **StateStoreAgent**: Normalizes and persists data to local SQLite DB
3. **PlannerAgent**: Calculates energy expenditure and sets macro targets
4. **MealGenAgent**: Generates meal suggestions using LLM
5. **ChatUIAgent**: Provides conversational interface via FastAPI
6. **PlateRecognizer** (optional): Estimates meal macros from photos

```text
 [ Vision Flow Diagram Placeholder ]
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Poetry (package manager)
- Docker & Docker Compose (for demo)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd macrocoach

# Install dependencies
poetry install

# Set up pre-commit hooks
poetry run pre-commit install

# Run tests
poetry run pytest

# Start the demo
make demo
```

### Environment Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./macrocoach.db
LOG_LEVEL=INFO
```

## 📋 Development Roadmap

- [x] T-00: Repo scaffold – Poetry + Ruff + pre-commit
- [ ] T-01: Implement StateStoreAgent + tests
- [ ] T-02: Implement HealthKitConnector (mock data first)
- [ ] T-03: Implement HealthConnectConnector (Android emulator)
- [ ] T-04: Implement rule-based PlannerAgent with unit tests
- [ ] T-05: Implement MealGenAgent using OpenAI GPT-4o function calls
- [ ] T-06: Wire ChatUIAgent (FastAPI) + simple Streamlit dashboard
- [ ] T-07: End-to-end test with dummy data; CI via GitHub Actions
- [ ] T-08: Produce README + architecture diagram (.svg)

## 🧪 Testing

```bash
# Run all tests with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_state_store.py

# Run with verbose output
poetry run pytest -v
```

## 🔧 API Usage

### Start the server

```bash
poetry run uvicorn src.macrocoach.main:app --reload
```

### Chat Interface

```bash
# Get daily status
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "/status"}'

# Get meal plan
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "/plan"}'
```

## 📊 Data Schema

The normalized health metrics schema:

```python
{
    "timestamp": "2025-07-22T10:30:00Z",
    "kcal_out": 2200,
    "heart_rate": 75,
    "steps": 8500,
    "sleep_score": 85,
    "weight": 70.5,
    "protein_g": 120,
    "carbs_g": 250,
    "fat_g": 80,
    "workout_type": "strength",
    "rpe": 7
}
```

## 🌟 Future Enhancements (v2.0)

- Reinforcement Learning via PPO/SAC
- Real-time WebSocket HR streaming
- GPT-4o vision for plate recognition
- Advanced workout planning algorithms

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Apple HealthKit documentation
- Google Fit API (until 2025-06-30)
- Mi Band community for BLE insights
- OpenAI for GPT-4o integration
