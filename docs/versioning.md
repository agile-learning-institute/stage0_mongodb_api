# Version Management

The stage0_mongodb_api service uses a four-part versioning scheme to track changes to collections and their schemas.

## Version Format

Version numbers follow the format: `major.minor.patch.schema`

- **major**: Major version number for significant changes
- **minor**: Minor version number for new features
- **patch**: Patch version number for bug fixes
- **schema**: Schema version number for schema changes

Example: `1.0.0.1` represents:
- Major version 1
- Minor version 0
- Patch version 0
- Schema version 1

## Version Storage

Versions are stored in the collection specified by the `VERSION_COLLECTION_NAME` environment variable (default: `msmCurrentVersions`). Each document in this collection has the following structure:

```yaml
collection_name: string          # Name of the collection
current_version: string         # Current version (major.minor.patch.schema)
```

## Version Processing

When processing a collection:
1. The service checks the current version in the version collection
2. If no version exists, returns "0.0.0.0"
3. If multiple versions exist, returns "0.0.0.0"
4. Otherwise, returns the current version

## Version Comparison

Versions are compared component by component:
1. Major versions are compared first
2. If equal, minor versions are compared
3. If equal, patch versions are compared
4. If equal, schema versions are compared

Example:
```
1.0.0.1 < 1.0.0.2
1.0.0.1 < 1.1.0.0
1.0.0.1 < 2.0.0.0
```

## Version Updates

When updating a version:
1. The version string must match the format `major.minor.patch.schema`
2. All components must be non-negative integers
3. The version document is upserted with:
   - Collection name
   - Current version

## Related Documentation
- [Collection Configuration](collection_config.md)
- [Processing Guide](processing.md)
- [Configuration Options](config.md) 