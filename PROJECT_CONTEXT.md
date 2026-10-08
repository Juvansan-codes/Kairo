# HNX26EPS06 — CANONICAL PROJECT CONTEXT

## IMPORTANT

This document is the **single source of truth** for our HNX26EPS06 external hackathon project.

Every teammate's AI assistant should be given this context before doing project work.

Do NOT change the core architecture, tech stack, project scope, or research direction unless the team explicitly agrees.

When making implementation decisions, prioritize:

1. Reliability within a 24-hour hackathon
2. Judging rubric performance
3. Measurable research contribution
4. Clean integration between teammates
5. Demo stability
6. Simplicity over unnecessary complexity

---

# 1. HACKATHON PROBLEM

## Problem Statement

**HNX26EPS06 — 3D Scene Generation from Blueprints and Room Video Pitch**

The track asks teams to turn a 2D description of a static space into a navigable 3D model.

There are two possible modes:

### Mode A

Floor plan / architectural blueprint → 3D model

### Mode B

Room images/video → 3D scene with completion of unseen regions

---

# 2. OUR SELECTED MODE

## 🔒 LOCKED: MODE A

We are building:

> **Floor Plan / Blueprint → Metric 3D Model**

We are NOT implementing Mode B.

The input is a static architectural floor plan / blueprint.

The output is a navigable 3D representation of the space.

The generated model should contain:

* walls
* rooms
* doors
* windows
* floor
* sensible wall height
* correct or estimated metric scale
* clean topology
* standard 3D format
* browser-based interactive viewer

Primary output:

```text
scene.glb
```

Secondary output:

```text
scene.json
```

---

# 3. JUDGING RUBRIC

Mode A is scored out of 100 points:

### Layout accuracy — 40%

Wall placement, door/window placement, room layout, dimensions.

### Completeness — 15%

Every room and opening from the plan should be represented correctly.

### Model quality — 15%

Clean geometry, sensible proportions, scale, wall heights.

### 3D viewer usability — 10%

The output must be usable in a real 3D viewer.

### Research contribution — 20%

We must demonstrate something new/improved compared with a baseline using comparison and/or ablation.

---

# 4. CORE PROJECT IDEA

Our research contribution is:

# Metric-Aware Geometric Reconciliation (MGR)

The central idea is:

> Neural models provide semantic evidence. OCR provides measurement evidence. Computer vision provides geometric evidence. A deterministic reconciliation layer combines these signals to produce a metrically and topologically consistent floorplan before 3D generation.

We do NOT want:

```text
Floorplan → AI → arbitrary 3D
```

We want:

```text
Floorplan
   ↓
semantic perception
   +
geometric analysis
   +
dimension extraction
   ↓
Metric-Aware Geometric Reconciliation
   ↓
structured floorplan graph
   ↓
3D mesh
   ↓
GLB
```

The geometry is produced by deterministic/constraint-based processing rather than being hallucinated by an LLM.

---

# 5. WHY MGR IS OUR RESEARCH CONTRIBUTION

A neural prediction can be visually plausible while still being geometrically wrong.

Examples:

* walls that should meet do not meet
* fragmented walls appear as separate walls
* slightly angled walls should actually be orthogonal
* doors/windows float away from walls
* a room may be closed incorrectly
* dimensions may be interpreted incorrectly
* the model may have correct proportions but wrong physical scale

MGR addresses these issues by combining:

```text
semantic evidence
geometric evidence
dimension evidence
topological constraints
architectural priors
```

into a final structured representation.

---

# 6. FINAL PIPELINE

