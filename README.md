# AI Sports Model Builder

A sophisticated sports betting data collection and analysis system, focusing on NBA games and odds data.

## Overview

This project collects and analyzes sports betting data, with a focus on NBA games. It features real-time odds collection, historical data analysis, and a robust data processing pipeline.

## Features

- Real-time odds collection from multiple bookmakers
- Historical odds data analysis
- Efficient data storage and caching
- Comprehensive error handling and logging
- Rate limiting and API optimization
- Async/await pattern for improved performance

## Project Structure

```
.
├── src/
│   ├── data_collection/           # Data collection modules
│   │   ├── clients/               # API clients
│   │   ├── collectors/            # Data collectors
│   │   ├── transformers/          # Data transformers
│   │   └── utils/                 # Utility functions
│   ├── models/                    # Data models
│   │   ├── domain/               # Domain models
│   │   └── database/             # Database models
│   ├── schemas/                   # Data schemas
│   │   ├── requests/             # Request schemas
│   │   ├── responses/            # Response schemas
│   │   └── validation/           # Validation schemas
│   └── services/                  # Business logic services
│       ├── data/                 # Data services
│       ├── odds/                 # Odds processing services
│       ├── notification/         # Notification services
│       └── prediction/           # Prediction services
├── scripts/                       # Utility scripts
│   ├── data/                     # Data scripts
│   ├── deployment/               # Deployment scripts
│   └── testing/                  # Testing scripts
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
└── docs/                         # Documentation
    ├── architecture/            # Architecture docs
    ├── development/            # Development guides
    └── api-reference/         # API documentation
```

## Setup

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
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Running the Live Odds Collector

```bash
# Set collection interval (optional, defaults to 300 seconds)
export COLLECTION_INTERVAL=300

# Set maximum retries (optional, defaults to 3)
export MAX_RETRIES=3

# Run the collector
python scripts/data/collect_live_odds.py
```

### Development

1. Install pre-commit hooks:

```bash
pre-commit install
```

2. Run tests:

```bash
pytest
```

3. Run linting:

```bash
black .
isort .
flake8
mypy .
```

## Configuration

The following environment variables are supported:

- `ODDS_API_KEY`: Your API key for The Odds API
- `COLLECTION_INTERVAL`: Interval between odds collections (seconds)
- `MAX_RETRIES`: Maximum number of retries for failed operations
- `DATABASE_URL`: Database connection string
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Odds API for providing sports betting data
- All contributors who have helped with the project
