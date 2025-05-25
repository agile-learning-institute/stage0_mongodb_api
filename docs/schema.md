# Schema Language

The stage0_mongodb_api service uses the stage0 Simple Schema language for defining MongoDB collections. This is a simplified version of JSON Schema with additional features for MongoDB-specific needs.

## Basic Properties

The schema language supports the following properties:
```yaml
title: Required on top-level objects
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
`type: enum` and `type: enum_array` represent single or multiple values from a list of valid values. The values are defined in the `data/enumerators.yaml` file and referenced by name in the schema.

Example:
```yaml
status:
  type: enum
  description: The current status of the item
  enums: defaultStatus  # References the defaultStatus enumerator from data/enumerators.yaml
```

The enumerator definition in `data/enumerators.json`:
```json
{
  "defaultStatus": {
    "Draft": "Not finalized",
    "Active": "Not deleted",
    "Archived": "Soft delete indicator"
  }
}
```

This approach:
1. Centralizes enumerator definitions for reuse across schemas
2. Makes enumerators available to API/SPA code through the database
3. Ensures consistency in enumerator values and descriptions
4. Supports versioning of enumerator definitions

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

### Type Resolution

When a primitive type is used in a schema:

1. If the type has a common schema:
   - Use the schema for both JSON and BSON
   - Replace `type` with `bsonType` for BSON schema

2. If the type has format-specific schemas:
   - Use the appropriate schema for each format
   - No property name replacement needed

## Schema Validation

All schemas are validated against the following rules:

1. **Property Requirements**
   - Every property must have a `description`
   - Every property must have a `type`
   - `required` is optional, defaults to false
   - Types must be from the valid list:
     - `array`: Array type definition
     - `object`: Object type definition
     - `enum`: Single value from an enumerator
     - `enum_array`: Multiple values from an enumerator
     - `one_of`: Polymorphic list with type indicator
     - Custom types: Any type defined in the dictionary/types folder

2. **Type-Specific Requirements**
   - `object` type:
     - Must have a `properties` object
     - `additionalProperties` is optional, defaults to false
   - `array` type must have an `items` definition
   - `enum` and `enum_array` types must have an `enums` reference
   - `one_of` type must have `type_property` and `schemas` definitions

3. **Custom Type Validation**
   - Custom types must be defined in the dictionary/types folder
   - Custom types can be complex types with objects and lists
   - Each custom type must resolve to a primitive type with both json and bson schemas
   - Primitive types must have valid JSON Schema and BSON Schema definitions

4. **Recursive Validation**
   - Object properties are recursively validated
   - Array item definitions are recursively validated
   - Custom types are recursively resolved to primitive types

5. **Enumerator Validation**
   - All referenced enumerators must exist in data/enumerators.json
   - Enumerator values must be valid for the referenced type

## Error Handling

Schema validation collects all errors rather than failing on the first error. This allows users to fix all issues at once. The validation process:

1. Validates the schema structure
2. Validates all properties recursively
3. Resolves and validates custom types
4. Validates enumerator references
5. Returns a list of all validation errors found

Example validation errors:
```yaml
errors:
  - "Property 'name' missing description"
  - "Property 'status' has invalid type 'unknown_type'"
  - "Property 'tags' of type 'array' missing items definition"
  - "Unknown enumerator 'invalidStatus' referenced by property 'status'"
  - "Custom type 'word' missing required field 'json_type'"
```

## Related Documentation
- [Custom Types](types.md)
- [Collection Configuration](collection_config.md)
- [Enumerators](enumerators.md) 