```text
                    FLOOR PLAN
                         │
                         ▼
                ┌────────────────┐
                │  PREPROCESSING  │
                └───────┬────────┘
                        │
                        ▼
                 Raster2Seq
                        │
                        ▼
          structured / semantic prediction
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      Geometry Analysis           OCR
             │                     │
             │              dimensions / labels
             │                     │
             └──────────┬──────────┘
                        ▼
          METRIC-AWARE GEOMETRIC
                 RECONCILIATION
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
     Wall Graph     Opening Graph   Scale Model
         │              │              │
         └──────────────┼──────────────┘
                        ▼
                 Room Polygonization
                        │
                        ▼
                   Room Graph
                        │
                        ▼
                  3D Generation
                        │
                        ▼
                      GLB
                        │
                        ▼
              Next.js 3D Viewer
```

---

# 7. FINALIZED TECH STACK

## Frontend

```text
Next.js 16
React 19
TypeScript
Tailwind CSS 4
shadcn/ui
```

The frontend stack is LOCKED.

Do not replace Next.js with Vite.

---

# 8. 3D VIEWER

```text
Three.js
React Three Fiber 9
Drei
GLTFLoader
OrbitControls
```

The viewer is integrated into the Next.js application.

The viewer should support:

* orbit
* zoom
* pan
* model loading
* room highlighting
* wall visibility toggle
* door visibility toggle
* window visibility toggle
* dimensions toggle
* basic statistics
* GLB export/download
* 2D ↔ 3D comparison where practical

Keep the viewer visually polished but do not spend excessive hackathon time on frontend decoration.

---

# 9. BACKEND

```text
Python 3.11
FastAPI
Pydantic
Uvicorn
uv
```

FastAPI handles the reconstruction pipeline.

Example endpoint:

```text
POST /api/reconstruct
```

Input:

```text
floorplan.png
```

Output:

```text
scene.glb
scene.json
```

The frontend communicates with FastAPI through HTTP.

---

# 10. PRIMARY FLOORPLAN MODEL

## 🔒 PRIMARY MODEL: Raster2Seq

Raster2Seq is the main modern perception/vectorization model we plan to test and use.

It is attractive because it produces structured floorplan representations rather than only raw pixel segmentation.

Use a pretrained checkpoint.

### IMPORTANT

We are NOT training Raster2Seq during the 24-hour hackathon.

We only use inference.

---

# 11. FALLBACK MODEL

## ResNet34 + U-Net

A practical four-class floorplan segmentation model is our fallback.

Expected semantic classes:

```text
BACKGROUND
WALL
DOOR
WINDOW
FLOOR
```

The fallback exists because hackathons fail due to dependency/inference issues, not only algorithmic problems.

If Raster2Seq becomes unusable because of environment/dependency problems, switch to the fallback rather than wasting the hackathon trying to repair a research environment indefinitely.

---

# 12. MODEL-AGNOSTIC ARCHITECTURE

The downstream geometry system must NOT depend tightly on Raster2Seq.

Use an adapter/interface conceptually like:

```text
Model Adapter
     │
 ┌───┼───────────┐
 ▼   ▼           ▼
R2S  U-Net      other
 │    │           │
 └────┼───────────┘
      ▼
Common Structured Representation
      ▼
MGR
```

This allows us to replace the perception model without rewriting the geometry engine.

---

# 13. OCR / DIMENSION ENGINE

## OCR

Use:

```text
PaddleOCR
```

The OCR subsystem should detect:

* printed dimensions
* room labels
* unit indicators
* numerical annotations
* rotated text

Examples:

```text
3500
4200
12'-6"
10'-0"
12' x 10'
BEDROOM
KITCHEN
LIVING
```

---

# 14. DIMENSION PROCESSING

Dimension extraction is one of the most important parts of the project.

Do NOT assume every number near a line is the wall dimension.

Real floor plans may contain:

* chained dimensions
* extension lines
* arrows
* tick marks
* rotated dimensions
* imperial notation
* metric notation
* room-label dimensions
* decorative / irrelevant numbers

The dimension engine should therefore perform:

```text
OCR
 ↓
text parsing
 ↓
unit normalization
 ↓
candidate classification
 ↓
geometry association
 ↓
scale candidates
 ↓
robust consensus
 ↓
final scale
```

---

# 15. SCALE ESTIMATION

