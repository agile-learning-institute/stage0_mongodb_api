# Collection Configuration

Each collection configuration file defines the version history and migration steps for a MongoDB collection. The configuration follows the schema defined in [collection_config_schema.yaml](./schemas/collection_config_schema.yaml).

## Basic Example

```yaml
name: users
versions:
  - version: "1.0.0.1"
    testData: users-1.0.0.1
    addIndexes:
      - name: emailIndex
        key:
          email: 1
        options:
          unique: true

  - version: "1.0.0.2"
    testData: users-1.0.0.2
    addIndexes:
      - name: nameIndex
        key:
          lastName: 1
          firstName: 1
```

## Configuration Components

### Version Configuration
Each version configuration can include:
- `version`: The version number in major.minor.patch.schema format
- `testData`: Name of the test data file for this version
- `addIndexes`: List of indexes to create
- `dropIndexes`: List of indexes to remove
- `aggregations`: List of MongoDB aggregation pipelines to run for data migration

### Index Configuration
Index configurations specify:
- `name`: Unique name for the index
- `key`: Field(s) to index and their sort order (1 for ascending, -1 for descending)
- `options`: Additional MongoDB index options (unique, sparse, etc.)

For detailed MongoDB index specifications, see the [MongoDB Index Types](https://www.mongodb.com/docs/manual/indexes/) documentation.

## Processing Order

When processing a collection:
1. Versions are processed in chronological order
2. For each version:
   - Drop schema validation
   - Drop specified indexes
   - Run aggregation pipelines
   - Create new indexes
   - Add schema validation
   - Update the collection version

## Advanced Configuration

For more complex configurations including:
- Data migrations using aggregation pipelines
- Complex index configurations
- Multiple version updates
- Test data management

See [Advanced Collection Configuration](advanced_collection_config.md).

## Related Documentation
- [Version Management](versioning.md)
- [Index Management](indexes.md)
- [Collection Config Schema](./schemas/collection_config_schema.yaml) 