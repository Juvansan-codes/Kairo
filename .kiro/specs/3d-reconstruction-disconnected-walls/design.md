# 3D Reconstruction Disconnected Walls Bugfix Design

## Overview

The KAIRO 3D reconstruction pipeline produces disconnected floating wall segments instead of properly connected room structures. The root cause is an inconsistent tolerance parameter: room polygonization is called with 25.0 px tolerance while the wall graph was built with 15.0 px endpoint tolerance during intersection splitting. This mismatch prevents the detection of closed polygons, resulting in zero rooms being identified.

The fix ensures consistent tolerance usage across all geometric graph-building operations in the MGR pipeline. By aligning the `node_tolerance_px` parameter with the `endpoint_tolerance_px` used in earlier phases, walls will properly connect into closed regions, enabling successful room detection and coherent 3D model generation.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when `polygonize_rooms()` is called with a tolerance value inconsistent with the tolerance used to build the wall graph
- **Property (P)**: The desired behavior - room polygonization should detect closed wall regions and the 3D generator should render connected room structures with floors
- **Preservation**: Existing floor plans that already work correctly must continue to produce identical results
- **MGR Pipeline**: Multi-stage Geometric Reconciliation pipeline in `backend/app/geometry/pipeline.py` that processes wall geometry
- **node_tolerance_px**: The tolerance parameter controlling how close two wall endpoints must be to be considered the same connection point
- **endpoint_tolerance_px**: The tolerance used during intersection splitting to snap wall endpoints together
- **polygonize_rooms()**: Function in `room_polygonization.py` that extracts closed polygonal room regions from wall segments
- **build_wall_graph()**: Function that constructs a graph representation of walls with vertices and edges, used internally by `polygonize_rooms()`

## Bug Details

### Bug Condition

The bug manifests when the MGR pipeline processes a floor plan containing walls that should form closed room regions. The `node_tolerance_px` parameter passed to `polygonize_rooms()` (25.0 px) is inconsistent with the `endpoint_tolerance_px` used earlier in `split_wall_intersections()` (15.0 px). This tolerance mismatch causes the wall graph to have incorrect topology, preventing the detection of closed polygonal regions.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type MGRPipelineInput
  OUTPUT: boolean
  
  RETURN input.node_tolerance_px != input.endpoint_tolerance_px
         AND input.walls_exist
         AND input.walls_can_form_closed_regions
         AND polygonize_rooms_called_with_mismatched_tolerance