Example:

```text
Detected dimension = 4200 mm
Measured dimension = 212 px

scale = 4200 / 212
      ≈ 19.81 mm/px
```

Do NOT trust a single candidate.

Instead:

```text
candidate scales:
19.8
19.7
19.9
37.2
```

Use robust consensus such as:

* median
* inlier filtering
* RANSAC-style reasoning
* weighted agreement

to determine the final scale.

---

# 16. SCALE FALLBACK HIERARCHY

Use this order:

```text
1. Printed dimensions
2. Multiple printed dimensions
3. Room-label dimensions
4. Overall plan span / area information
5. Known door-width prior
6. Wall-thickness prior
7. Relative scale only
```

If the system does not have reliable metric information, it must explicitly mark scale as estimated.

Never silently claim an exact real-world scale when the evidence does not support it.

---

# 17. VLM USAGE

VLMs are allowed ONLY as optional verifiers.

Good use:

```text
OCR detects uncertain text
        ↓
VLM verifies:
"Is this likely a dimension?"
        ↓
confidence
```

Bad use:

```text
Floorplan → VLM → invented coordinates → 3D
```

The VLM must NOT be responsible for final geometry.

The final geometry must remain deterministic and auditable.

---

# 18. COMPUTER VISION STACK

```text
OpenCV
scikit-image
```

OpenCV is used for:

* image normalization
* thresholding
* morphology
* denoising
* contour processing
* connected components
* deskew
* perspective correction
* image cleanup

scikit-image is mainly used for:

```text
skeletonization
```

---

# 19. GEOMETRY EXTRACTION

### Important correction

Hough transform is NOT the primary wall reconstruction method.

It can be used as a supporting signal if helpful.

Primary geometry path:

```text
wall/structure mask
      ↓
morphological cleanup
      ↓
skeletonization
      ↓
junction / endpoint detection
      ↓
segment tracing
      ↓
PCA / least-squares line fitting
      ↓
collinear merging
      ↓
wall graph
```

This is more robust to fragmented wall predictions than blindly applying Hough lines.

---

# 20. WALL GRAPH

The wall graph should represent:

### Nodes

* wall endpoints
* intersections
* junctions

### Edges

* wall segments

### Metadata

* length
* angle
* confidence
* source
* thickness where available

Conceptually:

```text
A ───────────── B
│              │
│              │
C ─────────────D
```

---

# 21. GEOMETRIC RECONCILIATION

MGR should enforce:

## Manhattan alignment

For architectural layouts:

```text
0°
90°
```

are common.

A predicted wall at 89° may be snapped to 90° if confidence and context support it.

## Collinearity

Merge fragmented segments that represent the same wall.

## Intersection consistency

Walls that should connect must connect cleanly.

## Opening binding

Doors and windows should belong to actual walls.

## Opening snapping

Small prediction offsets should be corrected by snapping openings onto the nearest valid wall.

---

# 22. ROOM EXTRACTION

Room extraction is mandatory.

Pipeline:

```text
Wall Graph
   ↓
line noding
   ↓
closed regions
   ↓
polygonization
   ↓
room polygons
```

Use Shapely.

Each room should have metadata such as:

```json
{
  "id": "R01",
  "polygon": [],
  "area_m2": 14.32,
  "label": "Bedroom"
}
```

Room polygons are useful for:

* 3D generation
* room highlighting
* area calculation
* evaluation
* UI

---

# 23. GEOMETRY / GRAPH STACK

Use:

```text
Shapely
NetworkX
NumPy
SciPy
```

### Shapely

For:

* LineString
* Polygon
* intersection
* union
* difference
* buffer
* snap
* polygonization

### NetworkX

For:

* graph construction
* connectivity
* traversal
* topology validation
* connected components

### NumPy / SciPy

For:

* vector math
* distances
* PCA
* fitting
* optimization helpers
* robust scale estimation

---

# 24. 3D GENERATION

Use:

```text
trimesh
```

