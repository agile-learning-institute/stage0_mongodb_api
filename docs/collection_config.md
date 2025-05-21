# Collection Configuration

Each collection configuration file defines the version history and migration steps for a MongoDB collection. The configuration follows this schema:

```yaml
title: Collection Configuration
description: Configuration for a MongoDB collection's version history and migrations
type: object
properties:
  name:
    type: word
    description: The name of the MongoDB collection
  versions:
    type: array
    description: List of version configurations in chronological order
    items:
      type: object
      description: Configuration for a specific version
      properties:
        version:
          type: string
          description: Version string in format major.minor.patch.enums
        testData:
          type: word
          description: Name of the test data file for this version
        addIndexes:
          type: array
          description: List of indexes to add in this version
          items:
            type: object
            description: MongoDB index configuration
            properties:
              name:
                type: word
                description: Name of the index
              key:
                type: object
                description: Index key specification
              options:
                type: object
                description: MongoDB index options
        dropIndexes:
          type: array
          description: List of index names to drop in this version
          items:
            type: word
        aggregations:
          type: array
          description: List of aggregation pipelines to run for this version
          items:
            type: array
            description: MongoDB aggregation pipeline stages
```

## Example Configuration

```yaml
name: sample
versions:
  - version: "1.0.0.1"
    testData: sample-1.0.0.1
    addIndexes:
      - name: nameIndex
        key:
          userName: 1
        options:
          unique: true
      - name: statusIndex
        key:
          status: 1
        options:
          unique: false

  - version: "1.0.0.2"
    testData: sample-1.0.0.2

  - version: "1.0.1.3"
    testData: sample-1.0.1.3
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
            userName:
              $reduce:
                input:
                  $split:
                    - $userName
                    - " "
                initialValue: ""
                in:
                  $concat:
                    - "$$value"
                    - "$$this"
        - $merge:
            into: sample
            on: _id
            whenMatched: replace
            whenNotMatched: discard
    dropIndexes:
      - statusIndex
```

## Configuration Components

### Version Configuration
Each version configuration can include:
- `version`: The version number in major.minor.patch.enums format
- `testData`: Name of the test data file for this version
- `addIndexes`: List of indexes to create
- `dropIndexes`: List of indexes to remove
- `aggregations`: List of MongoDB aggregation pipelines to run for data migration

### Index Configuration
Index configurations specify:
- `name`: Unique name for the index
- `key`: Field(s) to index and their sort order (1 for ascending, -1 for descending)
- `options`: Additional MongoDB index options (unique, sparse, etc.)

### Aggregation Pipeline
Aggregation pipelines are used for data migrations:
- Each pipeline is an array of MongoDB aggregation stages
- Stages are executed in order
- Common stages include:
  - `$match`: Filter documents
  - `$addFields`: Add or modify fields
  - `$merge`: Write results back to the collection

## Processing Order

When processing a collection:
1. Versions are processed in chronological order
2. For each version:
   - Drop specified indexes
   - Run aggregation pipelines
   - Create new indexes
   - Update the collection version

## Related Documentation
- [Version Management](versioning.md)
- [Index Management](indexes.md)
- [Migration Guide](migrations.md) 