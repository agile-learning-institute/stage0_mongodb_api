# Data Directory Structure

The stage0_mongodb_api service expects a specific directory structure in the input folder. This structure organizes collection configurations, type definitions, and data files.

## Input Directory Layout

```
input_folder
├── collections/            # collection configurations *.yaml
│   ├── user.yaml
│   ├── org.yaml
│   └── ...
├── dictionary/             # Simple schema *.yaml
│   ├── types/              # Custom types *.yaml
│   │   ├── word.yaml
│   │   ├── sentence.yaml
│   │   └── ...
│   ├── user.1.0.0.yaml        
│   ├── user.1.0.1.yaml        
│   ├── org.1.0.0.yaml        
│   └── ...
└── data/                   # Test Data *.json
    ├── enumerators.json      ## enumerators 
    ├── users.1.0.0.1.json        
    ├── org.1.0.0.1.json        
    └── ...
```

## Directory Contents

### collections/
Contains the main [collection configuration](./collection_config.md) files. Each file defines:
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
Schema definitions and test data for specific versions:
- Named as `{collection}.{version}.yaml`
- Contains the schema or data for that version
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
- Data files: `{collection}.json` or `{collection}.{version}.json` 

## Related Documentation
- [Simple Schema Language](./schema.md)
- [Collection Configuration](./collection_config.md)
- [Custom Types](./types.md)
- [Enumerators](./enumerators.md) 