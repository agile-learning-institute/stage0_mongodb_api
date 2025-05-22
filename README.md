# stage0_mongodb_api

This API implements index, schema, and migration management services for a MongoDB database. Schemas are described using the stage0 Simple Schema standard. 

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
pipenv run local
```

## Configuration

The API is configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_DB_NAME` | MongoDB database name | - |
| `MONGO_CONNECTION_STRING` | MongoDB connection string | - |
| `INPUT_FOLDER` | Directory containing configurations | - |
| `AUTO_PROCESS` | Process configurations on startup | false |
| `EXIT_AFTER_PROCESSING` | Exit after processing or expose API | false |

## API Usage

The API provides endpoints for managing MongoDB collections, including:
- Collection configuration
- Schema management
- Index management
- Data migrations

For detailed API examples, see [CURL_EXAMPLES.md](CURL_EXAMPLES.md).

### Example Collection Configuration
```yaml
name: sample
versions:
  - version: "1.0.0.0"
    testData: "sample-1.0.0.1"
    addIndexes:
      - name: nameIndex
        keys:
          userName: 1
        options:
          unique: true
```

## [Reference Documentation](./docs/REFERENCE.md) - Complete Reference documentation

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines and workflow.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 