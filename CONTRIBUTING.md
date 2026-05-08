# Contributing to Sales Agentic Army

First off, thank you for considering contributing! It's people like you that make the Sales Agentic Army such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps to reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed and what behavior you expected**
* **Include screenshots and animated GIFs if possible**
* **Include log output if available**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a detailed description of the suggested enhancement**
* **Explain why this enhancement would be useful**
* **List some examples of how this enhancement would be used**

### Pull Requests

* Fill in the required template
* Follow the Python style guide (Black formatting)
* Include tests for new functionality
* Update documentation as needed
* Add an entry to the changelog

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Kubernetes cluster (kind, minikube, or cloud)
- Redis, PostgreSQL, Kafka (can run via Docker)

### Local Development

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/sales-agentic-army.git
cd sales-agentic-army

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest tests/unit -v
```

## Coding Guidelines

### Style Guide

We use [Black](https://black.readthedocs.io/) for code formatting and [isort](https://pycqa.github.io/isort/) for import sorting:

```bash
black src/ tests/
isort src/ tests/
```

### Type Hints

All public functions should have type hints:

```python
from typing import Dict, List, Optional

def process_lead(lead_id: str, fields: Optional[List[str]] = None) -> Dict[str, any]:
    ...
```

### Documentation

* Use docstrings for all public functions and classes
* Follow Google style for docstrings
* Keep documentation up to date

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest tests/unit
pytest tests/integration
pytest tests/load
```

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
feat: add NegotiatorAgent with RL-based strategy
fix: resolve memory leak in ChromaDB connection
docs: update architecture diagrams
chore: upgrade LangChain dependency to 0.1.0
```

## Release Process

Releases are automated through GitHub Actions:

1. Version bump is triggered by merging a `chore: release` PR
2. CI/CD pipeline runs tests and builds artifacts
3. Docker images are pushed to registry
4. GitHub release is created with changelog
5. Documentation is deployed

Thank you for contributing! 🎉