END FUNCTION
```

### Examples

- **Standard Floor Plan**: A floor plan with 3 rectangular rooms. Wall endpoints are snapped at 15.0 px during intersection splitting. `polygonize_rooms()` is called with 25.0 px tolerance. The excessive tolerance over-merges distinct vertices, breaking graph topology. Result: 0 rooms detected, disconnected wall rendering.

- **Open Plan Layout**: A floor plan with 2 rooms and an open connecting area. Wall endpoints use 15.0 px tolerance. `polygonize_rooms()` uses 25.0 px. The loose tolerance causes nearby but distinct connection points to collapse, destroying the topological structure. Result: 0 rooms, floating wall segments.

- **Complex Floor Plan**: A floor plan with 5 rooms, hallways, and multiple wall intersections. Intersection splitting uses 15.0 px endpoint tolerance to correctly snap connections. Room polygonization uses 25.0 px node tolerance. The 10 px discrepancy causes critical vertices to merge incorrectly. Result: 0 rooms detected, complete 3D reconstruction failure.

- **Edge Case - Minimal Tolerance Difference**: Even a small tolerance mismatch (e.g., 15.0 px vs 16.0 px) could potentially cause issues in floor plans with tightly spaced wall junctions, though larger mismatches (15.0 px vs 25.0 px) are more reliably problematic.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Floor plans that already produce correct room detection with current tolerance values must continue to work identically
- Dimension evidence processing and metric calibration must remain unchanged
- Door and window association logic must continue using existing reconciliation parameters
- Wall mesh generation with opening cutouts must preserve the robust 1D segmentation approach
- Geometric reconciliation phases (snapping, merging, intersection splitting) must maintain their existing tolerance parameters and behavior
- Topology validation when enabled must continue to validate geometric consistency

**Scope:**
All inputs that do NOT involve the tolerance mismatch (floor plans already working correctly, or pipeline configurations where tolerances are already consistent) should be completely unaffected by this fix. This includes:
- Floor plans processed with custom tolerance parameters that are already consistent
- Pipeline phases unrelated to room polygonization (OCR, dimension extraction, scale consensus)
- 3D generation logic for walls, doors, and windows (only the input data quality changes, not the generation logic itself)

## Hypothesized Root Cause

Based on the bug description and requirements analysis, the root cause has been confirmed:

1. **Parameter Mismatch**: The pipeline default configuration has `node_tolerance_px=25.0` but `endpoint_tolerance_px=15.0`
   - These parameters control the same geometric concept (vertex connection distance) but use different values
   - Located in `pipeline.py` lines 67 and 238-241

2. **Sequential Phase Dependency**: Intersection splitting (Phase 7) creates snapped wall endpoints at 15.0 px tolerance, but room polygonization (Phase 9) attempts to build a graph at 25.0 px tolerance
   - The wall graph construction in `build_wall_graph()` uses the passed `node_tolerance_px`
   - The excessive 25.0 px tolerance causes over-merging of distinct vertices that were correctly separated at 15.0 px

3. **Graph Topology Corruption**: The tolerance mismatch breaks the topological structure required for Shapely's `polygonize()` function
   - Closed polygon detection requires consistent vertex positions across graph construction
   - Over-merged vertices destroy the cycle structure needed to identify room boundaries

4. **Cascade Effect**: Zero rooms detected → no floor polygons → disconnected wall rendering
   - The 3D generator relies on room polygon context for spatial coherence
   - Without rooms, walls are positioned as isolated segments rather than connected structures

## Correctness Properties

Property 1: Bug Condition - Consistent Tolerance Enables Room Detection

_For any_ floor plan input where walls can form closed regions and the pipeline previously failed due to tolerance mismatch (isBugCondition returns true), the fixed pipeline SHALL use consistent tolerance values across intersection splitting and room polygonization, enabling successful detection of closed room polygons and generation of connected 3D wall structures with floor meshes.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - Existing Correct Results Unchanged

_For any_ floor plan input where tolerance parameters were already consistent or the pipeline already produced correct results (isBugCondition returns false), the fixed pipeline SHALL produce exactly the same room detection, wall topology, and 3D geometry as the original pipeline, preserving all existing correct behavior.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct (tolerance mismatch between intersection splitting and room polygonization):

**File**: `backend/app/geometry/pipeline.py`

**Function**: `run_mgr_pipeline()`

**Specific Changes**:

1. **Align Default Tolerance Values**: Change the `node_tolerance_px` default parameter to match `endpoint_tolerance_px`
   - Line 67: Change `node_tolerance_px: float = 25.0` to `node_tolerance_px: float = 15.0`
   - Or alternatively, derive `node_tolerance_px` from `endpoint_tolerance_px` by default

2. **Document Tolerance Consistency Requirement**: Add a comment or assertion explaining that these parameters must be consistent
   - Add inline comment near parameter definitions explaining the relationship
   - Consider adding a validation check that warns if tolerances are mismatched

3. **Alternative: Explicit Derivation**: Instead of separate parameters, derive `node_tolerance_px` from `endpoint_tolerance_px`
   - Remove `node_tolerance_px` as a separate parameter
   - Pass `endpoint_tolerance_px` directly to `polygonize_rooms()`
   - Update `polygonize_rooms()` signature if needed to accept the parameter with clearer naming

4. **Update Function Call**: Ensure the corrected tolerance is passed to `polygonize_rooms()`
   - Line 238-241: Verify `node_tolerance_px` parameter uses the aligned value
   - Ensure no hardcoded tolerance values override the parameter

5. **Consider Configuration Validation**: Add early validation to detect tolerance mismatches
   - Add assertion or warning if `node_tolerance_px != endpoint_tolerance_px`
   - This prevents future regressions from configuration changes

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code using floor plans that should produce rooms but don't, then verify the fix enables correct room detection while preserving existing behavior for floor plans already working correctly.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the tolerance mismatch is indeed the root cause. If we refute this hypothesis, we will need to re-analyze.

**Test Plan**: Use existing floor plan test cases from `backend/data/` or create synthetic floor plans with clear rectangular rooms. Run the UNFIXED pipeline with default parameters (25.0 px node tolerance, 15.0 px endpoint tolerance) and observe zero rooms detected. Then run with consistent tolerances (15.0 px for both) to verify this resolves the issue.

**Test Cases**:
1. **Simple Rectangular Rooms Test**: Load a floor plan with 2-3 rectangular rooms, run unfixed pipeline with mismatched tolerances (will fail - 0 rooms detected)
2. **Complex Floor Plan Test**: Load a floor plan with 5+ rooms and multiple wall intersections, run unfixed pipeline (will fail - 0 rooms detected)
3. **Open Plan Layout Test**: Load a floor plan with open areas and connecting spaces, run unfixed pipeline (will fail - 0 rooms detected)
4. **Manually Consistent Tolerance Test**: Run unfixed pipeline but manually override `node_tolerance_px=15.0` to verify this workaround succeeds (should detect rooms correctly)

**Expected Counterexamples**:
- Pipeline returns `MGRResult` with `rooms=[]` (empty list)
- 3D generation produces isolated wall segments without floor polygons
- Console logs show "Polygonization found 0 rooms"
- Possible root cause confirmation: Running with consistent tolerance produces non-zero rooms

### Fix Checking

**Goal**: Verify that for all floor plan inputs where the bug condition holds (tolerance mismatch), the fixed pipeline produces the expected behavior (successful room detection and connected 3D rendering).

**Pseudocode:**
```
FOR ALL floorplan WHERE isBugCondition(floorplan) DO
  result := run_mgr_pipeline_fixed(floorplan)
  ASSERT result.rooms.length > 0
  ASSERT walls_form_closed_regions(result.walls, result.rooms)
  ASSERT all_rooms_have_floor_meshes(result.scene_3d)
  ASSERT walls_are_connected(result.scene_3d)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all floor plan inputs where the bug condition does NOT hold (tolerances already consistent or pipeline already working), the fixed pipeline produces the same result as the original pipeline.

