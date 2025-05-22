# Schema Language

The stage0_mongodb_api service uses the stage0 Simple Schema language for defining MongoDB collections. This is a simplified version of JSON Schema with additional features for MongoDB-specific needs.

## Basic Properties

The schema language supports the following properties:
```yaml
title: Required on top-level objects specified in the data catalog
description: Required for ALL properties
type: [array, object, enum, enum_array, one_of, **custom_type**]
items: for array types
properties: for object types
required: for object types
additional_properties: for object types
enums: for enum or enum_array types - references an enumerator from data/enumerators.yaml
one_of: for polymorphic list properties with type indicator
```

## JSON Schema Compatibility

The following properties are identical to their JSON Schema equivalents:
- `title`: Required on top-level objects
- `description`: Required for all properties
- `type: object`: Object type definition
- `type: array`: Array type definition
- `items`: Array item definition
- `properties`: Object property definitions
- `required`: Required property list
- `additional_properties`: Additional properties configuration

## Special Types

### Enumerator Types
`type: enum` and `type: enum_array` represent single or multiple values from a list of valid values. The values are defined in the `data/enumerators.yaml` file and referenced by name in the schema.

Example:
```yaml
status:
  type: enum
  description: The current status of the item
  enums: defaultStatus  # References the defaultStatus enumerator from data/enumerators.yaml
```

The enumerator definition in `data/enumerators.yaml`:
```yaml
defaultStatus:
  Draft: "Not finalized"
  Active: "Not deleted"
  Archived: "Soft delete indicator"
```

This approach:
1. Centralizes enumerator definitions for reuse across schemas
2. Makes enumerators available to API/SPA code through the database
3. Ensures consistency in enumerator values and descriptions
4. Supports versioning of enumerator definitions

### OneOf Type
The `one_of` type describes a polymorphic list with a type indicator. Useful for storing objects with different structures based on their type.

Example:
```yaml
cards:
  type: array
  description: List of index cards for different media types
  items:
    type: object
    description: An index card for a media item
    properties:
      type:
        type: enum
        description: The type of media this card represents
        enums: mediaType
      title:
        type: sentence
        description: The title of the media
      description:
        type: paragraph
        description: A detailed description of the media
    one_of:
      type_property: type
      schemas:
        book:
          type: object
          description: Properties specific to book media
          properties:
            author:
              type: sentence
              description: The author of the book
            isbn:
              type: word
              description: The ISBN number of the book
            page_count:
              type: count
              description: Number of pages in the book
        video:
          type: object
          description: Properties specific to video media
          properties:
            director:
              type: sentence
              description: The director of the video
            duration:
              type: count
              description: Length of the video in minutes
            format:
              type: enum
              description: The video format
              enums: videoFormat
```

The enumerator definitions in `data/enumerators.yaml`:
```yaml
mediaType:
  book: "A printed or digital book"
  video: "A video recording"
  article: "A written article"

videoFormat:
  dvd: "Digital Versatile Disc"
  bluray: "Blu-ray Disc"
  digital: "Digital streaming format"
```

This would validate documents like:
```json
{
  "cards": [
    {
      "type": "book",
      "title": "The Great Gatsby",
      "description": "A novel by F. Scott Fitzgerald",
      "author": "F. Scott Fitzgerald",
      "isbn": "9780743273565",
      "page_count": 180
    },
    {
      "type": "video",
      "title": "The Godfather",
      "description": "A crime drama film",
      "director": "Francis Ford Coppola",
      "duration": 175,
      "format": "bluray"
    }
  ]
}
```

The `one_of` property specifies:
- `type_property`: The name of the property that determines the object's type
- `schemas`: A map of type values to their corresponding schemas

## Custom Types

Custom types are defined in the dictionary/types folder and eventually resolve to primitive types. Primitive types define the core validation rules needed for different schema formats (JSON Schema, BSON Schema, etc.).

### Primitive Type Example
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

### Type Resolution
When a custom type is used in a schema, the system:
1. Looks up the type definition in the dictionary/types folder
2. If the type references another custom type, recursively resolves it
3. Continues until reaching a primitive type
4. Uses the primitive's validation rules to generate the appropriate schema

### Available Custom Types
- `word`: A string of up to 32 characters, no special characters or whitespace
- `sentence`: A string of up to 255 printable characters, whitespace allowed
- `paragraph`: An array of sentences
- `count`: A non-negative integer
- `quantity`: A positive, non-zero integer
- `currency`: A USD Currency Value
- `identity`: A system-generated Unique Identifier
- `breadcrumb`: A system-generated Unique Identifier

## Related Documentation
- [Custom Types](types.md)
- [Collection Configuration](collection_config.md)
- [Enumerators](enumerators.md) 