# stage0_mongodb_api Reference

This document provides detailed technical reference information for using the stage0_mongodb_api service. This service implements the [stage0 simple schema](https://github.com/agile-learning-institute/stage0/blob/main/SIMPLE_SCHEMA.md) standard for mongodb configuration purposes.

## INPUT_FOLDER Structure

The `INPUT_FOLDER` contains the configuration files that define your MongoDB collections, schemas, and data structures. The folder structure follows this pattern:

```
INPUT_FOLDER/
├── collections/           # Collection configuration files (.yaml)
│   ├── user.yaml
│   ├── organization.yaml
│   └── media.yaml
├── data/                 # Data files (.json)
│   ├── enumerators.json  # Enumeration definitions
│   └── user.1.0.0.1.json # Test Data 
└── dictionary/           # Simple Schema definitions
    ├── types/            # Primitive type definitions
    │   ├── word.yaml
    │   ├── sentence.yaml
    │   └── identity.yaml
    ├── user.1.0.0.yaml   # Collection schema versions
    ├── organization.1.0.0.yaml
    └── media.1.0.0.yaml
```

### Collection Configuration Files

Each `.yaml` file in the `collections/` directory defines a MongoDB collection with its versioning strategy. The configuration specifies:
- Collection name and description
- Version definitions with schema references
- Index management (add/drop operations)
- Data migration pipelines
- Schema validation rules

## Collection Configuration Schema

The [collection configuration schema](./docs/collection_config_schema.yaml) defines the structure for collection configuration files. Key elements include:

- **name**: Collection identifier
- **versions**: Array of version configurations
  - **version**: Version string (e.g., "1.0.0.1")
  - **schema**: Reference to schema definition file
  - **add_indexes**: Indexes to create
  - **drop_indexes**: Indexes to remove
  - **aggregations**: Data migration pipelines

## Versioning Scheme

The API uses a four-component versioning scheme: `major.minor.patch.enumerator`

- **Major**: Breaking changes to schema structure
- **Minor**: Backward-compatible feature additions
- **Patch**: Bug fixes and minor improvements
- **Enumerator**: Sequential number for multiple changes at same version

Examples:
- `1.0.0.1` - First version of a collection
- `1.2.3.4` - Version 1.2.3 with version 4 enumerators
- `2.0.0.4` - Major version upgrade, with v4 enumerators

## Schema Processing

The API processes collection configurations to manage MongoDB schemas, indexes, and data migrations. "Processing" a collection involves, first determining if the schema version in the collection configuration is greater than the current version, and if so then:
- Removing any existing schema validation
- Remove specified indexes (optional)
- Run defined migrations (optional)
- Add any new indexes (optional)
- Apply new Schema Validation
- Load Test Data (optional)

## Configuration Reference

The API is configured through environment variables.

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_API_PORT` | API Port number | `8081` |
| `MONGO_DB_NAME` | MongoDB database name | `stage0` |
| `MONGO_CONNECTION_STRING` | MongoDB connection string | `mongodb://root:example@localhost:27017/?tls=false&directConnection=true` |
| `VERSION_COLLECTION_NAME`| MongoDB Version Collection name | `CollectionVersions` |
| `INPUT_FOLDER` | Directory containing configurations | `/input` |
| `LOAD_TEST_DATA` | Load Test data during processing | `false` |
| `AUTO_PROCESS` | Process configurations on startup | `false` |
| `EXIT_AFTER_PROCESSING` | Exit after processing | `false` |
| `LOGGING_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

