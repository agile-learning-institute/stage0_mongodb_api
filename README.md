# stage0_mongodb_api

This API implements index, schema, and migration management services for a MongoDB database. 
Schemas are described using the [stage0 Simple Schema](https://github.com/agile-learning-institute/stage0/blob/main/SIMPLE_SCHEMA.md) standard. 

## Architecture Overview

The API is built around a modular manager system that provides clear separation of concerns:

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

## Prerequisites

- [Python](https://www.python.org/downloads/) 3.8 or later
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)
- [MongoDB](https://www.mongodb.com/try/download/community) or MongoDB Atlas account

### Optional

- [Mongo Compass](https://www.mongodb.com/try/download/compass) - MongoDB GUI client
- [Docker](https://www.docker.com/products/docker-desktop) - For containerized deployment

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/agile-learning-institute/stage0_mongodb_api.git
cd stage0_mongodb_api
```

2. Install dependencies:
```bash
pipenv install
```

3. Configure environment variables:
```bash
export MONGO_DB_NAME=your_database
export MONGO_CONNECTION_STRING=your_connection_string
export INPUT_FOLDER=path/to/configs
export AUTO_PROCESS=true
export EXIT_AFTER_PROCESSING=false
```

4. Run the API:
```bash
# Start API server
pipenv run local

# Start with custom input folder
INPUT_FOLDER=./tests/test_cases/small_sample pipenv run local

# Run in debug mode
pipenv run debug

# Process all collections and exit (batch mode)
pipenv run batch
```

## Configuration

The API is configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_DB_NAME` | MongoDB database name | `stage0` |
| `MONGO_CONNECTION_STRING` | MongoDB connection string | `mongodb://root:example@localhost:27017/?tls=false&directConnection=true` |
| `INPUT_FOLDER` | Directory containing configurations | `./stage0_input` |
| `AUTO_PROCESS` | Process configurations on startup | `false` |
| `EXIT_AFTER_PROCESSING` | Exit after processing or expose API | `false` |
| `LOGGING_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

## API Usage

The API provides endpoints for managing MongoDB collections, including:
- Collection configuration management
- Schema validation and application
- Index creation and deletion
- Data migrations via aggregation pipelines
- Version tracking and processing

For detailed API examples, see [CURL_EXAMPLES.md](./docs/CURL_EXAMPLES.md).
For detailed usage information see [REFERENCE.md](./docs/REFERENCE.md).

## Development Workflow

### Running Tests
```bash
pipenv run test
```

### API Testing with StepCI
```bash
pipenv run stepci
pipenv run load  # Load testing
```

### Container Deployment
```bash
pipenv run build
pipenv run container
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines and workflow.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 