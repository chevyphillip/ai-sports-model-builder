# Testing Documentation

## Overview
This document describes the testing infrastructure and practices used in the project.

## Test Structure
The tests are organized into the following categories:

### Unit Tests (`tests/unit/`)
- Tests for individual components in isolation
- Fast execution
- No external dependencies
- Example: Testing model methods, utility functions

### Integration Tests (`tests/integration/`)
- Tests for component interactions
- May involve external services (mocked)
- Example: Testing API clients, database operations

### Functional Tests (`tests/functional/`)
- Tests for complete features
- End-to-end workflows
- Example: Testing data collection pipeline

### End-to-End Tests (`tests/e2e/`)
- Tests for complete system behavior
- Real external services
- Example: Testing full application workflows

## Test Configuration

### pytest.ini
The project uses pytest with the following configuration:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Logging settings
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)s)
log_cli_date_format = %Y-%m-%d %H:%M:%S

# Custom markers
markers =
    unit: Unit tests
    integration: Integration tests
    functional: Functional tests
    e2e: End-to-end tests
    api: API tests
    model: Database model tests
    service: Service layer tests
    slow: Tests that take longer to run
    smoke: Basic smoke tests
```

### Test Dependencies
Required packages for testing (from `requirements-dev.txt`):
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
pytest-asyncio>=0.21.1
pytest-xdist>=3.3.1
pytest-sugar>=0.9.7
pytest-timeout>=2.1.0
coverage>=7.3.0
```

## Test Fixtures

### Database Fixtures
- `engine`: SQLAlchemy engine for testing
- `tables`: Creates and drops database tables
- `db_session`: Provides a database session

### Directory Fixtures
- `temp_dir`: Temporary directory for test files
- `test_data_dir`: Directory for test data files
- `test_models_dir`: Directory for test model files
- `test_logs_dir`: Directory for test log files

### API Fixtures
- `odds_api_client`: Client for The Odds API
- Mock response fixtures for various API endpoints

## Running Tests

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test Categories
```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# Functional tests
python -m pytest tests/functional/

# End-to-end tests
python -m pytest tests/e2e/
```

### Run with Coverage
```bash
python -m pytest --cov=src
```

## Test Coverage
- Coverage reports are generated in HTML format
- Coverage data is displayed in the terminal
- Minimum coverage requirements:
  - Unit tests: 90%
  - Integration tests: 80%
  - Overall: 75%

## Edge Cases
The test suite includes comprehensive edge case testing:
- Empty responses
- Malformed data
- Network errors
- Invalid parameters
- Unicode handling
- Large datasets
- Rate limiting
- Missing required fields

## Best Practices
1. Write tests before implementing features (TDD)
2. Keep tests focused and isolated
3. Use meaningful test names
4. Document test requirements and assumptions
5. Mock external dependencies
6. Handle test data cleanup
7. Avoid test interdependence
8. Use appropriate assertions
9. Test both success and failure cases
10. Keep tests maintainable

## Continuous Integration
Tests are run automatically on:
- Pull requests
- Merges to main branch
- Release tags

## Future Improvements
1. Add performance testing
2. Implement load testing
3. Add security testing
4. Improve test data management
5. Add mutation testing 