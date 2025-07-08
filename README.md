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

## API Documentation

The complete API documentation with interactive testing is available at:
- **Swagger UI**: http://localhost:8081/docs/ (when server is running)
- **OpenAPI Spec**: http://localhost:8081/docs/openapi.yaml

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

For complete API documentation and interactive testing, serve the Swagger UI at from /docs/index.html

## Migration Refactor Progress

**Status**: In Progress  
**Goal**: Move MongoDB aggregation pipelines from inline YAML to separate JSON files to solve `$` prefix issues

### ✅ Completed Steps

1. **New Folder Structure** - Created migrations folder structure
2. **Migration JSON Files** - Created initial migration files:
   - `tests/test_cases/large_sample/migrations/user_merge_name_fields.json`
   - `tests/test_cases/large_sample/migrations/content_merge_content_fields.json`
3. **Config Updates** - Added MIGRATIONS_FOLDER and API_CONFIG_FOLDER configurations
4. **MongoIO Updates** - Added migration file loading with `bson.json_util.loads()`:
   - `load_migration_pipeline()` - Loads JSON files with proper $ prefix handling
   - `execute_migration_from_file()` - Executes migrations from JSON files

### ✅ Completed Steps

1. **New Folder Structure** - Created migrations folder structure
2. **Migration JSON Files** - Created initial migration files:
   - `tests/test_cases/large_sample/migrations/user_merge_name_fields.json`
   - `tests/test_cases/large_sample/migrations/content_merge_content_fields.json`
3. **Config Updates** - Added MIGRATIONS_FOLDER and API_CONFIG_FOLDER configurations
4. **MongoIO Updates** - Added migration file loading with `bson.json_util.loads()`:
   - `load_migration_pipeline()` - Loads JSON files with proper $ prefix handling
   - `execute_migration_from_file()` - Executes migrations from JSON files
5. **Configuration Format Changes** - Updated YAML to use file references:
   - Updated `user.yaml` and `content.yaml` to use `file:` instead of `pipeline:`
   - Added backward compatibility for legacy `pipeline:` format
   - Added validation for migration format

### ✅ Completed Steps

1. **New Folder Structure** - Created migrations folder structure
2. **Migration JSON Files** - Created initial migration files:
   - `tests/test_cases/large_sample/migrations/user_merge_name_fields.json`
   - `tests/test_cases/large_sample/migrations/content_merge_content_fields.json`
3. **Config Updates** - Added MIGRATIONS_FOLDER and API_CONFIG_FOLDER configurations
4. **MongoIO Updates** - Added migration file loading with `bson.json_util.loads()`:
   - `load_migration_pipeline()` - Loads JSON files with proper $ prefix handling
   - `execute_migration_from_file()` - Executes migrations from JSON files
5. **Configuration Format Changes** - Updated YAML to use file references:
   - Updated `user.yaml` and `content.yaml` to use `file:` instead of `pipeline:`
   - Added backward compatibility for legacy `pipeline:` format
   - Added validation for migration format
6. **API Routes** - Added `/api/migrations` endpoints:
   - `GET /api/migrations/` - List all migration files
   - `GET /api/migrations/{filename}/` - Get specific migration
   - `DELETE /api/migrations/{filename}/` - Delete migration
   - `DELETE /api/migrations/` - Clean all migrations

### 🔄 In Progress

7. **File Structure Changes** - Move config files to `api_config/`

### 📋 Remaining Steps

5. **Configuration Format Changes** - Update YAML to use file references
6. **API Routes** - Add `/api/migrations` endpoints
7. **File Structure Changes** - Move config files to `api_config/`
8. **Testing Updates** - Update all tests to use new format
9. **Documentation Updates** - Update API and configuration docs

### 🎯 Benefits

- ✅ Solves the `$` prefix issue completely
- ✅ Better separation of concerns (config vs. migrations)
- ✅ More maintainable migration pipelines
- ✅ Proper API for migration management
- ✅ Consistent with existing Extended JSON handling


