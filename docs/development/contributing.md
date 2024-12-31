# Contributing Guide

## Getting Started

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/yourusername/ai-sports-model-builder.git
cd ai-sports-model-builder
```

3. Set up your development environment:
```bash
make dev-setup
```

## Development Workflow

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes following our coding standards:
- Use type hints
- Write docstrings
- Follow PEP 8
- Keep functions focused
- Write tests

3. Run tests and checks:
```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test
```

4. Commit your changes:
```bash
git add .
git commit -m "Description of your changes"
```

5. Push your changes:
```bash
git push origin feature/your-feature-name
```

6. Create a pull request

## Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Configuration is in `setup.cfg` and `.pre-commit-config.yaml`.

## Testing

Write tests for all new features:

```python
def test_your_feature():
    # Arrange
    data = setup_test_data()
    
    # Act
    result = your_feature(data)
    
    # Assert
    assert result == expected_result
```

Test categories:
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Functional tests: `tests/functional/`
- End-to-end tests: `tests/e2e/`

## Documentation

Update documentation for new features:

1. Add docstrings to your code:
```python
def your_function(param: str) -> bool:
    """Do something with param.
    
    Args:
        param: Description of param
        
    Returns:
        Description of return value
    """
```

2. Update relevant markdown files in `docs/`
3. Build docs: `make docs`
4. Check locally: `make serve-docs`

## Pull Request Process

1. Update documentation
2. Add tests
3. Run all checks
4. Update CHANGELOG.md
5. Request review
6. Address feedback

## Commit Messages

Follow conventional commits:
```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
refactor: Refactor code
style: Format code
chore: Update tooling
```

## Release Process

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create release PR
4. After merge, tag release:
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Questions?

- Open an issue
- Join our discussions
- Read our documentation 