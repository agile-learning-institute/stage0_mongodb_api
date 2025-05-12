# stage0_mongodb_api

This API implements index, schema, and migration management services for a MongoDB database. Schemas are described using the stage0 Simple Schema standard. 

## Prerequisites

- [Stage0 Developer Edition]() #TODO for now Docker
- [Python](https://www.python.org/downloads/)
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)

### Optional

- [Mongo Compass](https://www.mongodb.com/try/download/compass) - if you want a way to look into the database

## Usage
Instructions for creating a project Mongo DB API service using your own simple schema documentation. Should include a template repo with a Dockerfile and directory structure.

## Configurability
API Configuration Values
- MONGO_DB_NAME
- MONGO_CONNECTION_STRING
- INPUT_FOLDER that contains configurations etc.
- AUTO_PROCESS ``true`` will process configurations on startup
- EXIT_AFTER_PROCESSING ``false`` to expose API

## Install Dependencies

```bash
pipenv install
```

## Run Unit Testing

```bash
pipenv run test
```

## Run the API locally (assumes database is already running)

```bash
pipenv run local
```

## Build and run the server Container
This will build the new container, and {re}start the mongodb and API container together.
```bash
pipenv run container
```

## Run StepCI end-2-end testing
NOTE: Assumes the API is running at localhost:8580
```bash
pipenv run stepci
```

# API Testing with CURL

There are quite a few endpoints, see [CURL_EXAMPLES](./CURL_EXAMPLES.md) for all of them.

The [Dockerfile](./Dockerfile) uses a 2-stage build, and supports both amd64 and arm64 architectures. 