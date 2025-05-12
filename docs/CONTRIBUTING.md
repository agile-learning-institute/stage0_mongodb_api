# Contributing to stage0_mongodb_api

Thank you for your interest in contributing to the stage0_mongodb_api project! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork
3. Install dependencies:
   ```bash
   pipenv install
   ```
4. Set up your development environment:
   - Install Python 3.8 or later
   - Install Pipenv
   - Install MongoDB (or use Docker)

## Development Workflow

1. Create a new branch for your feature or bugfix
2. Make your changes
3. Run tests:
   ```bash
   pipenv run test
   ```
4. Run end-to-end tests:
   ```bash
   pipenv run stepci
   ```
5. Submit a pull request

## Code Standards

- Follow PEP 8 style guidelines
- Write unit tests for new features
- Update documentation for API changes
- Keep the OpenAPI specification up to date

## Testing

- Unit tests should have at least 90% coverage
- End-to-end tests should cover all API endpoints
- Test both success and error cases
- Include integration tests for MongoDB operations

## Documentation

- Update README.md for significant changes
- Document new configuration options
- Update OpenAPI specification for API changes
- Add examples for new features

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the OpenAPI specification if the API changes
3. The PR will be merged once you have the sign-off of at least one other developer

## Questions?

Feel free to open an issue for any questions or concerns. 