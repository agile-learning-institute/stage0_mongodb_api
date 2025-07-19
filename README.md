# MongoDB Configurator API

This project builds a the [MongoDB Configurator](https://github.com/agile-learning-institute/mongodb_configurator) API. This API supports the [MongoDB Configurator SPA](https://github.com/agile-learning-institute/mongodb_configurator_spa)

## Quick Start

### Prerequisites

- [Python](https://www.python.org/downloads/) 3.12 or later
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)
- [StepCI](https://github.com/stepci/stepci/blob/main/README.md)
- [Docker Desktop](https://github.com/agile-learning-institute/stage0/tree/main/developer_edition)
- [MongoDB Compass](https://www.mongodb.com/products/compass) *optional*

### Quick Start
```bash
# Clone the repository
git clone git@github.com:agile-learning-institute/mongodb_configurator_api.git
cd mongodb_configurator_api
pipenv run service
# Open http://localhost:8082/
```

### Developer Setup
```bash
# Install dependencies
pipenv install

# Run tests to verify setup
pipenv run test

```

### Developer Commands

```bash
# Select a test_case for the server
export INPUT_FOLDER=./tests/test_cases/small_sample
export INPUT_FOLDER=./tests/test_cases/large_sample
export INPUT_FOLDER=./tests/test_cases/playground

# Set Debug Mode if needed
export LOGGING_LEVEL=DEBUG

# Install dependencies
pipenv install --dev

#####################
# Running test server  - uses INPUT_FOLDER setting# 
pipenv run database     # Start the backing mongo database
pipenv run local        # Start the server locally
pipenv run debug        # Start locally with DEBUG logging
pipenv run batch        # Run locally in Batch mode (process and exit)

# Drop the Testing Database - Live - Real Drop Database!!!
pipenv run drop

#####################
# Building and Testing the container (before a PR)
pipenv run container    # Build the container
pipenv run service      # Run the DB, API, and SPA containers
# visit http://localhost:8082 and "process all"

pipenv run down         # Stops all testing containers

################################
# Black Box Testing with StepCI 
export INPUT_FOLDER=./tests/test_cases/stepci
pipenv run stepci

```

## Separation of Concerns
The /configurator directory contains source code.
```
configurator/
├── routes/                     # Flask HTTP Handlers
│   ├── config_routes.py            # API Config Routes
│   ├── configuration_routes.py     # Configuration Routes
│   ├── database_routes.py          # Database Routes
│   ├── dictionary_routes.py        # Dictionary Routes
│   ├── enumerator_routes.py        # Enumerator Routes
│   ├── migration_routes.py         # Migration Routes
│   ├── test_data_routes.py         # Test Data Routes
│   ├── type_routes.py              # Type Routes
├── services/                   # Processing, Rendering Models
│   ├── configuration_services.py   # Configuration Services
│   ├── dictionary_services.py      # Dictionary Services
│   ├── enumerator_service.py       # Enumerator Services
│   ├── template_service.py         # Template Services
│   ├── type_services.py            # Type Services
├── utils/                      # Utilities
│   ├── config.py                   # API Configuration
│   ├── configurator_exception.py   # Exception Classes
│   ├── ejson_encoder.py            # Extended JSON Encoder
│   ├── file_io.py                  # File IO Wrappers
│   ├── mongo_io.py                 # MongoDB Wrappers
│   ├── route_decorators.py         # Route Decorators
│   ├── version_manager.py          # Version Manager
│   ├── version_number.py           # Version Number utility
├── server.py                   # Application Entrypoint
```

## Testing
The `tests/` directory contains python unit tests, stepci black box, and testing data.
```
tests/
├── test_server.py          # Server.py unit tests
├── integration/            # Integration tests dependent on backing services
├── models/                 # Model class unit tests
├── routes/                 # Route class unit tests
├── services/               # Service layer unit tests
├── utils/                  # Utility unit tests
├── stepci/                 # API Black Box testing
├── test_cases/             # Test data 
│   ├── failing_*/          # Integration Test data for failure use cases
│   ├── failing_refs/           # Circular/Missing Refs, integration/test_refs.py
│   ├── failing_missing/        # Missing folders, integration/test_missing.py
│   ├── failing_unparsable/     # Non yaml/json files, integration/test_unparsable.py
│   ├── failing_validation/     # Missing required, integration/test_validation.py
│   ├── passing_*/          # Integration Test data for success use cases
│   ├── passing_complex_refs/   # integration/test_renders.py, integration/test_processing.py
│   ├── passing_config_files/   # integration/test_config_file.py
│   ├── passing_empty/          # integration/test_renders.py, integration/test_processing.py
│   ├── passing_process/        # integration/test_renders.py, integration/test_processing.py
│   ├── passing_type_renders/   # integration/test_type_renders.py
│   ├── playground/         # Playground for SPA - not used in integration testing
│   ├── stepci/             # Configuration for step ci testing - setup/tear down in tests
│   ├── template/           # Template, integration/test_renders.py, integration/test_processing.py

```

## API Documentation

The complete API documentation with interactive testing is available:
- [API Server docs/index.html](http://localhost:8081/docs/index.html) if the API is running
- GoLive on [index.html](./docs/index.html)

The Swagger UI provides:
- Interactive endpoint testing
- Auto-generated curl commands for each endpoint
- Request/response schemas
- Parameter documentation

### Quick API Examples

```bash
# Health check
curl -X GET http://localhost:8081/api/health

# Get current configuration
curl -X GET http://localhost:8081/api/config/

# List all configurations
curl -X GET http://localhost:8081/api/configurations/

# Process all configurations
curl -X POST http://localhost:8081/api/configurations/

# Lock all types
curl -X PATCH http://localhost:8081/api/types/
```
---
