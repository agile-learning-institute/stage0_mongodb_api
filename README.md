# MongoDB Configurator API

This project builds a the [MongoDB Configurator](https://github.com/agile-learning-institute/mongodb_configurator) API. 

## Quick Start

### Prerequisites

- [Python](https://www.python.org/downloads/) 3.12 or later
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)
- [Docker Desktop](https://github.com/agile-learning-institute/stage0/tree/main/developer_edition)
- [MongoDB Compass]() *optional*

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

# Run Unit Tests and generate coverage report
pipenv run test

# Drop the Testing Database - Live - Real Drop Database!!!
pipenv run drop

#####################
# Running test server  - uses INPUT_FOLDER setting# 
pipenv run database     # Start the backing mongo database
pipenv run local        # Start the server locally
pipenv run debug        # Start locally with DEBUG logging
pipenv run batch        # Run locally in Batch mode (process and exit)

#####################
# Building and Testing the container (before a PR)
pipenv run build        # Build the container
pipenv run service      # Run the DB, API, and SPA containers
# visit http://localhost:8082 and "process all"

pipenv run down         # Stops all testing containers

#####################
# Black Box Testing #
pipenv run stepci-observe   # Observability endpoints
pipenv run stepci-<type>    # [configurations, dictionaries, types, test_data, enumerators]

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
├── models/                 # Model class unit tests
├── routes/                 # Route class unit tests
├── services/               # Service layer unit tests
├── utils/                  # Utility unit tests
├── stepci/                 # API Black Box testing
├── test_cases/             # Test data 
│   ├── small_sample/       # Simple test configuration
│   ├── large_sample/       # Complex test configuration
│   ├── empty_input/        # Load Error testing
│   ├── sample_template/    # Configuration for Template
│   ├── playground/         # Served with Stack for UI testing
│   ├── .../                # Additional test cases
```
the unit tests TestConfigurationIntegration and TestTypeRendering are integration tests that use the input folders in test_cases. 

## API Documentation

The complete API documentation with interactive testing is available:
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

# Clean all types
curl -X PATCH http://localhost:8081/api/types/
```
---
