# MongoDB Configurator API

This project builds a the [MongoDB Configurator](https://github.com/agile-learning-institute/mongodb_configurator) API. 

## Quick Start

### Prerequisites

- [Python](https://www.python.org/downloads/) 3.8 or later
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

# Set Debug Mode if needed
export LOGGING_LEVEL=DEBUG

# Install dependencies
pipenv install --dev

# Run Unit Tests and generate coverage report
pipenv run test

# Run a backing mongo database
pipenv run database

## All run locally commands assume the database is running
# Start server locally**
pipenv run local

# Start locally with debugging 
pipenv run debug 

# Run locally in Batch mode (process and shut down)
pipenv run batch

# Build container after code changes
pipenv run build

# Start Containerized Stack (Database, API, and SPA)
pipenv run service

# Stop the testing containers
pipenv run down

#####################
# Black Box Testing #

# MongoDB Utilities
pipenv run db-drop-silent   # drop the testing database
pipenv run db-compare       # Compare the database to a know set of data
pipenv run db-harvest       # Update the set of known data from the database

# Run StepCI black box testing 
pipenv run stepci-observability
pipenv run stepci-small
pipenv run stepci-large

# Combine DB actions with Batch testing 
pipenv run db-drop-silent 
pipenv run db-compare                   # Should fail
pipenv run batch 
pipenv run db-compare                   # Should pass

# Combine DB actions, containerized runtime, and StepCI testing 
pipenv run service
pipenv run db-compare                   # Should fail
pipenv run stepci-large
pipenv run db-compare                   # Should pass

# Use the SPA to find errors and test configuration
pipenv run service      # if it's not already running
pipenv run db-compare   # Should fail
# visit http://localhost:8082 and "process all"
pipenv run db-compare   # Should pass

```

## Separation of Concerns
The /configurator directory contains source code.
```
configurator/
├── models/                     # Core processing models
│   ├── database_model.py          # Configuration Database
│   ├── configuration_model.py     # Collection Configuration
│   ├── property_model.py          # Schema Property
│   ├── enumerators_model.py       # Schema Enumerators
│   ├── type_model.py              # Schema Type
│   ├── event_model.py             # Processing or Validation Event
├── routes/                     # Flask HTTP Handlers
│   ├── config_routes.py            # API Config Routes
│   ├── configuration_routes.py     # Configuration Routes
│   ├── data_routes.py              # Test Data Routes
│   ├── dictionary_routes.py        # Dictionary Routes
│   ├── render_routes.py            # Schema Rendering Routes
│   ├── type_routes.py              # Type Routes
├── services/                   # Business Logic and RBAC
│   ├── configuration_services.py   # Configuration Routes
│   ├── data_services.py            # Test Data Routes
│   ├── dictionary_services.py      # Dictionary Routes
│   ├── type_services.py            # Type Routes
├── utils/                      # Utilities
│   ├── config.py                   # API Configuration
│   ├── fileIO.py                   # File IO Wrappers
│   ├── mongoIO.py                  # MongoDB Wrappers
│   ├── version.py                  # Version Number utility
├── server.py                   # Application Entrypoint
```

## Testing
The `tests/` directory contains python unit tests, stepci black box, and testing data.
```
tests/
├── test_server.py      # Server.py unit tests
├── models/             # Model class unit tests
├── routes/             # Route class unit tests
├── services/           # Service layer unit tests
├── utils/              # Utility unit tests
├── stepci/             # API Black Box testing
├── test_cases/         # Test data 
│   ├── small_sample/   # Simple test configuration
│   ├── large_sample/   # Complex test configuration
│   ├── empty_input/    # Load Error testing
│   ├── .../            # Additional test cases
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
# Configuration Management
curl -X GET http://localhost:8081/api/configurations/                    # List all configurations
curl -X GET http://localhost:8081/api/configurations/{file_name}/        # Get specific configuration
curl -X PUT http://localhost:8081/api/configurations/{file_name}/        # Save configuration
curl -X POST http://localhost:8081/api/configurations/                   # Process all configurations
curl -X POST http://localhost:8081/api/configurations/{file_name}/       # Process specific configuration
curl -X PATCH http://localhost:8081/api/configurations/                  # Clean all configurations
curl -X DELETE http://localhost:8081/api/configurations/{file_name}/     # Delete configuration
curl -X PATCH http://localhost:8081/api/configurations/{file_name}/      # Lock/Unlock configuration

# Dictionary Management
curl -X GET http://localhost:8081/api/dictionaries/                      # List all dictionaries
curl -X GET http://localhost:8081/api/dictionaries/{file_name}/          # Get specific dictionary
curl -X PUT http://localhost:8081/api/dictionaries/{file_name}/          # Save dictionary
curl -X PATCH http://localhost:8081/api/dictionaries/                    # Clean all dictionaries
curl -X DELETE http://localhost:8081/api/dictionaries/{file_name}/       # Delete dictionary
curl -X PATCH http://localhost:8081/api/dictionaries/{file_name}/        # Lock/Unlock dictionary

# Type Management
curl -X GET http://localhost:8081/api/types/                             # List all types
curl -X GET http://localhost:8081/api/types/{file_name}/                 # Get specific type
curl -X PUT http://localhost:8081/api/types/{file_name}/                 # Save type
curl -X PATCH http://localhost:8081/api/types/                           # Clean all types
curl -X DELETE http://localhost:8081/api/types/{file_name}/              # Delete type
curl -X PATCH http://localhost:8081/api/types/{file_name}/               # Lock/Unlock type

# Enumerator Management
curl -X GET http://localhost:8081/api/enumerators/                       # Get all enumerators
curl -X PUT http://localhost:8081/api/enumerators/                       # Save enumerators
curl -X PATCH http://localhost:8081/api/enumerators/                     # Clean enumerators

# Test Data Management
curl -X GET http://localhost:8081/api/test_data/                         # List all test data files
curl -X GET http://localhost:8081/api/test_data/{file_name}/             # Get specific test data file
curl -X PUT http://localhost:8081/api/test_data/{file_name}/             # Save test data file
curl -X DELETE http://localhost:8081/api/test_data/{file_name}/          # Delete test data file
curl -X PATCH http://localhost:8081/api/test_data/{file_name}/           # Lock/Unlock test data file

# Schema Rendering
curl -X GET http://localhost:8081/api/configurations/json_schema/{file_name}/{version_number}/  # Get JSON schema
curl -X GET http://localhost:8081/api/configurations/bson_schema/{file_name}/{version_number}/  # Get BSON schema

# System Management
curl -X GET http://localhost:8081/api/config/                            # Get current configuration
curl -X GET http://localhost:8081/api/health                             # Health check
curl -X DELETE http://localhost:8081/api/database/                       # Drop database
```
