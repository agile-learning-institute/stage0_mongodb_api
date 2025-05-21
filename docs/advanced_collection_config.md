# Advanced Collection Configuration

This guide covers advanced collection configuration scenarios including data migrations, complex indexes, and test data management.

## Data Migrations

### Aggregation Pipelines
Aggregation pipelines are used for data migrations:
- Each pipeline is an array of MongoDB aggregation stages
- Stages are executed in order
- Common stages include:
  - `$match`: Filter documents
  - `$addFields`: Add or modify fields
  - `$merge`: Write results back to the collection

### Example Migration
```yaml
name: users
versions:
  - version: "1.0.1.0"
    aggregations:
      - - $match:
            name:
              $ne: VERSION
        - $addFields:
            fullName:
              firstName:
                $arrayElemAt:
                  - $split:
                      - $userName
                      - " "
                  - 0
              lastName:
                $arrayElemAt:
                  - $split:
                      - $userName
                      - " "
                  - 1
        - $merge:
            into: users
            on: _id
            whenMatched: replace
            whenNotMatched: discard
```

## Complex Index Configurations

### Text Indexes
```yaml
addIndexes:
  - name: contentSearch
    key:
      title: "text"
      description: "text"
    options:
      weights:
        title: 10
        description: 5
      default_language: "english"
```

### Compound Indexes
```yaml
addIndexes:
  - name: userStatus
    key:
      status: 1
      lastLogin: -1
      email: 1
    options:
      unique: true
      sparse: true
```

## Test Data Management

### Version-Specific Test Data
```yaml
versions:
  - version: "1.0.0.1"
    testData: users-1.0.0.1
  - version: "1.0.0.2"
    testData: users-1.0.0.2
```

### Test Data Structure
Test data files should match the schema version they're associated with. See [Schema Language](schema.md) for details.

## Multiple Version Updates

### Sequential Updates
```yaml
versions:
  - version: "1.0.0.1"
    addIndexes:
      - name: emailIndex
        key:
          email: 1
        options:
          unique: true
  - version: "1.0.0.2"
    addIndexes:
      - name: nameIndex
        key:
          lastName: 1
          firstName: 1
    dropIndexes:
      - oldNameIndex
  - version: "1.0.1.0"
    aggregations:
      - - $match: { status: "active" }
        - $set: { status: "ACTIVE" }
```

## Best Practices

1. **Version Management**
   - Increment versions appropriately
   - Document version changes
   - Test migrations thoroughly

2. **Data Safety**
   - Backup data before migrations
   - Validate data after changes
   - Monitor migration progress

3. **Performance**
   - Use appropriate indexes
   - Schedule large migrations
   - Monitor resource usage

## Related Documentation
- [Collection Configuration](collection_config.md)
- [Schema Language](schema.md)
- [Index Management](indexes.md)
- [Migration Guide](migrations.md) 