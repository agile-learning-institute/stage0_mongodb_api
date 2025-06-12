# MongoDB Schema Management Reference

This document provides an overview of the stage0_mongodb_api service, which extends the Simple Schema standard with MongoDB-specific features.

### Core Concepts
- [Stage0 Simple Schema](https://github.com/agile-learning-institute/stage0/blob/main/SIMPLE_SCHEMA.md) - The base schema language and concepts
- [REST API](./openapi.yaml) - OpenAPI documentation

## Stage0 Simple Schema Extensions

### Version Management
The API extends Simple Schema's version-less structures with a four component version:
- `major.minor.patch.schema`
  - First three components follow traditional major/minor/patch semantic versioning
  - Fourth component tracks enumerators version

This extension enables:
- Versioning of dictionaries and enumerators
- Collection-specific schema version tracking
- Version state management in MongoDB
- MongoDB Collection Schema Validation

### Enumerator Support
The API extends Simple Schema's enumerator support with:
- Versioned enumerator definitions
- MongoDB-based enumerator storage
- Collection-specific enumerator version selection

### Collection Processing
The core of collection processing is implementing a new schema validation configuration. 
- See [this article](https://www.mongodb.com/community/forums/t/best-practices-for-schema-management-migrations-and-scaling-in-mongodb/306805) for Mongo schema management best practices
- See [this article](https://www.mongodb.com/blog/post/building-with-patterns-the-schema-versioning-pattern) for schema versioning best practices. 

The API processes collections in the following order:

1. **Version Check**
   - Retrieves current version from MongoDB
   - Compares with target version
   - Proceeds only if version update is needed

2. **Schema Removal**
   - Removes existing schema validation
   - Preserves collection data
   - Prepares for schema update

3. **Index Removal** (Optional)
   - Removes indexes specified in `dropIndexes`
   - Skips if no index changes specified

4. **Data Migration** (Optional)
   - Executes aggregation pipelines in order
   - Applies data transformations
   - Updates documents in place
   - Skips if no migrations specified

5. **Index Creation** (Optional)
   - Creates new indexes specified in `addIndexes`
   - Skips if no index changes specified

6. **Schema Application**
   - Applies new schema validation
   - Updates collection version

7. **Test Data Loading** (Optional)
   - Loads test data if specified in version configuration
   - Only executes if test data loading is enabled
   - Skips if no test data specified

Example processing sequence:
```yaml
# Current version: 1.0.0.1
# Target version: 1.0.0.2

name: users
versions:
  - version: "1.0.0.1"
    addIndexes:
      - name: statusIndex
        key:
          status: 1
  - version: "1.0.0.2"
    # 1. Remove existing schema validation
    # 2. Drop indexes if requested
    dropIndexes:
      - statusIndex
    # 3. Run migrations
    aggregations:
      - - $match:
            status: "pending"
        - $set:
            status: "PENDING"
        - $merge:
            into: users
            on: _id
    # 4. Create new Indexes
    addIndexes:
      - name: statusIndex
        key:
          status: 1
          updatedAt: -1
    # 5. Apply new schema validation v1.0.0.2
    # 6. Load test data (if enabled)
    test_data: users-1.0.0.2
```

Note: Schema validation is always replaced during processing, while index management, migrations, and test data loading are optional steps that only execute if specified in the configuration and enabled in the service settings.

### Collection Configuration
The API uses a [versioned collection configuration file](./collection_config_schema.yaml) to configure collection validation, and indexing. A very simple collection configuration file just list the version numbers. 

```yaml
name: users              # Collection name
versions:                # List of version configurations
  - version: "1.0.0.1"   # (major.minor.patch.enums)
  - version: "1.0.0.2"
  - version: "1.0.1.3"
```

Each version configuration can optionally include:
- `drop_indexes`: Optional list of index names to drop
- `aggregations`: Optional list of aggregation pipelines (see [MongoDB Aggregation](https://www.mongodb.com/docs/manual/aggregation/))
- `add_indexes`: Optional list of indexes to add (see [MongoDB Indexes](https://www.mongodb.com/docs/manual/indexes/))
- `test_data`: Optional name of test data file for this version

### Advanced Configuration
The API supports advanced collection configurations for data migrations and complex indexes:

1. **Data Migrations**
   ```yaml
   versions:
     - version: "1.0.1.0"
       aggregations:
         - - $match:
               status: "active"
           - $set:
               status: "ACTIVE"
           - $merge:
               into: users
               on: _id
               whenMatched: replace
   ```
   See [MongoDB Aggregation Pipeline](https://www.mongodb.com/docs/manual/aggregation/) for available stages and operators.

2. **Complex Indexes**
   ```yaml
   versions:
     - version: "1.0.0.1"
       addIndexes:
         - name: contentSearch
           key:
             title: "text"
             description: "text"
           options:
             weights:
               title: 10
               description: 5
         - name: userStatus
           key:
             status: 1
             lastLogin: -1
             email: 1
           options:
             unique: true
             sparse: true
   ```
   See [MongoDB Index Types](https://www.mongodb.com/docs/manual/indexes/) for available index types and Options

Best Practices:
- Increment versions appropriately
- Backup data before migrations
- Test migrations thoroughly
- Monitor resource usage during large migrations

## Configuration

The service is configured through environment variables:
- `MONGO_DB_NAME`: The name of the MongoDB database
- `MONGO_CONNECTION_STRING`: MongoDB connection string
- `INPUT_FOLDER`: Directory containing schema configurations
- `AUTO_PROCESS`: Set to "true" to process configurations on startup
- `EXIT_AFTER_PROCESSING`: Set to "false" to expose the API after processing

For detailed configuration options, see [Configuration Options](./config.md).

## Quick Start

1. Review the [Simple Schema Documentation](../../stage0/SIMPLE_SCHEMA.md)
2. Set up your input folder structure following Simple Schema conventions
3. Configure your environment variables
4. Run the service to process your collections

## Related Documentation
- [Contributing Guide](./CONTRIBUTING.md) - Development and contribution guidelines
- [Simple Schema Documentation](../../stage0/SIMPLE_SCHEMA.md) - Base schema language
