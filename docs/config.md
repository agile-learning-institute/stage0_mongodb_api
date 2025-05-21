# Configuration Options

This guide details the configuration options available for the stage0_mongodb_api service. All variables have default values and can be overridden through environment variables or configuration files.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_DB_NAME` | MongoDB database name | stage0 |
| `MONGO_CONNECTION_STRING` | MongoDB connection string | mongodb://root:example@localhost:27017/?tls=false&directConnection=true |
| `INPUT_FOLDER` | Input directory path | /input |
| `OUTPUT_FOLDER` | Output directory path | /output |
| `CONFIG_FOLDER` | Configuration directory | ./ |
| `LOGGING_LEVEL` | Logging level | INFO |
| `ACTIVE_STATUS` | Active status value | active |
| `ARCHIVED_STATUS` | Archived status value | archived |
| `PENDING_STATUS` | Pending status value | pending |
| `COMPLETED_STATUS` | Completed status value | complete |
| `LATEST_VERSION` | Latest version identifier | latest |
| `VERSION_COLLECTION_NAME` | MongoDB collection for version tracking | msmCurrentVersions |

## Configuration Sources

Configuration values are loaded in the following order:
1. Configuration file in `CONFIG_FOLDER`
2. Environment variable
3. Default value

## Related Documentation
- [Processing Guide](processing.md)
- [Collection Configuration](collection_config.md)
- [REST API](./openapi.yaml) 