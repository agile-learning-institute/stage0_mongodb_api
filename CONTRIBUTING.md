# Contributing to stage0_mongodb_api

This document provides information for developers contributing to the stage0_mongodb_api project.

## Development Standards

This project follows the [Stage0 development standards](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/contributing.md) and implements [API standards](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/api-standards.md) for consistency across the platform. The service is designed with [configurability](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/service-configurability.md) and [observability](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/service-observability.md) in mind.

## Separation of Concerns

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

- Stage0 [Developers Edition](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/README.md)

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
export INPUT_FOLDER=./tests/test_cases/large_sample

# Set Debug Mode
export LOGGING_LEVEL=DEBUG

# Change the testing database name
export MONGO_DB_NAME=test_database

# Start API server (starts MongoDB container first)
pipenv run start

# Start API server if database is already running
pipenv run local

# Start with debugging
pipenv run debug

# Run in Batch mode (process and shut down)
pipenv run batch

#####################
# Black Box Testing #

# Silent drop MONGO_DB_NAME for automation
pipenv run db-drop-silent

# Compare with INPUT_FOLDER/MONGO_DB_NAME
pipenv run db-compare

# Harvest current state to INPUT_FOLDER/MONGO_DB_NAME
pipenv run db-harvest

# Run StepCI black box testing 
pipenv run stepci_observability
pipenv run stepci_small_sample
pipenv run stepci_large_sample

# Combine DB actions with StepCI testing - see test_cases small & large
pipenv run db-drop-silent && pipenv run stepci_observability && pipenv run db-compare

# Build the API Docker Image
pipenv run build

# Build & run the API Docker Container
pipenv run container
```

## Testing

### Test Structure

The `tests/` directory contains python unit tests, stepci black box, and testing data.

```
tests/
├── test_server.py     # Server.py unit tests
├── managers/          # Manager class unit tests
├── routes/            # Route class unit tests
├── services/          # Service layer unit tests
├── test_cases/        # Test data 
│   ├── small_sample/  # Simple test configuration
│   ├── large_sample/  # Complex test configuration
│   ├── empty_input/   # Load Error testing
│   ├── .../           # Additional test cases
```
 
### Test Cases

The `tests/test_cases/` directory contains test scenarios:

- **small_sample**: Minimal configuration with one collection for basic functionality testing
- **large_sample**: Complex multi-collection setup with relationships and advanced features
- **validation_errors**: Test cases for error handling and validation scenarios
- **minimum_valid**: Empty configuration for edge case testing
If you need a new set of test data to validate features you are adding, feel free to add a new test case folder. Take note of these unit tests that use the test data. 

### Load and Validation Errors
 Load and validation unit testing leverages test cases with known errors. Assertions validate that the errors were thrown using the unique identifier thrown in the code. If you introduce new testing, make sure you add new unique identifiers here.

### Rendering Tests
 Rendering tests for both the small_sample and large_sample test cases is done using the expected output found in the `tests/test_cases/{case}/expected/json_schema` and `expected/bson_schema` folders. If your new test case needs to include rendering tests, you can add the expected output there and extend the rendering unit tests.

## CURL Examples

```bash
# Get Configuration
curl -X GET http://localhost:8582/api/config

# Health Check
curl -X GET http://localhost:8582/health

# List Collections
curl -X GET http://localhost:8582/api/collections/

# Get a Collection Config
curl -X GET http://localhost:8582/api/collections/{collection_name}

# Process All Collections
curl -X POST http://localhost:8582/api/collections/

# Process Specific Collection
curl -X POST http://localhost:8582/api/collections/{collection_name}

# Render BSON Schema
curl -X GET http://localhost:8582/api/render/bson_schema/{version_name}

# Render JSON Schema
curl -X GET http://localhost:8582/api/render/json_schema/{version_name}

# Render OpenAPI Specification
curl -X GET http://localhost:8582/api/render/openapi/{version_name}

```

