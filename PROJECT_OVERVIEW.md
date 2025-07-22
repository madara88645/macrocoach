# 📋 MACROCOACH v0.1 - Project Overview

## 🎯 What is MACROCOACH?

MACROCOACH is an AI-powered nutrition coaching system that provides personalized meal plans and health recommendations. Built with a focus on Turkish cuisine and privacy-first approach.

## ✨ Key Features

### 🤖 **5-Agent Architecture**
- **StateStoreAgent**: Data persistence and management
- **PlannerAgent**: BMR/TDEE calculations and macro planning  
- **MealGenAgent**: AI-powered Turkish meal generation
- **ChatUIAgent**: Conversational interface
- **DataConnectorAgent**: Health platform integrations

### 🍽️ **Smart Nutrition Planning**
- Science-based BMR/TDEE calculations (Mifflin-St Jeor equation)
- Personalized macro targets (protein/carbs/fat ratios)
- Turkish cuisine recipe database
- Meal swapping and preference learning

### 📊 **Health Data Integration**
- Apple HealthKit (iOS)
- Android Health Connect
- Xiaomi Mi Band 9
- Manual data entry
- Real-time metric synchronization

### 🔒 **Privacy-First Design**
- Local SQLite database
- GDPR compliant data handling
- No cloud storage of personal health data
- Optional data sharing controls

## 🏗️ Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI | REST API server |
| **Database** | SQLite | Local data storage |
| **AI/ML** | OpenAI GPT-4 | Meal generation |
| **Frontend** | Streamlit | Analytics dashboard |
| **Containerization** | Docker | Deployment |
| **Testing** | Pytest | Unit/integration tests |
| **CI/CD** | GitHub Actions | Automated testing |

## 📂 Project Structure

```
macrocoach/
├── src/macrocoach/           # Main application code
│   ├── agents/               # Agent implementations
│   ├── core/                 # Core models and context
│   └── main.py              # FastAPI application
├── dashboard/                # Streamlit dashboard
├── tests/                    # Test suite
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── docker/                   # Docker configurations
├── .github/workflows/        # CI/CD pipelines
└── data/                     # Sample data and schemas
```

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   git clone https://github.com/yourusername/macrocoach.git
   cd macrocoach
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Add your OpenAI API key to .env
   ```

3. **Run the application**:
   ```bash
   uvicorn src.macrocoach.main:app --reload
   ```

4. **Test the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/macrocoach --cov-report=html

# Run specific test categories
pytest tests/agents/
pytest tests/core/
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in production mode
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/health` | GET | System health check |
| `/chat` | POST | Chat with the nutrition coach |
| `/users/{user_id}/status` | GET | Get user status and metrics |
| `/users/{user_id}/plan` | GET | Get current nutrition plan |
| `/meals/suggest` | POST | Get meal suggestions |

## 🔮 Roadmap

### Version 0.2 (Next)
- [ ] Reinforcement learning for meal preferences
- [ ] Advanced analytics dashboard
- [ ] Mobile app companion
- [ ] Multi-language support

### Version 0.3 (Future)
- [ ] Computer vision food recognition
- [ ] Advanced biometric analysis
- [ ] Social features and challenges
- [ ] Nutrition expert consultation integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Turkish cuisine database inspired by traditional recipes
- Health metric calculations based on peer-reviewed research
- Built with modern Python ecosystem best practices

---

**Made with ❤️ for healthier living through technology**
