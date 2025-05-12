# MongoDB Schema Management Reference

This document outlines the schema management functionality provided by the stage0_mongodb_api service.

## Schema Language

The service uses the stage0 Simple Schema language for defining MongoDB collections. The schema language is a simplified version of JSON Schema with the following properties:

```yaml
title: Required on top-level objects specified in the data catalog
description: Required for ALL properties
type: [array, object, enum, enum_array, one_of, **custom_type**]
items: for array types
properties: for object types
required: for object types
additional_properties: for object types
enums: for enum or enum_array types
one_of: for polymorphic list properties with type indicator
```

## Schema Types

### Basic Types
- `array`: An array of items
- `object`: A JSON object with properties
- `enum`: A single value from a predefined list
- `enum_array`: An array of values from a predefined list
- `one_of`: A polymorphic property that can be one of several types

### Custom Types
The service provides several custom types for common use cases:
- `word`: A string of up to 32 characters, no special characters or whitespace
- `sentence`: A string of up to 255 printable characters, whitespace allowed
- `paragraph`: An array of sentences
- `count`: A non-negative integer
- `currency`: A USD Currency Value
- `identity`: A system-generated Unique Identifier

## Schema Management Features

### Index Management
- Create and manage indexes for collections
- Support for single and compound indexes
- Index validation and optimization

### Schema Validation
- Enforce data structure and type constraints
- Validate required fields
- Support for custom validation rules

### Migration Support
- Version control for schema changes
- Automatic migration execution
- Rollback capabilities

## Configuration

The service is configured through environment variables:
- `MONGO_DB_NAME`: The name of the MongoDB database
- `MONGO_CONNECTION_STRING`: MongoDB connection string
- `INPUT_FOLDER`: Directory containing schema configurations
- `AUTO_PROCESS`: Set to "true" to process configurations on startup
- `EXIT_AFTER_PROCESSING`: Set to "false" to expose the API after processing

## API Endpoints

The service provides RESTful endpoints for:
- Schema management
- Index management
- Migration execution
- Configuration validation

See the OpenAPI documentation for detailed endpoint specifications. 