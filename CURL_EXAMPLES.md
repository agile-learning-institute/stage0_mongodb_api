# Testing with ``curl``

This document provides examples for testing the MongoDB Schema Management API endpoints.

## Collection Management

### List all configured collections
```sh
curl http://localhost:8580/api/collections
```

### Process all configured collections
```sh
curl -X POST http://localhost:8580/api/collections
```

### Get collection configuration by name
```sh
curl http://localhost:8580/api/collection/sample
```

### Process a specific collection
```sh
curl -X POST http://localhost:8580/api/collection/sample
```

## Configuration

### Get current configuration
```sh
curl http://localhost:8580/api/config
```

### Health check (Prometheus metrics)
```sh
curl http://localhost:8580/api/health
```

## Example Collection Configuration

Here's an example of a collection configuration that can be processed:

```json
{
  "name": "sample",
  "versions": [
    {
      "version": "1.0.0.0",
      "testData": "sample-1.0.0.1",
      "dropIndexes": ["oldIndex"],
      "migrations": [
        [
          {"$addFields": {"name": {"$concat": ["$firstName", " ", "$lastName"]}}},
          {"$merge": {"into": "sample","on": "_id","whenMatched": "replace","whenNotMatched": "discard"}}
        ],
        [
          {"$unset": ["firstName", "lastName"]},
          {"$merge": {"into": "sample","on": "_id","whenMatched": "replace","whenNotMatched": "discard"}}
        ]
      ],
      "addIndexes": [
        {
          "name": "nameIndex",
          "keys": { "userName": 1 },
          "options": { "unique": true }
        },
        {
          "name": "typeIndex",
          "keys": { "type": 1 },
          "options": { "unique": false }
        }
      ]
    }
  ]
}
```
