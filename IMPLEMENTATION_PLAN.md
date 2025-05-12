# Implementation Plan

## Phase 1: Repository Setup
We will be creating the content for the stage0_mongodb_api project currently open in the cursor workspace. 
We will be using code and documentation from the mongoSchemaManager, stage0_fran, and stage0 repo's to inform our work, all of these directories are in the workspace for reference. 
- [x] Review stage0/developer_edition/docs/api_standards.md for context.
- [x] Copy stage0_fran Project here as a template. 
- [x] Rename the directory ``stage0_fran`` to ``src``
- [x] Remove the ``agents`` folder as we won't need it.

## Phase 2: Update Documentation
- [x] Update the README.md to incorporate NEW_README.md 
- [x] Review stage0/bots/SIMPLE_SCHEMA.md to understand the schema language.
- [x] Review mongoSchemaManager/docs/REFERENCE.md to understand the POC for this project. 
- [x] Refactor docs/REFERENCE.md for SIMPLE_SCHEMA
- [x] Refactor docs/CONTRIBUTING.md as appropriate
- [x] Replace the docs/openapi.yaml with new_openapi.yaml 
- [x] Review and complete the openapi.yaml

## Phase3: Refactor and add code
- [ ] Refactor server.py to remove the use of the echo framework. This is a simple API not a discord bot
- [ ] Refactor server.py to match openapi.yaml
- [ ] Rename/refactor routes to match server.py
- [ ] Remove un-needed routes
- [ ] Remove un-needed services
- [ ] Create a schema_service to read config and back routes
    - [ ] Review mongoSchemaManager/src/CollectionProcessor.ts, and port / refactor into a method in schema_service
- [ ] Add batch processing support to server.py
- [ ] Build and Test Container
- [ ] Configure github package for container image
- [ ] Configure and Test CI

## Phase 4: Template Repo
- [ ] Create a github template repo for downstream users of the API.
- [ ] Template has no code, uses a makefile for automation, and a Dockerfile that is *from* stage0_mongodb_api and copies the repo's configurations into the container accordingly. 
- [ ] Update api README.md as needed with instructions on how to use the template repo.

## Phase 5: SPA Development
- [ ] Create Vue.js 3 SPA with TypeScript and Vuetify 3
- [ ] Implement key features for extraction to stage0-vue-utils:
   - Configuration browser 
   - Schema viewer 
   - Execution selector
   - Progress tracking with toast notifications
   - Error handling and reporting
- [ ] Build and Test container

