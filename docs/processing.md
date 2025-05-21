# Processing Guide

This guide explains how the stage0_mongodb_api service processes collections and handles migrations.

## Processing Modes

The service can operate in two modes:

1. **Auto Process Mode**
   - Triggered on service startup when `AUTO_PROCESS=true`
   - Processes all collections in the input folder
   - Can exit after processing if `EXIT_AFTER_PROCESSING=true`

2. **API Mode**
   - Service exposes REST API endpoints
   - Collections can be processed on demand
   - Supports individual collection processing

## Processing Steps

### 1. Collection Discovery
```yaml
# Example directory structure
input_folder/
  collections/
    user.yaml
    organization.yaml
  dictionary/
    types/
      word.yaml
      sentence.yaml
    user.1.0.0.yaml
    user.1.0.1.yaml
    organization.1.0.0.yaml
  data/
    enumerators.yaml
    users.yaml
    organizations.yaml
```

The service:
- Scans the `collections/` directory for collection configuration files
- Identifies schema versions in `dictionary/` directory
- Validates required files exist:
  - Collection config file (`{collection}.yaml`)
  - Schema version file (`{collection}.{version}.yaml`)
  - Type definitions in `dictionary/types/`
  - Enumerator definitions in `data/enumerators.yaml`

### 2. Version Processing

For each collection:

1. **Version Validation**
   - Validates version numbers
   - Checks version dependencies
   - Ensures backward compatibility

2. **Schema Processing**
   - Loads and validates schema definitions
   - Resolves custom types
   - Validates enumerator references
   - Generates MongoDB validation rules

3. **Index Management**
   - Processes `addIndexes` configurations
   - Handles `dropIndexes` requests
   - Validates index definitions

4. **Data Migration**
   - Executes migration scripts if needed
   - Updates document structures
   - Handles data transformations

### 3. Database Operations

1. **Collection Creation/Update**
   - Creates new collections if needed
   - Updates existing collections
   - Applies schema validation rules

2. **Index Operations**
   - Creates new indexes
   - Drops specified indexes
   - Validates index operations

3. **Data Operations**
   - Applies test data if configured
   - Executes aggregation pipelines
   - Updates document structures

## Related Documentation
- [Collection Configuration](collection_config.md)
- [Schema Language](schema.md)
- [Version Management](versioning.md)
- [Index Management](indexes.md) 
