# Contributing to stage0_mongodb_api

Thank you for your interest in contributing to the stage0_mongodb_api project! This document provides a quick start guide for development and contribution.

## Project Structure

```
stage0_mongodb_api/
├── stage0_mongodb_api/          # Main package directory
│   ├── managers/               # Database managers
│   ├── routes/                 # API route handlers
│   ├── services/              # Business logic services
│   ├── server.py              # Main server application
│   └── __init__.py
├── tests/                      # Test directory
│   ├── managers/              # Tests for database managers
│   ├── routes/                # Tests for API routes
│   ├── services/              # Tests for business logic
│   ├── test_server.py         # Server tests
│   └── stepci.yaml            # StepCI configuration
├── docs/                       # Documentation
│   ├── REFERENCE.md           # Main reference documentation
│   ├── collection_config.md   # Collection configuration guide
│   ├── schema.md             # Schema language documentation
│   ├── types.md              # Custom types documentation
│   ├── versioning.md         # Version management guide
│   └── schemas/              # Schema definitions
├── Pipfile                     # Python dependencies
├── requirements.txt            # Additional requirements
└── CURL_EXAMPLES.md           # API usage examples
```

## Development Setup

1. Set up your development environment:
   - Install Python 3.8 or later
   - Install Pipenv
   - Install Docker Desktop
   - Install MongoDB or use MongoDB Atlas

2. Clone the repository:
   ```bash
   git clone https://github.com/agile-learning-institute/stage0_mongodb_api.git
   cd stage0_mongodb_api
   ```

3. Install dependencies:
   ```bash
   pipenv install
   ```

## Development Workflow

### Local Development
```bash
pipenv run local
```

### Testing
```bash
# Run unit tests
pipenv run test

# Run end-to-end tests
pipenv run stepci
```

### Containerized Development
```bash
# Build and run containers
pipenv run container
```

## Development Standards

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document all public functions and classes
- Keep functions focused and small

### Testing Requirements
- Maintain 90% test coverage
- Write unit tests for all new features
- Include integration tests for API endpoints
- Run tests before submitting PRs

### Documentation
- Update relevant documentation files
- Include examples for new features
- Add API endpoint documentation
- Update CURL examples if needed

### Pull Request Process
1. Create a feature branch
2. Make your changes
3. Run tests and ensure they pass
4. Update documentation
5. Submit a pull request
6. Address review comments

## Getting Help

- Join our [Discord Server](https://discord.gg/agile-learning-institute)
- Check existing issues and PRs
- Ask in the development channel
- Contact maintainers

## License

By contributing to stage0_mongodb_api, you agree that your contributions will be licensed under the project's MIT License. 