The structured geometry is converted into 3D.

Generate:

```text
floor
walls
doors
windows
optional ceiling
```

Wall height should be sensible.

If wall height is not present in the input, use a documented default prior.

Do not pretend that a default wall height is extracted from the plan.

---

# 25. OUTPUT FORMAT

Primary:

```text
scene.glb
```

Secondary:

```text
scene.json
```

GLB must be directly viewable in the browser.

JSON should contain:

```text
scale
rooms
walls
doors
windows
dimensions
confidence
provenance
assumptions
```

---

# 26. PROVENANCE

Every major reconstructed element should have provenance.

Example:

```text
WALL_01
source:
  neural_prediction
  +
geometry_reconciliation

DOOR_05
source:
  neural_prediction
  +
wall_snapping

SCALE
source:
  OCR
  +
dimension_consensus

WALL_HEIGHT
source:
  default_prior
```

This is useful scientifically and prevents the UI from making unsupported claims.

---

# 27. CONFIDENCE

Never fabricate confidence percentages.

Confidence must be computed from real signals.

Possible inputs:

```text
model confidence
OCR confidence
geometry fit error
scale agreement
topology consistency
opening-wall consistency
```

Example:

```text
Wall confidence
Opening confidence
Scale confidence
Topology confidence
```

The exact scoring formula can be defined during implementation.

---

# 28. INPUT PREPROCESSING

The system should support, where practical:

* PNG
* JPG/JPEG
* PDF
* scanned plans
* rotated plans
* photographed plans

Preprocessing:

```text
input
 ↓
document detection
 ↓
crop
 ↓
perspective correction
 ↓
deskew
 ↓
orientation normalization
 ↓
resolution normalization
```

Do not assume the judge will provide perfectly clean digital floor plans.

---

# 29. CLI

The project must also have a CLI.

Example:

```bash
python reconstruct.py \
  --input floorplan.png \
  --output scene.glb
```

or equivalent.

The CLI is important because judges may want to evaluate unseen inputs without using the web interface.

---

# 30. API / DATA CONTRACT

The frontend should NOT know internal Python implementation details.

Backend should expose structured outputs.

Example:

```json
{
  "status": "success",
  "model_url": "/results/scene.glb",
  "metadata": {
    "rooms": 5,
    "walls": 18,
    "doors": 6,
    "windows": 9,
    "scale_mm_per_px": 19.82
  }
}
```

The exact field names can evolve, but the contract must remain stable once frontend/backend integration begins.

---

# 31. REPOSITORY STRUCTURE

Recommended structure:

```text
project-root/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   ├── perception/
│   │   ├── ocr/
│   │   ├── geometry/
│   │   ├── reconstruction/
│   │   └── utils/
│   │
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── evaluation/
│   │
│   └── reconstruct.py
│
├── models/
│
├── outputs/
│
├── evaluation/
│   ├── metrics/
│   ├── ground_truth/
│   └── results/
│
├── docs/
│
└── README.md
```

The exact structure can be adjusted, but frontend, backend, geometry, evaluation and data should remain clearly separated.

---

# 32. EVALUATION PLAN

Evaluation must begin at **Hour 0**.

We need two datasets.

## Dataset A — Public benchmark

Use the CubiCasa5K test split.

Purpose:

* benchmark layout quality
* compare baseline vs ours
* produce reproducible research results

## Dataset B — Custom real-world evaluation set

Create approximately 10–15 varied floor plans.

Include:

* clean architectural plans
* scans
* phone photographs
* rotated plans
* text-heavy plans
* dimension-heavy plans
* varied layouts

Manually establish ground truth for:

* walls
* rooms
* doors
* windows
* dimensions / scale

---

# 33. METRICS

We should calculate real metrics such as:

### Layout

* wall IoU
* room IoU
* opening placement accuracy

### Dimension

* mean absolute dimension error
* percentage relative error

### Completeness

* room recall
* door/window recall

### Geometry

