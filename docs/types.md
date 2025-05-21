# Custom Types

The stage0_mongodb_api service provides a rich set of custom types for defining MongoDB schemas. These types are defined in the `dictionary/types` folder and provide validation rules for both JSON and BSON schemas.

## Type System

Custom types follow a hierarchical structure:
1. **Custom Types**: User-defined types that can reference other custom types
2. **Primitive Types**: Base types that define core validation rules
3. **Schema Formats**: JSON and BSON schema representations

## Primitive Types

Primitive types define the core validation rules for a data type. They include:
- The base type (string, number, etc.)
- Validation patterns (regex, ranges, etc.)
- Length constraints
- Format specifications

### Example: Word Type
```yaml
# dictionary/types/word.yaml
title: Word
description: A String of text, at least 4 and no more than 40 characters with no spaces, or special characters. Suitable for username, short name, or slug type data.
json_type: 
  type: string
  pattern: "^[a-zA-Z0-9_-]{4,40}$"
  minLength: 4
  maxLength: 40
bson_type: 
  type: string
  pattern: "^[a-zA-Z0-9_-]{4,40}$"
  minLength: 4
  maxLength: 40
```

## Available Types

### Basic Types
- `word`: A string of up to 32 characters, no special characters or whitespace
  - Pattern: `^[a-zA-Z0-9_-]{4,40}$`
  - Length: 4-40 characters
  - Use: usernames, short names, slugs

- `sentence`: A string of up to 255 printable characters, whitespace allowed
  - Pattern: `^[\x20-\x7E]{1,255}$`
  - Length: 1-255 characters
  - Use: titles, short descriptions

- `paragraph`: An array of sentences
  - Type: array of sentence
  - Use: longer text content

### Numeric Types
- `count`: A non-negative integer
  - Type: integer
  - Range: 0 to MAX_INT
  - Use: quantities, counts, sizes

- `quantity`: A positive, non-zero integer
  - Type: integer
  - Range: 1 to MAX_INT
  - Use: required quantities, sizes

- `currency`: A USD Currency Value
  - Type: decimal
  - Pattern: `^\d+(\.\d{2})?$`
  - Use: monetary values

### System Types
- `identity`: A system-generated Unique Identifier
  - Type: string
  - Pattern: UUID v4
  - Use: primary keys, references

- `breadcrumb`: A system-generated tracking record
  - Type: object
  - Properties:
    - `at_time`: date_time
    - `by_user`: word
    - `from_ip`: ip_address
    - `correlation`: word
  - Use: audit trails, tracking

## Type Resolution

When a custom type is used in a schema, the system:
1. Looks up the type definition in the dictionary/types folder
2. If the type references another custom type, recursively resolves it
3. Continues until reaching a primitive type
4. Uses the primitive's validation rules to generate the appropriate schema

### Example: Complex Type
```yaml
# dictionary/types/breadcrumb.yaml
title: Breadcrumb
description: A tracking breadcrumb
type: object
properties:
    at_time:
        description: The date/time the breadcrumb is created
        type: date_time
    by_user:
        description: The user who created the breadcrumb
        type: word
    from_ip:
        description: The users IP Address
        type: ip_address
    correlation:
        description: A correlation ID used to tie this breadcrumb to related transactions
        type: word
```

## Creating Custom Types

To create a new custom type:

1. Create a new YAML file in the `dictionary/types` folder
2. Define the type using the Simple Schema format
3. Include both `json_type` and `bson_type` for primitive types
4. Use existing types as building blocks for complex types

### Type Definition Template
```yaml
title: TypeName
description: Description of the type and its use
type: object  # or array, enum, etc.
properties:   # for object types
    property_name:
        type: existing_type
        description: Property description
json_type:    # for primitive types
    type: string
    pattern: regex_pattern
    minLength: min_length
    maxLength: max_length
bson_type:    # for primitive types
    type: string
    pattern: regex_pattern
    minLength: min_length
    maxLength: max_length
```

## Related Documentation
- [Schema Language](schema.md)
- [Collection Configuration](collection_config.md)
- [Enumerators](enumerators.md) 