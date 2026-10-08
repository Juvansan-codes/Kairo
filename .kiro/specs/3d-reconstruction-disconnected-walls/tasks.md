# Implementation Plan

- [-] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Consistent Tolerance Enables Room Detection
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the tolerance mismatch prevents room detection
  - **Scoped PBT Approach**: Scope the property to concrete floor plan cases with known closed room regions (e.g., rectangular rooms, L-shaped layouts) where default tolerances cause failure
  - Test implementation: For floor plans with walls forming closed regions, run unfixed pipeline with default parameters (`node_tolerance_px=25.0`, `endpoint_tolerance_px=15.0`)
  - Assert that `result.rooms` is empty (length == 0) on unfixed code - this confirms the bug
  - Assert that 3D output has disconnected wall segments (no floor meshes)
  - Document specific test cases: simple rectangular rooms (2-3 rooms), complex floor plans (5+ rooms), open plan layouts
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists and tolerance mismatch causes zero room detection)
  - Document counterexamples found: specific floor plan files that produce 0 rooms with mismatched tolerance but should produce N > 0 rooms
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [~] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Correct Results Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for floor plans that already work correctly or have consistent tolerance configurations
  - Identify test cases: floor plans currently producing correct room detection, custom tolerance configurations already working, edge case layouts (L-shapes, T-junctions) already functional
  - Write property-based test: For all floor plans where `isBugCondition` returns false (tolerances already consistent OR pipeline already working), verify room count, wall topology, and 3D geometry are identical between original and fixed pipeline
  - Property-based testing generates many test cases for stronger preservation guarantees
  - Test should compare: `result_original.rooms == result_fixed.rooms`, wall segment topology unchanged, 3D scene structure identical
  - Run tests on UNFIXED code to capture baseline behavior
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 3. Fix for tolerance mismatch causing disconnected walls

  - [~] 3.1 Align default tolerance values in pipeline.py
    - Change `node_tolerance_px` default parameter from 25.0 to 15.0 to match `endpoint_tolerance_px`
    - File: `backend/app/geometry/pipeline.py`, Line 67
    - Change: `node_tolerance_px: float = 25.0` → `node_tolerance_px: float = 15.0`
    - Verify the corrected tolerance is passed to `polygonize_rooms()` at Lines 238-241
    - Ensure no hardcoded tolerance values override the parameter elsewhere in the function
    - _Bug_Condition: isBugCondition(input) where input.node_tolerance_px != input.endpoint_tolerance_px AND input.walls_exist AND input.walls_can_form_closed_regions_
    - _Expected_Behavior: For floor plans with closed wall regions and previously mismatched tolerances, pipeline SHALL use consistent tolerance values (both 15.0 px), enabling successful room detection (rooms.length > 0) and connected 3D wall structures with floor meshes_
    - _Preservation: Floor plans with already-consistent tolerances or already-correct results SHALL produce identical room detection, wall topology, and 3D geometry as original pipeline_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [~] 3.2 Add documentation about tolerance consistency requirement
    - Add inline comment near parameter definitions (around Line 67) explaining that `node_tolerance_px` and `endpoint_tolerance_px` must be consistent to prevent graph topology corruption
    - Document the relationship: "node_tolerance_px controls vertex merging during room polygonization and must match endpoint_tolerance_px from intersection splitting to maintain consistent graph topology"
    - Consider adding docstring note in `run_mgr_pipeline()` function documentation
    - _Requirements: 2.5_

  - [~] 3.3 Add validation check to prevent future mismatches
    - Add early validation in `run_mgr_pipeline()` to detect tolerance mismatches
    - Implement assertion or warning: `if node_tolerance_px != endpoint_tolerance_px: warn("Tolerance mismatch detected...")`
    - Place validation near beginning of function (after parameter processing)
    - Consider using Python's `warnings` module for non-fatal warning
    - This prevents future regressions from configuration changes
    - _Requirements: 2.5_

  - [~] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Consistent Tolerance Enables Room Detection
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (rooms.length > 0 for floor plans with closed regions)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed - floor plans with closed regions now detect rooms correctly with consistent tolerance)
    - Verify specific outcomes: `result.rooms.length > 0`, walls form closed regions, 3D scene has floor meshes and connected wall structures
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [~] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Existing Correct Results Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions - floor plans already working correctly produce identical results)
    - Verify: same room count, same wall topology, same 3D geometry for all non-buggy inputs
    - Confirm all tests still pass after fix (no regressions)

- [~] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest backend/app/geometry/test_*.py -v`
  - Verify bug condition test passes (room detection succeeds with consistent tolerance)
  - Verify preservation tests pass (existing correct behavior unchanged)
  - Verify all existing geometry tests pass (no regressions in other pipeline phases)
  - Test with sample floor plans from `backend/data/evaluation/` if available
  - Optionally: Verify GLB 3D output visually - walls should be connected with floor meshes
  - If any tests fail, investigate and resolve before marking complete
  - Ask the user if questions arise or if further validation is needed
