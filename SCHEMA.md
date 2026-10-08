# Shared Schema

This document defines the logical structures shared between Python backend and TypeScript frontend.

## Core Models

### Confidence
```typescript
interface Confidence {
  overall: number;
  geometry: number;
  scale: number;
}
```

### Provenance
```typescript
interface Provenance {
  source: string;
  method: string;
}
```

### Dimension
```typescript
interface Dimension {
  value_mm: number;
  confidence: number;
}
```

### Wall
```typescript
interface Wall {
  id: string;
  start_point: [number, number];
  end_point: [number, number];
  thickness: number;
  height: number;
  provenance: Provenance;
}
```

### Opening (Door / Window)
```typescript
interface Opening {
  id: string;
  type: "door" | "window";
  wall_id: string;
  start_point: [number, number];
  end_point: [number, number];
}
```

### Room
```typescript
interface Room {
  id: string;
  label: string;
  polygon: [number, number][];
  area_m2: number;
}
```

### ReconstructionResult
```typescript
interface ReconstructionResult {
  scale_mm_per_px: number | null;
  rooms: Room[];
  walls: Wall[];
  doors: Opening[];
  windows: Opening[];
  confidence: Confidence;
  provenance: Provenance;
}
```
