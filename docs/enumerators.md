# Enumerators

Enumerators in the stage0_mongodb_api service provide a way to define and version sets of valid values for enum types. They are stored in the `data/enumerators.yaml` file and referenced in collection schemas.

## Enumerator Format

```yaml
title: Enumerators
description: Valid values for enum types
type: array
items:
  type: object
  properties:
    version:
      type: count
      description: Version number of this enumerator set
    enumerators:
      type: object
      description: Map of enumerator names to their values
      additionalProperties:
        type: object
        description: Map of enum values to their descriptions
        additionalProperties:
          type: sentence
          description: Description of the enum value
```

## Example Enumerators

```yaml
- name: Enumerations
  status: Active
  version: 3
  enumerators:
    defaultStatus:
      Draft: Not finalized
      Active: Not deleted
      Archived: Soft delete indicator
    type:
      radio: Select one option
      check: Select multiple options
      text: Enter a text string
    tags:
      User: A User
      Admin: An administrator
      Super: A super user

- name: Enumerations
  status: Deprecated
  version: 0
  enumerators: {}
```

## Using Enumerators

### In Schema Definitions
```yaml
status:
  type: enum
  description: The current status of the item
  enums: [Draft, Active, Archived]
```

### In Collection Versions
The enumerator version is referenced in the collection version number:
- Major version: Significant changes
- Minor version: New features
- Patch version: Bug fixes
- Enumerator version: Schema enum changes

Example: `1.0.0.1` indicates:
- Major version 1
- Minor version 0
- Patch version 0
- Enumerator version 1

## Enumerator Versioning

When updating enumerators:
1. Create a new version entry in the enumerators array
2. Set the status to "Active" for the new version
3. Optionally set previous versions to "Deprecated"
4. Update collection schemas to reference new values
5. Process collections to apply the changes

### Version Update Example
```yaml
# Version 1
- name: Enumerations
  status: Active
  version: 1
  enumerators:
    defaultStatus:
      Active: Not Deleted
      Archived: Soft Delete Indicator

# Version 2
- name: Enumerations
  status: Active
  version: 2
  enumerators:
    defaultStatus:
      Draft: Not finalized
      Active: Not deleted
      Archived: Soft delete indicator
```

## Best Practices

1. **Naming**
   - Use clear, descriptive names for enum values
   - Follow a consistent naming convention
   - Use PascalCase for enum values

2. **Documentation**
   - Provide clear descriptions for each value
   - Document when and how to use each value
   - Keep descriptions up to date

3. **Versioning**
   - Create new version entries for changes
   - Mark old versions as Deprecated
   - Maintain backward compatibility when possible
   - Implement migrations to address breaking changes

4. **Validation**
   - Ensure all enum values are valid words
   - Keep descriptions within sentence length limits
   - Validate against schema before deployment

## Related Documentation
- [Schema Language](schema.md)
- [Version Management](versioning.md)
- [Collection Configuration](collection_config.md)
- [Custom Types](types.md)

```json
[
    {
        "name": "Enumerations",
        "status": "Deprecated",
        "version": 0,
        "enumerators": []
    },
    {
        "name": "Enumerations",
        "status": "Active",
        "version": 1,
        "enumerators": {
            "defaultStatus": {
                "Active": "Not Deleted",
                "Archived": "Soft Delete Indicator"
            }
        }
    },
    {
        "name": "Enumerations",
        "status": "Active",
        "version": 2,
        "enumerators": {
            "defaultStatus": {
                "Draft": "Not finalized",
                "Active": "Not deleted",
                "Archived": "Soft delete indicator"
            }
        }
    },
    {
        "name": "Enumerations",
        "status": "Active",
        "version": 3,
        "enumerators": {
            "defaultStatus": {
                "Draft": "Not finalized",
                "Active": "Not deleted",
                "Archived": "Soft delete indicator"
            },
            "type": {
                "radio": "Select one option",
                "check": "Select multiple options",
                "text": "Enter a text string"
            },
            "tags": {
                "User": "A User",
                "Admin": "An administrator",
                "Super": "A super user"
            }
        }
    }
]
```
