# stage0_mongodb_api

This project builds a Utility Container that implements index, schema, and migration management services for a MongoDB database. 
Schemas are described using the [stage0 Simple Schema]() standard. 

## Quick Start for Users

- Read about [Simple Schema](https://github.com/agile-learning-institute/stage0/blob/main/SIMPLE_SCHEMA.md) to understand the Schema Language
- Read the [Reference](./REFERENCE.md) that describes how the utility works. 
- Use the [Template](https://github.com/agile-learning-institute/stage0_template_mongodb_api) to create your system mongodb_api 

## Quick Start for Contributors

### Prerequisites

- [Python](https://www.python.org/downloads/) 3.8 or later
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)
- [Stage0 Developers Edition](https://github.com/agile-learning-institute/stage0/tree/main/developer_edition)

### Setup

```bash
# Install dependencies
pipenv install

# Run tests to verify setup
pipenv run test

# Start development server
pipenv run local
```

## Documentation

- **[Reference](./REFERENCE.md)** - Detailed technical reference for users
- **[Contributing](./CONTRIBUTING.md)** - Development guidelines and architecture
- **[API Standards](https://github.com/agile-learning-institute/stage0/blob/main/developer_edition/docs/api-standards.md)** - Stage0 API standards
- **[Collection Config Schema](./docs/collection_config_schema.yaml)** - Configuration file specification

