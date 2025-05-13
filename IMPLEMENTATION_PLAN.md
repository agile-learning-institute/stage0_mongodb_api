# stage0_mongodb_api Implementation Plan
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
- [x] Refactor server.py to remove the use of the echo framework. This is a simple API not a discord bot
- [x] Refactor server.py to match openapi.yaml
- [x] Rename/refactor routes to match server.py
- [x] Remove un-needed routes
- [x] Remove un-needed services
- [x] Create a collection_service to read data and back routes.
    - [x] Load input folder into ``self.configs`` on __init__  See stage0_runbook_merge/src/main.py load_specifications() - we may migrate the code you write based on that to py_utils in the future.
    - [x] Load a ``self.collections`` list with names from the ``self.configs`` list, and query the only document from MongoDB config.VERSION_COLLECTION_NAME to populate version names in ``self.collections``. 
    - [x] Update services to return values from get endpoints from these properties.
    - [x] Review mongoSchemaManager/src/CollectionProcessor.ts, and refactor collection_service.process if necessary
    - [x] Propose a way to move code from mongoSchemaManager/src/models to support collection_service.process
    - [x] Update stage0_py_utils/mongo_utils if necessary to support process logic

## Phase 4: Unit Testing from managers up
- [ ] Test version_manager
- [ ] Test index_manager
- [ ] Test schema_manager
- [ ] Test collection_service
- [ ] Test collection_routes
- [ ] Test server.py
- [ ] Update py_utils/mongoIO and unit tests

## Phase 5: Finish up API
- [ ] Add batch processing support to server.py
- [ ] Build and Test Container
- [ ] Configure github package for container image
- [ ] Configure and Test CI

## Phase 6: Template Repo
- [ ] Create a github template repo for downstream users of the API.
- [ ] Template has no code, uses a makefile for automation, and a Dockerfile that is *from* stage0_mongodb_api and copies the repo's configurations into the container accordingly. 
- [ ] Update api README.md as needed with instructions on how to use the template repo.

## Phase 7: SPA Development
- [ ] Create Vue.js 3 SPA with TypeScript and Vuetify 3
- [ ] Implement key features for extraction to stage0-vue-utils:
   - Configuration browser 
   - Schema viewer 
   - Execution selector
   - Progress tracking with toast notifications
   - Error handling and reporting
- [ ] Build and Test container

