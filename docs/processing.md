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
- Validate that enumerators definitions exist at in `data/enumerators.yaml`
- Validates that schema's referenced in the collections yaml file exist
- Validates that test data referenced in the collections yaml file exist
- Validate that all `dictionary/` 's resolve to primitives, and verify any used enumerators exist

### 2. Version Processing

For each collection, the service processes versions in chronological order to bring the collection to the latest version. The process follows these steps:

1. Get the current version from the database (returns "0.0.0.0" if no version exists)
2. For each version in the configuration:
   - Compare version number with current version
   - If version number is greater than current version:
     a. Process the version configuration
     b. Update the current version in the database
   - If version number is less than or equal to current version:
     - Skip processing this version

When processing a version configuration, the following steps are completed in order:

1. **Drop existing Schema Validation** (Required)
2. **Drop any Indexes listed in drop_indexes** (Optional)
3. **Execute Aggregation Pipelines if provided** (Optional)
4. **Add Indexes listed in add_indexes** (Optional)
5. **Apply Schema Validation** (Required)
6. **Update Current Version** (Required)

## Related Documentation
- [Collection Configuration](collection_config.md)
- [Schema Language](schema.md)
- [Version Management](versioning.md)
- [Index Management](indexes.md) 
