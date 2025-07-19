# one_of Feature
We need to finalize the one_of formats and features. 

We will be working with the passing_complex_refs test case.
The current @tests/integration/test_processing_and_rendering.py has testing of the complex refs commented out, we need to uncomment that and get it passing.

## Phase1 - Finalize test data in workshops.1.0.0.0.json
- step1 review /dictionaries and /types
- step2 review workshops.1.0.0.0.json - specifically the first record with an id of 000000000000000000000000
- step3 improve testing data for observations based on dictionary definitions
At this point I will review and approve the test data, and then

Phase2 - Finalize dictionary workshops.1.0.0.yaml 
- step1 review /services/dictionary_services.py and the Property class - and OneOf class
- step2 review input dictionary workshops.1.0.0.yaml
- step3 suggest any changes to the one_of implementation
  - that simplify code or data structures
  - that more closely align with json / bson schema standards for one_of
  - that requires minimal or no code changes

Phase3 - Implement changes if approved. 

Phase4 - Make complex_refs pass
- step1 update dictionaries based on changes from Phase2 if necessary
- step2 update validated output with expected values
- step3 test, diagnose failure and continue fixing problems till tests pass.