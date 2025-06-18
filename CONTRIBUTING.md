# Contributing to stage0_mongodb_api

This document provides information for developers contributing to the stage0_mongodb_api project.

## Development Standards

This project follows the [Stage0 development standards](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/contributing.md) and implements [API standards](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/api-standards.md) for consistency across the platform. The service is designed with [configurability](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/service-configurability.md) and [observability](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/service-observability.md) in mind.

## Architecture Overview

### Application Entry Point

- **server.py** - Main Flask application entry point that initializes the API server, registers routes, and handles startup/shutdown logic

### API Layer

- **Routes** - Flask Blueprint modules that handle HTTP requests and responses
  - **collection_routes.py** - Collection management endpoints (`/api/collections`)
  - **render_routes.py** - Schema rendering endpoints (`/api/render`)
  - **config_routes.py** - Configuration endpoints (`/api/config`) from stage0_py_utils

- **Services** - Business logic layer that coordinates operations between routes and managers
  - **collection_service.py** - Collection processing and management operations
  - **render_service.py** - Schema rendering operations

### Core Managers

- **ConfigManager** - Loads collection configurations and orchestrates version processing workflows
- **VersionManager** - Tracks collection versions in MongoDB and provides version comparison
- **SchemaManager** - Handles schema loading, validation, rendering, and application to MongoDB
- **IndexManager** - Manages MongoDB index creation and deletion
- **MigrationManager** - Executes data migration pipelines using MongoDB aggregations

### Supporting Components

- **VersionNumber** - Parses and compares version strings (major.minor.patch.enumerator)
- **SchemaRenderer** - Renders schemas in JSON and BSON formats
- **SchemaValidator** - Validates schema definitions and configurations
- **SchemaTypes** - Type definitions and enums for schema operations

## Development Setup

### Prerequisites

- Python 3.8 or later
- Pipenv
- MongoDB (local or Docker)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd stage0_mongodb_api
```

### Developer Commands

```bash
# Run Unit Tests
pipenv run test

# Run unit tests with coverage
pipenv run test --with-coverage

# Select a test_case for the server
export INPUT_FOLDER=./tests/test_cases/small_sample

# Set Debug Mode
export LOGGING_LEVEL=DEBUG

# Start API server (starts MongoDB container first)
pipenv run start

# Start API server if database is already running
pipenv run local

# Start with debugging
pipenv run debug

# Run in Batch mode (process and shut down)
pipenv run batch

# Run StepCI API black box testing
pipenv run stepci

# Build the API Docker Image
pipenv run build

# Build & run the API Docker Container
pipenv run container
```

## Testing

### Test Structure

The `tests/` directory contains comprehensive test coverage:

```
tests/
├── managers/           # Manager class tests
├── routes/            # API endpoint tests
├── services/          # Service layer tests
├── test_cases/        # Test data and configurations
│   ├── small_sample/  # Minimal test configuration
│   ├── large_sample/  # Complex test configuration
│   └── validation_errors/ # Error scenario tests
└── test_server.py     # Server integration tests
```

### Test Cases

The `tests/test_cases/` directory contains test scenarios:

- **small_sample**: Minimal configuration with one collection for basic functionality testing
- **large_sample**: Complex multi-collection setup with relationships and advanced features
- **validation_errors**: Test cases for error handling and validation scenarios
- **minimum_valid**: Empty configuration for edge case testing

### Load and Validation Errors
 Load and validation unit testing leverages test cases with known errors. Assertions validate that the errors were thrown using the unique identifier thrown in the code. If you introduce new testing, make sure you add new unique identifiers here.

### Rendering Tests
 Rendering tests for both the small_sample and large_sample test cases is done using the expected output found in the expected/json_schema and expected/bson_schema folders. 

## CURL Examples

### Collection Management Endpoints

#### List Collections
```bash
GET /api/collections
```
Returns all configured collections and their current status.

#### Process All Collections
```bash
POST /api/collections/process
```
Processes all collections that have pending versions.

#### Process Specific Collection
```bash
POST /api/collections/{collection_name}/process
```
Processes a specific collection.

### Schema Rendering Endpoints

#### Render BSON Schema
```bash
GET /api/render/bson_schema/{collection_name}
```
Returns the BSON schema for a collection.

#### Render JSON Schema
```bash
GET /api/render/json_schema/{collection_name}
```
Returns the JSON schema for a collection.

#### Render OpenAPI Specification
```bash
GET /api/render/openapi/{collection_name}
```
Returns the OpenAPI specification for a collection.

### Configuration Endpoints

#### Get Configuration
```bash
GET /api/config
```
Returns the current configuration settings.

#### Health Check
```bash
GET /health
```
Returns the health status of the API.