* Chamfer distance where practical
* topology consistency

### System

* inference time
* successful reconstruction rate

Do NOT invent or manually choose favorable numbers.

---

# 34. BASELINES

We should maintain at least:

## B0 — Simple baseline

```text
Raster2Seq
    ↓
direct structured geometry / extrusion
```

or the simplest valid model-to-3D route.

## Strong external baseline

Use the strongest practical modern public floorplan-vectorization approach that we can actually run.

Preferred candidate:

```text
Raster2Seq
```

Other candidates may be tested during the pre-hackathon spike.

## Fallback baseline

```text
ResNet34-U-Net
```

---

# 35. ABLATION

Our research comparison should demonstrate the contribution of MGR.

Potential ladder:

```text
B0
Raster2Seq baseline

B1
+ geometric reconciliation

B2
+ metric dimension calibration

B3
+ topology / opening validation

OURS
full MGR
```

Expected table:

| Method          | Wall/Layout IoU | Dimension Error | Opening Completeness |
| --------------- | --------------: | --------------: | -------------------: |
| B0              |          actual |          actual |               actual |
| Strong baseline |          actual |          actual |               actual |
| + Geometry      |          actual |          actual |               actual |
| + Calibration   |          actual |          actual |               actual |
| Full MGR        |          actual |          actual |               actual |

No fabricated results.

---

# 36. PRE-HACKATHON SPIKE

Before the 24-hour event, if preparation is allowed, run a 2-hour technical spike.

Use approximately 5 varied floor plans.

Test:

```text
Raster2Seq
ResNet34-U-Net
optional stronger model
```

Measure:

* installation difficulty
* dependency problems
* inference speed
* wall quality
* room quality
* opening quality
* OCR behavior
* scale extraction
* output stability

Then lock the model.

### Important

We should not spend the hackathon deciding what model to use.

That decision should be made before the clock starts.

---

# 37. 24-HOUR EXECUTION PLAN

## Hour 0–2

* environment setup
* evaluate model installation
* establish dataset
* run first baseline
* establish repo structure

## Hour 2–4

* baseline inference
* initial geometry
* first GLB
* first viewer integration

## Hour 4–8

* skeletonization
* junction detection
* wall graph
* segment fitting
* snapping / merging

## Hour 6–10

Parallel work:

* OCR
* dimension parsing
* scale candidates
* unit normalization

## Hour 10–12

### MVP DEADLINE

Must have:

```text
floorplan
 ↓
baseline/model
 ↓
basic geometry reconciliation
 ↓
basic scale
 ↓
GLB
 ↓
viewer
```

At Hour 12, the system must already work end-to-end.

## Hour 12–16

* better geometric reconciliation
* room polygonization
* opening validation
* improved metric calibration

## Hour 16–18

* rotated / photographed plan handling
* provenance
* confidence
* viewer improvements

## Hour 18–20

* evaluation
* baseline comparison
* ablation
* metrics

## Hour 20–22

* fix high-impact failures
* improve robustness
* finalize demo cases

## Hour 22–24

* freeze code
* write-up
* screenshots
* architecture diagram
* demo script
* submission

No major architectural changes after freeze.

---

# 38. TEAM OF 4

## Person 1 — Perception + Dimensions

Responsible for:

* Raster2Seq
* fallback segmentation
* model adapter
* PaddleOCR
* dimension parsing
* unit handling
* scale estimation
* optional VLM verification

## Person 2 — Geometry / MGR

Responsible for:

* OpenCV processing
* skeletonization
* junction detection
* PCA / fitting
* wall graph
* segment merging
* snapping
* topology
* polygonization
* room graph

This is the primary research role.

## Person 3 — 3D + Frontend

Responsible for:

* trimesh
* wall extrusion
* door/window mesh
* GLB
* Three.js
* React Three Fiber
* Next.js
* Tailwind
* shadcn/ui
* viewer

## Person 4 — Integration + Evaluation

Responsible for:

