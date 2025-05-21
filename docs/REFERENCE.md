# MongoDB Schema Management Reference

This document provides an overview of the stage0_mongodb_api service. For detailed documentation, please refer to the following sections:

## Documentation Structure

### Core Concepts
- [Data Directory Structure](structure.md) - Overview of the input folder organization
- [Version Management](versioning.md) - Details about version numbering and management
- [Schema Language](schema.md) - Documentation of the Simple Schema language

### Configuration
- [Collection Configuration](collection_config.md) - How to configure collections and versions
- [Custom Types](types.md) - Available custom types and how to create new ones
- [Enumerators](enumerators.md) - Working with enumerator types and values

### Processing
- [Processing Guide](processing.md) - How the service processes collections
- [Migration Guide](migrations.md) - Creating and running migrations
- [Index Management](indexes.md) - Managing database indexes

### API Reference
- [REST API](./openapi.yaml) - OpenAPI documentation
- [Configuration Options](config.md) - Environment variables and settings

## Quick Start
NOTE: Future update to use a template repo and containerized API/UI

1. Set up your input folder structure as described in [Data Directory Structure](structure.md)
2. Configure your collections using the [Collection Configuration](collection_config.md) format
3. Define your schemas using the [Schema Language](schema.md)
4. Set environment variables as documented in [Configuration Options](config.md)
5. Run the service to process your collections

## Environment Variables

The service is configured through environment variables:
- `MONGO_DB_NAME`: The name of the MongoDB database
- `MONGO_CONNECTION_STRING`: MongoDB connection string
- `INPUT_FOLDER`: Directory containing schema configurations
- `AUTO_PROCESS`: Set to "true" to process configurations on startup
- `EXIT_AFTER_PROCESSING`: Set to "false" to expose the API after processing

For detailed configuration options, see [Configuration Options](config.md).
