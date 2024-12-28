# AI Sports Model Builder

A sophisticated sports betting model builder that uses machine learning and real-time data to analyze and predict sports outcomes.

## Overview

This project provides a comprehensive platform for:
- Collecting sports data from various sources
- Processing and analyzing betting odds
- Building predictive models
- Tracking model performance
- Making informed betting decisions

## Project Structure

```
ai-sports-model-builder/
├── src/                    # Source code
│   ├── api/               # API clients and integrations
│   │   ├── odds_api.py    # The Odds API client
│   │   └── utils.py       # API utilities and helpers
│   ├── core/              # Core functionality and base classes
│   │   ├── config.py      # Configuration management
│   │   ├── database.py    # Database connection and session management
│   │   └── logging.py     # Logging configuration
│   ├── data_collection/   # Data collection and processing
│   │   ├── collectors/    # Data collector implementations
│   │   └── processors/    # Data processing and transformation
│   ├── models/            # Database models and schemas
│   │   ├── base.py       # Base model classes
│   │   └── sports/       # Sport-specific models
│   ├── schemas/           # Pydantic schemas for validation
│   │   ├── base.py       # Base schema classes
│   │   └── sports/       # Sport-specific schemas
│   └── services/          # Business logic services
│       ├── odds/         # Odds processing services
│       └── predictions/  # Prediction generation services
│
├── tests/                 # Test suite
│   ├── unit/             # Unit tests for individual components
│   ├── integration/      # Integration tests for component interactions
│   ├── functional/       # Functional tests for complete features
│   └── e2e/             # End-to-end tests for system behavior
│
├── docs/                 # Documentation
│   ├── api/             # API documentation and endpoints
│   ├── models/          # Database models documentation
│   ├── data_collection/ # Data collection process documentation
│   └── testing/         # Testing strategy and guidelines
│
├── migrations/          # Database migrations
│   ├── versions/       # Migration version files
│   └── env.py         # Migration environment configuration
│
├── scripts/            # Utility and maintenance scripts
│   ├── setup_db.py    # Database setup script
│   └── load_data.py   # Data loading utilities
│
├── notebooks/          # Jupyter notebooks
│   ├── analysis/      # Data analysis notebooks
│   ├── modeling/      # Model development notebooks
│   └── examples/      # Example usage notebooks
│
├── data/              # Data directory (gitignored)
│   ├── raw/          # Raw data from various sources
│   ├── processed/    # Processed and cleaned data
│   ├── interim/      # Intermediate data
│   └── external/     # External reference data
│
├── .github/           # GitHub specific files
│   ├── workflows/    # GitHub Actions workflows
│   └── ISSUE_TEMPLATE/ # Issue and PR templates
│
├── requirements/      # Dependency management
│   ├── requirements.txt     # Production dependencies
│   └── requirements-dev.txt # Development dependencies
│
└── configuration files
    ├── .env.example   # Environment variables template
    ├── setup.py       # Package setup file
    ├── setup.cfg      # Tool configurations
    ├── pytest.ini     # pytest configuration
    ├── .gitignore     # Git ignore patterns
    ├── .gitattributes # Git attributes
    └── Makefile       # Development automation
```

### Directory Descriptions

#### Source Code (`src/`)
- `api/`: API client implementations for external data sources
- `core/`: Core functionality, configurations, and base classes
- `data_collection/`: Data collection and processing modules
- `models/`: SQLAlchemy models for database entities
- `schemas/`: Pydantic schemas for data validation
- `services/`: Business logic and service layer implementations

#### Tests (`tests/`)
- `unit/`: Tests for individual components in isolation
- `integration/`: Tests for component interactions
- `functional/`: Tests for complete features
- `e2e/`: End-to-end system tests

#### Documentation (`docs/`)
- `api/`: API documentation and usage guides
- `models/`: Database model documentation
- `data_collection/`: Data collection process documentation
- `testing/`: Testing strategy and guidelines

#### Database (`migrations/`)
- Database migration files for version control
- Migration environment configuration

#### Scripts (`scripts/`)
- Utility scripts for maintenance tasks
- Database setup and data loading tools

#### Notebooks (`notebooks/`)
- Jupyter notebooks for analysis and development
- Example usage and tutorials
- Model development and experimentation

#### Data (`data/`)
- Structured storage for different data stages
- Separated into raw, processed, interim, and external data
- Note: This directory is gitignored

#### Configuration
- Environment configuration templates
- Tool configurations for linting, testing, etc.
- Build and package configuration

#### GitHub (`github/`)
- CI/CD workflows
- Issue and PR templates
- GitHub-specific configuration

### Key Files

- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development dependencies
- `setup.py`: Package installation configuration
- `setup.cfg`: Tool configurations
- `pytest.ini`: Test configuration
- `Makefile`: Development automation commands
- `.env.example`: Environment variable template

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-sports-model-builder.git
cd ai-sports-model-builder
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

4. Set up environment variables:
```bash
# Create .env file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

## Database Setup

1. Initialize the database:
```bash
# Create database
python src/core/database.py

# Run migrations
alembic upgrade head
```

2. (Optional) Load sample data:
```bash
python scripts/load_sample_data.py
```

## Running Tests

The project uses pytest for testing. Here are the main test commands:

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/functional/
python -m pytest tests/e2e/

# Run with coverage report
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/path/to/test_file.py

# Run tests with specific marker
python -m pytest -m "unit"
python -m pytest -m "integration"
```

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Functional Tests**: Test complete features
- **End-to-End Tests**: Test complete system behavior

## Development

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run style checks:
```bash
# Format code
black src tests

# Sort imports
isort src tests

# Run linter
flake8 src tests

# Run type checker
mypy src tests
```

### Documentation

View the documentation:
- [API Documentation](docs/api/)
- [Models Documentation](docs/models/)
- [Data Collection Documentation](docs/data_collection/)
- [Testing Documentation](docs/testing/)

### Making Changes

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and run tests:
```bash
# Run tests
python -m pytest

# Run style checks
black src tests
isort src tests
flake8 src tests
mypy src tests
```

3. Commit your changes:
```bash
git add .
git commit -m "Description of your changes"
```

4. Push your changes:
```bash
git push origin feature/your-feature-name
```

## API Keys

The project requires API keys for:
- The Odds API (https://the-odds-api.com/)

Add your API keys to the `.env` file:
```bash
ODDS_API_KEY=your_api_key_here
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and style checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The Odds API for providing sports betting data
- SQLAlchemy for database operations
- pytest for testing infrastructure
- All contributors to the project
