# Integration Testing Refactor Plan

## Context & Goals
- The integration tests in `tests/integration` and some in `tests/services`, `tests/uitls`, and `tests/routes` rely on data from `tests/test_cases`.
- The test case data has been renamed and updated; integration tests must be refactored to use the new structure and data.
- The goal is to:
  - Ensure all integration tests use the updated test case data.
  - Move or rewrite tests so that only true integration tests use real data; all others should mock data or be unit tests.
  - Start with failing conditions (bad_refs, missing, unparsable), then move to processing and rendering tests, working through one test case at a time.
  - Each step should be reviewed and committed before proceeding.

## High-Level Steps
1. **Audit and Categorize Existing Tests** ✅ **COMPLETED**
   - Identify which tests are true integration tests (using real data from `test_cases`) and which should be unit tests (mocking data).
   - **Explicitly categorize tests that should be moved largely unchanged** (e.g., MongoIO, Config File, FileIO, etc.) if they are already integration-style tests using real data. These should be moved to the integration folder before refactoring the failing_ test cases.
   - Move or refactor tests as needed.
2. **Refactor Failing Condition Integration Tests** ✅ **COMPLETED**
   - Update and validate tests for:
     - `failing_refs` (bad references)
     - `failing_empty` (missing data)
     - `failing_not_parsable` (unparsable files)
   - Ensure these tests use the new data and assert correct exception handling and reporting.
3. **Refactor Processing and Rendering Integration Tests**
   - Start with `passing_template` and work through one test case at a time.
   - Update tests to use new data and verify output against `verified_output`.
   - **Note:** `test_configuration_service_integration.py` should be largely replaced by `test_processing.py` as they serve similar purposes.
   - Only move to the next test case after the previous one passes and is reviewed/committed.
4. **Refactor/Migrate Other Integration Tests**
   - ✅ **Main integration test moves completed in Step 1**
   - **Remove/refactor unit tests that are still failing because of data dependency:**
     - Identify any unit tests in `tests/services`, `tests/uitls`, `tests/routes` that are failing due to data dependency
     - Refactor these tests to use proper mocking instead of real data
     - Ensure all unit tests are truly unit tests (no external dependencies)
   - **Ensure all integration tests are in one place and use the correct data**
5. **Cleanup and Final Review**
   - Remove or rewrite any remaining tests that do not fit the new structure.
   - Ensure all tests pass and the integration suite is robust and maintainable.

---

## Step 1: Audit and Categorize Existing Tests ✅ **COMPLETED**
- ✅ Reviewed all tests in `tests/integration`, `tests/services`, `tests/uitls`, and `tests/routes`.
- ✅ Categorized each as:
  - Integration test (uses real data from `test_cases`)
  - Unit test (should mock data)
  - **Integration-style tests that should be moved largely unchanged** (e.g., MongoIO, Config File, FileIO, etc.)
- ✅ **Moved integration-style tests that use real data to the integration folder:**
  - `tests/uitls/test_mongo_io.py` → `tests/integration/test_mongo_io.py` (MongoDB integration tests)
  - `tests/uitls/test_config_file.py` → `tests/integration/test_config_file.py` (Config file loading tests)
  - `tests/services/test_configuration_service_integration.py` → `tests/integration/test_configuration_service_integration.py` (Configuration processing integration tests)

**Commit message suggestion:**
```
chore(test): move integration tests to integration folder

- Move test_mongo_io.py from uitls to integration (MongoDB integration tests)
- Move test_config_file.py from uitls to integration (Config file loading tests)  
- Move test_configuration_service_integration.py from services to integration (Configuration processing integration tests)
- Delete original files from old locations
```

---

## Step 2: Refactor Failing Condition Integration Tests ✅ **COMPLETED**
- ✅ **Updated and validated the following tests:**
  - `test_bad_refs.py` (uses `failing_refs`) - Tests circular references, missing references, and missing types
  - `test_missing.py` (uses `failing_empty`) - Tests empty/missing folders for all data types
  - `test_unparsable.py` (uses `failing_not_parsable`) - Tests unparsable files and unsupported file types
- ✅ **Ensured each test:**
  - Sets `INPUT_FOLDER` to the correct test case directory
  - Asserts correct exception handling and reporting (using `ConfiguratorException` and `ConfiguratorEvent`)
  - Uses the new test case data structure
  - Has proper cleanup in tearDown methods

**Commit message suggestion:**
```
refactor(test): update failing condition integration tests to use new test_cases data and assert correct error handling

- Refactor test_bad_refs.py to test circular references, missing references, and missing types
- Refactor test_missing.py to test empty/missing folders for all data types  
- Refactor test_unparsable.py to test unparsable files and unsupported file types
- Add proper exception handling assertions and cleanup
```

---

## Step 3: Refactor Processing and Rendering Integration Tests
- Start with `passing_template` and work through one test case at a time.
- Update tests to use new data and verify output against `verified_output`.
- **Note:** `test_configuration_service_integration.py` should be largely replaced by `test_processing.py` as they serve similar purposes.
- Only move to the next test case after the previous one passes and is reviewed/committed.

**Commit message suggestion:**
```
refactor(test): update processing and rendering integration tests to use new test_cases data, starting with passing_template
```

---

## Step 4: Refactor/Migrate Other Integration Tests
- ✅ **Main integration test moves completed in Step 1**
- **Remove/refactor unit tests that are still failing because of data dependency:**
  - Identify any unit tests in `tests/services`, `tests/uitls`, `tests/routes` that are failing due to data dependency
  - Refactor these tests to use proper mocking instead of real data
  - Ensure all unit tests are truly unit tests (no external dependencies)
- **Ensure all integration tests are in one place and use the correct data**

**Commit message suggestion:**
```
refactor(test): remove data dependencies from unit tests and ensure proper mocking
```

---

## Next Steps
- After review and commit of Step 2, proceed to Step 3: Refactor Processing and Rendering Integration Tests, starting with `passing_template`. 