**Pseudocode:**
```
FOR ALL floorplan WHERE NOT isBugCondition(floorplan) DO
  result_original := run_mgr_pipeline_original(floorplan)
  result_fixed := run_mgr_pipeline_fixed(floorplan)
  ASSERT result_original.rooms = result_fixed.rooms
  ASSERT result_original.walls = result_fixed.walls
  ASSERT result_original.topology_valid = result_fixed.topology_valid
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Identify or create floor plans that currently work correctly with the existing pipeline. Run both unfixed and fixed pipelines on these inputs and compare results structurally (same room count, same wall topology, same 3D geometry).

**Test Cases**:
1. **Already Working Floor Plan Preservation**: Use any floor plan that currently detects rooms correctly, verify fixed pipeline produces identical results
2. **Custom Tolerance Configuration Preservation**: Test with manually configured consistent tolerances, verify behavior unchanged
3. **Edge Case Floor Plans Preservation**: Test floor plans with unusual layouts (L-shapes, T-junctions, curved approximations), verify no regression
4. **Minimal Room Floor Plans Preservation**: Test floor plans with single rooms or very simple layouts, verify no change

### Unit Tests

- Test `polygonize_rooms()` with various tolerance values to understand sensitivity
- Test `build_wall_graph()` with wall segments that have nearby but distinct endpoints at different tolerance thresholds
- Test edge cases: walls with very close parallel segments, T-junctions, cross-intersections
- Test that corrected tolerance produces non-empty room results for synthetic rectangular room inputs

### Property-Based Tests

- Generate random floor plan configurations with rectangular rooms and verify fixed pipeline detects at least the expected number of rooms
- Generate random wall graphs with known closed cycles and verify `polygonize_rooms()` with consistent tolerance detects corresponding polygons
- Test that for any floor plan with N closed wall regions, room detection produces at least N rooms (accounting for minimum area filtering)
- Test preservation: for floor plans already producing correct results, verify fixed pipeline output matches original output structurally

### Integration Tests

- Test full pipeline flow with sample floor plans from `backend/data/evaluation/`
- Test that detected rooms appear as floor polygons in generated GLB 3D output
- Test that walls in 3D scene form connected structures rather than floating segments
- Test that doors and windows are properly positioned relative to room boundaries after fix
- Verify visual output: render GLB files and confirm spatial coherence of wall structures
