# Schema Language

The stage0_mongodb_api service uses the stage0 Simple Schema language for defining MongoDB collections. This is a simplified version of JSON Schema with additional features for MongoDB-specific needs.

## Basic Properties

The schema language supports the following properties:
```yaml
title: Optional, but recommended for top-level dictionaries
description: Required for ALL properties
type: [array, object, enum, enum_array, one_of, **custom_type**]
required: Optional boolean, defaults to false
items: Required for array types
properties: Required for object types
additionalProperties: Optional boolean for object types, defaults to false
enums: Required for enum or enum_array types
one_of: Required for polymorphic list properties
$ref: Optional reference to another dictionary schema
```

## Version Numbers

### Schema Files
Schema files use a three-part version number: `major.minor.patch`
- `major`: Significant changes
- `minor`: New features
- `patch`: Bug fixes

Example: `user.1.0.0.yaml` indicates:
- Major version 1
- Minor version 0
- Patch version 0

### Collection Configuration
Collection configurations use a four-part version number: `major.minor.patch.enumerator`
- `major`: Significant changes
- `minor`: New features
- `patch`: Bug fixes
- `enumerator`: Version of enumerators to use

Example: `1.0.0.2` in collection config indicates:
- Major version 1
- Minor version 0
- Patch version 0
- Enumerator version 2

## JSON Schema Compatibility

The following properties are identical to their JSON Schema equivalents:
- `title`: Required on top-level objects
- `description`: Required for all properties
- `type: object`: Object type definition
- `type: array`: Array type definition
- `items`: Array item definition
- `properties`: Object property definitions
- `additional_properties`: Additional properties configuration

## Special Types

### Required / Additional Properties
Unlike JSON Schema where `required` is a required property list, in Simple Schema required is a boolean attribute of a property, that defaults to false. 

`additional_properties`, as in JSON schema is an attribute of an object, but unlike in JSON Schema it defaults to false.

### Enumerator Types
`type: enum` and `type: enum_array` represent single or multiple values from a list of valid values. The values are defined in the `data/enumerators.json` file and referenced by name in the schema.

The enumerators.json file must follow the schema defined in `docs/schemas/enumerators_schema.yaml`. Each enumerator version must have:
- A unique version number
- A valid status ("Active" or "Deprecated")
- A map of enumerator definitions where each value has a description

Example:
```yaml
status:
  description: The current status of the item
  type: enum
  enums: defaultStatus  # References the defaultStatus enumerator from data/enumerators.json
```

The enumerator definition in `data/enumerators.json`:
```json
[
    {
        "name": "Enumerations",
        "status": "Active",
        "version": 1,
        "enumerators": {
            "defaultStatus": {
                "Draft": "Not finalized",
                "Active": "Not deleted",
                "Archived": "Soft delete indicator"
            }
        }
    }
]
```

When a schema references an enumerator, the version of the enumerator to use is determined by the collection configuration. For example:
- Collection config version `1.0.0.1` will use enumerator version 1
- Collection config version `1.0.0.2` will use enumerator version 2

This approach:
1. Centralizes enumerator definitions for reuse across schemas
2. Makes enumerators available to API/SPA code through the database
3. Ensures consistency in enumerator values and descriptions
4. Supports versioning of enumerator definitions
5. Allows collections to specify which version of enumerators to use
6. Validates enumerator definitions against a schema

### Schema References
The `$ref` property allows referencing schema files. This provides an alternative to complex custom types, and should be used when the complex type is likely to need version control. 

Example:
```yaml
# customer.1.0.0.yaml
title: Customer
description: Customer Information
type: object
properties:
  name:
    description: The customer name
    type: sentence
  home_address:
    $ref: street_address.1.0.0.yaml
  mailing_address:
    $ref: street_address.1.0.0.yaml
```

When resolving references:
1. The referenced schema must exist in the dictionary directory
2. The referenced schema must be valid
3. Circular references are not allowed
4. References are resolved before validation

### OneOf Type
The `one_of` type describes a polymorphic list with a type indicator. Useful for storing objects with different structures based on their type. The `one_of` property specifies:
- `type_property`: The name of the property that determines the object's type
- `schemas`: A map of type values to their corresponding schemas



Example:
```yaml
# customer.yaml
type: object
description: An index card for a media item
properties:
  card_type:
    description: The type of media this card represents
    type: enum
    enums: mediaType
  title:
    description: The card title
    type: Sentence
one_of:
  type_property: card_type
  schemas:
    book: 
      $ref: book.yaml
    movie: 
      $ref: movie.yaml
    audio: 
      $ref: audio.yaml
```

```yaml
# book.yaml
description: A book
type: object
properties:
  author:
    description: Author Name
    type: sentence
  isbn: 
    description: ISBN Number
    type: word
  page_count: 
    description: Page count
    type: count
```

```yaml
# movie.yaml
description: A Movie
type: object
properties:
  director:
    description: Directors name
    type: sentence
  duration:
    description: Duration in minutes
    type: count
  format:
    description: Page count
    type: enum
    enums: formats
```

```yaml
# audio.yaml
description: An audio recording 
type: object
properties:
  speaker:
    description: Speaker Name
    type: sentence
  duration: 
    description: Duration in minutes
    type: count
```

This would validate documents like:
```json
{
  "cards": [
    {
      "card_type": "book",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "isbn": "9780743273565",
      "page_count": 180
    },
    {
      "card_type": "video",
      "title": "The Godfather",
      "director": "Francis Ford Coppola",
      "duration": 175,
      "format": "bluray"
    }
  ]
}
```

## Custom Types

Custom types are defined in the dictionary/types folder. Custom types can be complex types that reference other custom types. All custom types must resolve to a primitive type that defines both json and bson versions.

Unlike enumerators, custom types are considered immutable and are not versioned. Once defined, they should not be changed as they may be used across multiple schemas.

### Type Resolution

Custom types are resolved recursively until a primitive type is found. For example:

```yaml
# types/breadcrumb.yaml
title: Breadcrumb
description: A tracking breadcrumb
type: object
properties:
  from_ip:
    description: Http Request remote IP address
    type: word
  by_user:
    description: ID Of User
    type: word
  at_time:
    description: The date-time when last updated
    type: date-time
  correlation_id:
    description: The logging correlation ID of the update transaction
    type: word
```

In this example:
1. `breadcrumb` is a complex type that uses `word` and `date-time` types
2. `word` and `date-time` are primitive types that resolve to JSON/BSON schemas
3. The resolution process continues until all types are resolved to primitive types

### Primitive Types

Primitive types are the fundamental building blocks of the schema system. They can be defined in two ways:

1. **Common Schema**: When the only difference between JSON and BSON is the type property name
2. **Format-Specific Schema**: When the formats require different validation rules

#### Common Schema Format
```yaml
# types/word.yaml
title: Word
description: A string of text, at least 4 and no more than 40 characters
schema:
  type: string
  minLength: 4
  maxLength: 40
  pattern: "^[a-zA-Z0-9_-]{4,40}$"
```

#### Format-Specific Schema
```yaml
# types/timestamp.yaml
title: Timestamp
description: ISO 8601 timestamp
json_schema:
  type: string
  format: date-time
bson_schema:
  bsonType: date
```