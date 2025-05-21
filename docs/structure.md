# Data Directory Structure

The stage0_mongodb_api service expects a specific directory structure in the input folder. This structure organizes collection configurations, type definitions, and data files.

## Directory Layout

```
input_folder
├── collections/
│   ├── user.yaml
│   ├── organization.yaml
│   └── ...
├── dictionary/
│   ├── types/
│   │   ├── word.yaml
│   │   ├── sentence.yaml
│   │   └── ...
│   ├── user.1.0.0.yaml        
│   ├── user.1.0.1.yaml        
│   └── organization.1.0.0.yaml        
└── data/
    ├── enumerators.yaml        
    ├── users.yaml        
    └── organizations.yaml        
```

## Directory Contents

### collections/
Contains the main collection configuration files. Each file defines:
- Collection name
- Version history
- Index configurations
- Migration steps

### dictionary/
Contains type definitions and schema versions:

#### types/
Custom type definitions that can be used in schemas:
- Primitive types (word, sentence, etc.)
- Complex types (breadcrumb, etc.)
- Each type includes validation rules

#### Version Files
Schema definitions for specific versions:
- Named as `{collection}.{version}.yaml`
- Contains the schema for that version
- References enumerator versions

### data/
Contains data files:
- `enumerators.yaml`: Valid values for enum types
- Collection-specific data files
- Test data for different versions

## File Naming Conventions

- Collection configs: `{collection}.yaml`
- Schema versions: `{collection}.{version}.yaml`
- Type definitions: `{type}.yaml`
- Data files: `{collection}.yaml` or `{collection}.{version}.yaml` 

## Related Documentation
- [Collection Configuration](collection_config.md)
- [Custom Types](types.md)
- [Enumerators](enumerators.md) 