* FastAPI
* API contract
* CLI
* evaluation dataset
* ground truth
* metrics
* baseline comparison
* ablation
* integration
* final documentation
* demo flow

---

# 39. TEAM WORKING RULES

## Rule 1 — Keep interfaces stable

Do not frequently change:

* API response shape
* JSON schema
* geometry data structures
* file locations

without informing the other teammates.

## Rule 2 — Commit small changes

Prefer:

```text
feature-specific commits
```

instead of huge unrelated commits.

## Rule 3 — Test before handing off

Every teammate should provide:

* sample input
* expected output
* usage instructions
* known limitations

## Rule 4 — Do not rewrite another person's module without agreement

Fix your own layer first.

## Rule 5 — Prioritize integration

A partially imperfect integrated pipeline is more valuable than five isolated perfect modules.

---

# 40. THINGS WE ARE NOT BUILDING

Do NOT add these unless the entire team explicitly decides otherwise:

```text
Mode B video reconstruction
NeRF
Gaussian splatting
4D reconstruction
furniture reconstruction
photorealistic rendering
full BIM system
Unity
Unreal
MongoDB
Firebase
Supabase
Redis
Celery
Kubernetes
authentication
complex cloud architecture
large-scale model training
```

These are outside the core 24-hour objective.

---

# 41. PRODUCT/DESIGN DIRECTION

The UI should be:

* minimalist
* modern
* clean
* professional
* responsive

Preferred visual direction:

```text
white / black
+
orange accent
```

Avoid:

* excessive gradients
* purple AI-style gradients
* excessive glassmorphism
* cluttered dashboards
* unnecessary animations

The 3D model should be the visual focus.

---

# 42. IDEAL USER FLOW

```text
1. Upload floor plan
          ↓
2. Preview 2D plan
          ↓
3. Click "Reconstruct"
          ↓
4. Processing state
          ↓
5. 3D model appears
          ↓
6. Orbit / zoom
          ↓
7. Toggle walls / doors / windows
          ↓
8. Inspect dimensions / room data
          ↓
9. Export GLB
```

Target a simple, obvious workflow.

---

# 43. DEMO STORY

The demo should show:

### Step 1

Upload an actual floor plan.

### Step 2

Show the extracted structure.

### Step 3

Show dimensions/scale being inferred.

### Step 4

Generate the 3D model.

### Step 5

Orbit the 3D model.

### Step 6

Highlight a room and show its dimensions.

### Step 7

Toggle walls/doors/windows.

### Step 8

Show baseline vs MGR if possible.

### Step 9

Show evaluation results.

The judges should understand the research contribution in under a few minutes.

---

# 44. CORE PITCH

Do NOT pitch:

> "We use AI to convert floorplans into 3D."

Instead:

> **"We introduce a metric-aware geometric reconciliation layer that converts noisy floor-plan predictions into a topologically consistent and dimensionally grounded 3D scene."**

Expanded explanation:

> The perception model identifies the semantic structure of the floor plan. OCR extracts dimensional evidence. Computer vision recovers geometric structure. Our reconciliation layer combines these signals and enforces architectural/topological consistency before generating the final metric 3D model.

---

# 45. RESEARCH HYPOTHESIS

Our hypothesis is:

> **Combining learned semantic predictions with explicit geometric and dimensional constraints reduces structural and metric errors compared with direct floor-plan vectorization or segmentation-to-extrusion pipelines.**

The ablation study should determine whether this is actually true.

---

# 46. SUCCESS CRITERIA

The project is considered successful if:

### Minimum

* one floor plan can be processed end-to-end
* walls are reconstructed
* rooms exist
* doors/windows exist
* a 3D model is generated
* GLB loads correctly
* browser viewer works

### Strong

* metric scale works
* room polygons are correct
* opening placement is robust
* photographed/rotated plans work
* measurable improvement over baseline exists

### Excellent

* strong baseline comparison
* strong ablation
* low dimension error
* clean topology
* polished viewer
* reliable CLI
* standard GLB output
* clear research narrative

