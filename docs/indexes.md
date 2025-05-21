# Index Management

This guide explains how to configure indexes in the stage0_mongodb_api service. For detailed information about MongoDB indexes, refer to the [MongoDB Index Documentation](https://www.mongodb.com/docs/manual/indexes/).

## Index Configuration

Indexes are configured in the collection configuration file under the `addIndexes` and `dropIndexes` sections.

```yaml
# Example collection configuration
name: users
versions:
  - version: "1.0.0"
    status: Active
    schema: user.1.0.0.yaml
    addIndexes:
      - name: email_unique
        keys:
          email: 1
        options:
          unique: true
    dropIndexes:
      - name: old_index_name
```

## Index Types

The service supports all MongoDB index types as documented in [MongoDB Index Types](https://www.mongodb.com/docs/manual/core/index-types/):

- Single Field Indexes
- Compound Indexes
- Text Indexes
- Geospatial Indexes
- Hashed Indexes
- TTL Indexes

## Index Options

All MongoDB index options are supported as documented in [MongoDB Index Options](https://www.mongodb.com/docs/manual/reference/method/db.collection.createIndex/#options).

## Index Management

Indexes are managed through the collection configuration file:

1. **Adding Indexes**
   - Define in `addIndexes` section
   - Processed during collection version updates
   - Created in background for large collections

2. **Dropping Indexes**
   - List in `dropIndexes` section
   - Processed during collection version updates
   - Handled before adding new indexes

## Best Practices

For index best practices and performance considerations, refer to:
- [MongoDB Index Best Practices](https://www.mongodb.com/docs/manual/core/index-best-practices/)
- [MongoDB Index Performance](https://www.mongodb.com/docs/manual/core/index-performance/)

## Related Documentation
- [Collection Configuration](collection_config.md)
- [Processing Guide](processing.md)
- [Version Management](versioning.md) 