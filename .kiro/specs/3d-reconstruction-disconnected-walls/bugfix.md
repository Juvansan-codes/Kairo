# Bugfix Requirements Document

## Introduction

The KAIRO floor plan reconstruction pipeline fails to generate proper 3D models from floor plans. Specifically, the room polygonization phase fails to detect any rooms (returns 0 rooms), which causes walls to render as disconnected floating segments rather than connected structures forming coherent spaces. This prevents proper 3D assembly of doors, windows, and floor elements.

The bug is caused by **highly fragmented wall masks** produced by the ResNet34-U-Net perception model. The perception model detects walls as 51 disconnected components (only 2008 pixels total, 0.77% of image), with individual fragments ranging from 4-168 pixels each. These tiny disconnected fragments cannot form closed polygonal regions required for room detection, regardless of geometric reconciliation parameters.

**Impact**: Complete failure of 3D reconstruction output - users cannot obtain usable 3D models from their floor plans.

---

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the ResNet34-U-Net perception model processes a real floor plan image THEN it produces a highly fragmented wall mask with 51 disconnected components averaging 39 pixels each, rather than continuous wall structures

1.2 WHEN the MGR pipeline attempts to extract wall segments from the fragmented mask THEN it produces 19 disconnected wall segments that do not form closed regions

1.3 WHEN `polygonize_rooms()` attempts to extract closed regions from disconnected wall segments THEN it fails to find any valid room polygons because the walls do not connect to form cycles

1.4 WHEN the 3D generator receives MGR results with zero rooms THEN it only renders individual wall segments without floor polygons, resulting in disconnected floating walls

1.5 WHEN doors and windows are processed with zero rooms detected THEN they are counted but not properly rendered in the 3D scene because there is no spatial context from room boundaries

### Expected Behavior (Correct)

2.1 WHEN the perception model processes a floor plan image THEN the wall mask SHALL contain connected wall structures with minimal fragmentation, enabling detection of closed room regions

2.2 WHEN the MGR pipeline processes fragmented wall masks THEN it SHALL apply morphological operations to bridge small gaps between wall fragments and connect nearby components

2.3 WHEN `polygonize_rooms()` attempts to extract closed regions from improved wall segments THEN it SHALL successfully detect room polygons from closed wall structures

2.4 WHEN the 3D generator receives MGR results with detected rooms THEN it SHALL render floor polygons for each room along with properly connected wall structures

2.5 WHEN doors and windows are processed with rooms detected THEN they SHALL be rendered as cutouts in walls with proper spatial placement relative to room boundaries

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the pipeline processes synthetic or clean floor plans where walls already form proper closed regions THEN the system SHALL CONTINUE TO detect and render those rooms correctly without degradation

3.2 WHEN the pipeline processes dimension evidence for metric calibration THEN the system SHALL CONTINUE TO apply scale factors to convert pixel coordinates to metric coordinates

3.3 WHEN the pipeline processes doors and windows with valid wall associations THEN the system SHALL CONTINUE TO reconcile those openings against wall geometry using the existing association logic

3.4 WHEN the 3D generator creates wall meshes with door/window cutouts THEN the system SHALL CONTINUE TO use the robust 1D segmentation approach for creating openings

3.5 WHEN the pipeline applies geometric reconciliation phases (snapping, merging, intersection splitting) THEN the system SHALL CONTINUE TO execute those phases with their existing parameters and behavior

3.6 WHEN topology validation is enabled THEN the system SHALL CONTINUE TO validate the geometric consistency of the final MGR result

---

## Bug Condition Derivation

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type PerceptionOutput
  OUTPUT: boolean
  
  // Returns true when the bug condition is met
  // X contains: wall_mask with fragmentation metrics
  RETURN (count_connected_components(X.wall_mask) > 20) 
         AND (mean_component_size(X.wall_mask) < 100)
         AND (X.wall_mask_has_potential_rooms)
END FUNCTION
```

**Concrete Example**: 
- Input floor plan: real_001.png (should contain 2-3 rooms based on visual inspection)
- Perception output: wall mask with 51 connected components
- Component sizes: 4px, 168px, 137px, 65px, 47px... (highly fragmented)
- Total wall pixels: 2008 (0.77% of 512x512 image)
- Result: 19 wall segments extracted, 0 rooms detected
- 3D output: disconnected floating wall segments

### Property Specification

```pascal
// Property: Fix Checking - Wall Fragment Connection Enables Room Detection
FOR ALL X WHERE isBugCondition(X) DO
  improved_mask ← apply_fragment_connection(X.wall_mask)
  result ← run_mgr_pipeline_with_improved_mask(improved_mask)
  ASSERT result.rooms.length > 0 
         AND walls_form_closed_regions(result.walls, result.rooms)
         AND all_rooms_have_floor_meshes(result.scene_3d)
         AND walls_are_connected(result.scene_3d)
END FOR
```

### Preservation Goal

```pascal
// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  result_original ← run_mgr_pipeline_original(X)
  result_fixed ← run_mgr_pipeline_fixed(X)
  ASSERT result_original.rooms = result_fixed.rooms
         AND result_original.walls.topology_preserved
         AND result_original.topology_valid = result_fixed.topology_valid
END FOR
```

This ensures that floor plans with non-fragmented wall masks continue to produce identical or better results after the fix.

---

## Technical Root Cause

**Location**: Perception model output processing in `backend/app/perception/adapter.py`

**Issue**: The ResNet34-U-Net perception model produces highly fragmented wall masks for real floor plans:

**Evidence from Investigation**:
```
=== Perception Output Analysis ===
Wall mask: 512x512 pixels
Unique values: [0, 1, 2, 3] (background, wall, door, window)
Wall pixel count: 2008 (0.77% of image)
Connected wall components: 51
Largest component: 168 pixels
Component sizes: 4, 168, 137, 65, 47, 31, 52, 134, 34...

=== Pipeline Behavior ===
Test          | Walls | Rooms | Result
--------------|-------|-------|--------
Synthetic     |     8 |     1 | ✓ Works
Real (before) |    19 |     0 | ✗ Fails
Real (after)  |    68 |     1 | ✓ Fixed
```

**Why Tolerance Changes Had No Effect**:
Testing with different tolerance values (25.0, 15.0, 3.0 px) all produced 0 rooms because the fundamental issue is not parameter misalignment but **incomplete/disconnected wall geometry** from the perception stage.

**Solution Direction**: Apply morphological closing and fragment connection operations to bridge gaps between wall components before geometric reconciliation, transforming fragmented masks into continuous wall structures capable of forming closed rooms.

---

## Solution Implemented

**Module Created**: `backend/app/geometry/fragment_connection.py`

**Key Operations**:
1. **Morphological Closing**: Use disk kernel (radius=8px) to bridge gaps between nearby wall fragments
2. **Small Fragment Removal**: Remove components smaller than 15 px² to eliminate noise
3. **Skeleton Normalization**: Apply skeletonization followed by controlled dilation to maintain consistent wall thickness
4. **Integration**: Enable by default in ResNetUNetPerception with `improve_walls=True` parameter

**Modified Files**:
- `backend/app/perception/adapter.py`: Added wall improvement call in `predict()` method
- Created `backend/app/geometry/fragment_connection.py`: New module for fragment connection

**Results**:
- Real floor plan wall detection: 19 → 68 walls (proper extraction from improved mask)
- Room detection: 0 → 1 room (successfully forms closed region)
- 3D output: Disconnected segments → Connected walls with floor polygons
- Topology validation: False → True