---

# 47. WHEN MAKING TECHNICAL DECISIONS

Every AI assistant should evaluate proposed changes using this priority:

```text
1. Does it improve judging performance?
2. Does it improve geometry/metric accuracy?
3. Can it run reliably within 24 hours?
4. Does it integrate with the existing architecture?
5. Does it create extra dependency risk?
6. Does it actually contribute to our research claim?
```

If a proposed technology does not provide a meaningful benefit, do not add it just because it is trendy.

---

# 48. NON-NEGOTIABLE PRINCIPLES

### Principle 1

**Geometry is authoritative.**

Neural predictions are evidence, not final truth.

### Principle 2

**Do not fabricate confidence.**

All confidence values must come from real signals.

### Principle 3

**Do not fabricate evaluation metrics.**

Every result shown to judges must come from a real run.

### Principle 4

**Do not overbuild.**

We have 24 hours.

### Principle 5

**MVP first.**

An end-to-end working system comes before advanced features.

### Principle 6

**Model and geometry must remain decoupled.**

We must be able to replace the perception model without rewriting MGR.

### Principle 7

**Every feature must justify its engineering cost.**

---

# 49. FINAL LOCKED STACK

```text
FRONTEND
Next.js 16
React 19
TypeScript
Tailwind CSS 4
shadcn/ui

3D VIEWER
Three.js
React Three Fiber 9
Drei
GLTFLoader
OrbitControls

BACKEND
Python 3.11
FastAPI
Pydantic
Uvicorn
uv

PRIMARY MODEL
Raster2Seq

FALLBACK
ResNet34 + U-Net

OCR
PaddleOCR

CV
OpenCV
scikit-image

GEOMETRY
Shapely
NetworkX
NumPy
SciPy

3D GENERATION
trimesh

DOCUMENTS
PyMuPDF

OUTPUT
GLB
JSON
```

---

# 50. CURRENTLY LOCKED VS OPEN

## 🔒 LOCKED

* Mode A
* Floor plan → 3D
* Next.js frontend
* React
* TypeScript
* Tailwind CSS
* shadcn/ui
* Three.js
* React Three Fiber
* FastAPI
* Raster2Seq as primary candidate
* ResNet34-U-Net as fallback
* PaddleOCR
* OpenCV
* scikit-image
* Shapely
* NetworkX
* NumPy / SciPy
* trimesh
* PyMuPDF
* GLB
* JSON
* MGR research direction
* deterministic geometry
* evaluation + ablation
* CLI

## ⚠️ OPEN BEFORE HACKATHON

* final Raster2Seq environment verification
* exact pretrained checkpoint
* exact model adapter format
* optional stronger secondary baseline
* optional VLM verifier
* final metric definitions / evaluation implementation
* exact UI details

These should be resolved during the pre-hackathon spike, not during the main event unless necessary.

---

# 51. WHAT YOUR AI SHOULD DO WITH THIS CONTEXT

When a teammate gives this context to an AI assistant, the assistant should:

* understand the complete architecture
* avoid suggesting unrelated technologies
* respect the locked stack
* make modular changes
* preserve existing API/data contracts
* focus on the teammate's assigned module
* communicate assumptions
* prioritize integration
* avoid fake metrics
* avoid unnecessary complexity

The AI should behave as a **technical collaborator on this exact project**, not as a generic coding assistant.

---

# 52. TEAMMATE-SPECIFIC CONTEXT

After pasting this master context, each teammate should append:

```text
MY ROLE:
[Person 1 / Person 2 / Person 3 / Person 4]

MY RESPONSIBILITIES:
[list]

CURRENT TASK:
[task]

CURRENT FILES:
[list]

DEPENDENCIES:
[list]

EXPECTED OUTPUT:
[list]

DO NOT MODIFY:
[list]
```

This lets every teammate AI share the same global understanding while still focusing on the correct subsystem.
