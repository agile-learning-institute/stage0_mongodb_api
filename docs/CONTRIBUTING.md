# Contributing to stage0_mongodb_api

Thank you for your interest in contributing to the stage0_mongodb_api project! This document provides a quick start guide for development and contribution.

## Project Structure

```
stage0_mongodb_api/
├── stage0_mongodb_api/       # Main package directory
│   ├── managers/             # Database managers
│   ├── routes/               # API route handlers
│   ├── services/             # Business logic services
│   ├── server.py             # Main server application
│   └── __init__.py
├── tests/                    # Test directory
│   ├── managers/             # Tests for database managers
│   ├── routes/               # Tests for API routes
│   ├── services/             # Tests for business logic
│   ├── test_server.py        # Server tests
│   ├── test_cases/           # Schema test cases
│   └── stepci.yaml           # StepCI configuration
├── docs/                     # Documentation
│   ├── REFERENCE.md          # Main reference documentation
│   ├── CONTRIBUTING.md       # Collection configuration guide
│   ├── schema.md             # Schema language documentation
│   ├── types.md              # Custom types documentation
│   ├── versioning.md         # Version management guide
│   └── schemas/              # Schema definitions
├── README.md                 # Overview and Usage
└── CURL_EXAMPLES.md          # API usage examples
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

## Development Commands

All development commands are run using pipenv:

```bash
# Local development
pipenv run local

# Run unit tests
pipenv run test

# Run end-to-end tests
pipenv run stepci

# Build and run containers
pipenv run container
```

## Schema Testing

The schema system uses test input folders to validate functionality. Each test case consists of:

1. **Test Case Structure**:
```
tests/test_cases/
  case_name/
    collections/              # Collection configurations
      user.yaml              # User collection config
      media.yaml             # Media collection config
    dictionary/              # Schema definitions
      types/                 # Custom types
        word.yaml
        timestamp.yaml
      user.1.0.0.yaml        # Schema version
    data/                    # Test data
      enumerators.json       # Enumerator definitions
      users.1.0.0.1.json     # Test data version
    expected/
      validation.json                # Expected validation errors
      user.1.0.0.1.json_schema.json  # Expected JSON schema
      user.1.0.0.1.bson_schema.json  # Expected BSON schema
      media.1.0.0.1.json_schema.json # Expected JSON schema
      media.1.0.0.1.bson_schema.json # Expected BSON schema
```

2. **Test Organization**:
   - Each test case has its own directory
   - Input files mirror the production structure
   - Expected outputs are stored in the `expected` directory
   - Validation results are a list of errors (empty list for success)
   - Schema outputs are organized by collection

## Development Standards

This project follows the development standards defined in the stage0 project:

- [Contributing Guidelines](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/contributing.md)
- [API Standards](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/api-standards.md)

## Getting Help

- Join our [Discord Server](https://discord.gg/agile-learning-institute)
- Check existing issues and PRs
- Ask in the development channel
- Contact maintainers

## License

By contributing to stage0_mongodb_api, you agree that your contributions will be licensed under the project's MIT License. 