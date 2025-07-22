# PowerShell script equivalent to Makefile for Windows
# Run with: .\make.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Available commands:" -ForegroundColor Cyan
    Write-Host "  install     - Install dependencies" -ForegroundColor Green
    Write-Host "  test        - Run tests with coverage" -ForegroundColor Green
    Write-Host "  lint        - Run linting" -ForegroundColor Green
    Write-Host "  format      - Format code" -ForegroundColor Green
    Write-Host "  clean       - Clean up cache and temporary files" -ForegroundColor Green
    Write-Host "  demo        - Start the demo with Docker Compose" -ForegroundColor Green
    Write-Host "  dev         - Start development server" -ForegroundColor Green
    Write-Host "  streamlit   - Start Streamlit dashboard" -ForegroundColor Green
}

function Install-Dependencies {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    poetry install
    poetry run pre-commit install
}

function Run-Tests {
    Write-Host "Running tests with coverage..." -ForegroundColor Yellow
    poetry run pytest --cov=src --cov-report=html --cov-report=term-missing
}

function Run-Linting {
    Write-Host "Running linting..." -ForegroundColor Yellow
    poetry run ruff check src tests
    poetry run mypy src
}

function Format-Code {
    Write-Host "Formatting code..." -ForegroundColor Yellow
    poetry run black src tests
    poetry run ruff --fix src tests
}

function Clean-Up {
    Write-Host "Cleaning up cache and temporary files..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force .pytest_cache -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force .mypy_cache -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force htmlcov -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force *.egg-info -ErrorAction SilentlyContinue
}

function Start-Demo {
    Write-Host "Starting demo with Docker Compose..." -ForegroundColor Yellow
    docker-compose up --build
}

function Start-Dev {
    Write-Host "Starting development server..." -ForegroundColor Yellow
    poetry run uvicorn src.macrocoach.main:app --reload --host 0.0.0.0 --port 8000
}

function Start-Streamlit {
    Write-Host "Starting Streamlit dashboard..." -ForegroundColor Yellow
    poetry run streamlit run src/macrocoach/ui/dashboard.py
}

switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "test" { Run-Tests }
    "lint" { Run-Linting }
    "format" { Format-Code }
    "clean" { Clean-Up }
    "demo" { Start-Demo }
    "dev" { Start-Dev }
    "streamlit" { Start-Streamlit }
    default { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help 
    }
}
