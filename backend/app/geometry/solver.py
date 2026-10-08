"""
MGR geometry solver.

Phase 2: Morphological cleanup & skeletonization
    wall mask  →  morphological cleanup  →  skeletonization  →  clean skeleton

Phase 3: Skeleton graph extraction & geometric line fitting
    clean skeleton  →  endpoints/junctions  →  path tracing  →  PCA line fitting  →  WallSegment objects

Later phases will add wall-graph generation, room polygonization, metric calibration, etc.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import scipy.ndimage as ndi
from skimage.morphology import (
    closing,
    disk,
    opening,
    remove_small_objects,
    skeletonize,
)

from app.geometry.types import WallSegment


# ---------------------------------------------------------------------------
# Phase 2 – Validation, Normalization & Morphological Cleanup Helpers
# ---------------------------------------------------------------------------

def _validate_mask(mask: np.ndarray) -> None:
    """Raise *ValueError* or *TypeError* if *mask* is not a usable 2-D array."""
    if not isinstance(mask, np.ndarray):
        raise TypeError(
            f"mask must be a numpy ndarray, got {type(mask).__name__}"
        )
    if mask.ndim != 2:
        raise ValueError(
            f"mask must be 2-D, got {mask.ndim}-D array with shape {mask.shape}"
        )
    if mask.size == 0:
        raise ValueError("mask is empty (zero elements)")


def _normalize_mask(mask: np.ndarray) -> np.ndarray:
    """Convert an arbitrary binary-ish mask to a strict ``bool`` array.

    Accepted encodings:

    * ``bool`` arrays  – used as-is.
    * ``0 / 1`` integer or float arrays.
    * ``0 / 255`` image-style arrays.

    Any value > 0 is treated as *True* (wall).
    """
    if mask.dtype == bool:
        return mask.copy()
    return mask.astype(bool)


def _cleanup_wall_mask(
    mask: np.ndarray,
    *,
    min_object_size: int = 64,
    close_radius: int = 3,
    open_radius: int = 1,
) -> np.ndarray:
    """Apply morphological cleanup to a **boolean** wall mask.

    Steps
    -----
    1. Remove small isolated noise blobs (area < *min_object_size* pixels).
    2. Morphological closing with a disk of *close_radius* to bridge
       small gaps between wall fragments.
    3. Morphological opening with a disk of *open_radius* to remove
       tiny protrusions introduced by closing.

    Parameters
    ----------
    mask:
        Boolean 2-D array where ``True`` marks wall pixels.
    min_object_size:
        Connected components smaller than this (in pixels) are removed.
    close_radius:
        Radius of the structuring element used for morphological closing.
    open_radius:
        Radius of the structuring element used for morphological opening.
        Set to 0 to skip opening.

    Returns
    -------
    np.ndarray
        Cleaned boolean mask.
    """
    # 1. Remove small noise blobs
    # max_size removes objects with area <= threshold
    cleaned = remove_small_objects(mask, max_size=min_object_size - 1)

    # 2. Close small gaps
    if close_radius > 0:
        selem_close = disk(close_radius)
        cleaned = closing(cleaned, footprint=selem_close)

    # 3. Light opening to smooth jagged edges from closing
    if open_radius > 0:
        selem_open = disk(open_radius)
        cleaned = opening(cleaned, footprint=selem_open)

    return cleaned.astype(bool)


# ---------------------------------------------------------------------------
# Phase 2 Public API – Skeletonization
# ---------------------------------------------------------------------------

def skeletonization(mask: np.ndarray) -> np.ndarray:
    """Produce a one-pixel-wide skeleton from a binary wall mask.

    Full pipeline:

    1. **Validate** – ensure *mask* is a 2-D NumPy array with data.
    2. **Normalize** – convert any encoding (bool / 0-1 / 0-255) to bool.
    3. **Morphological cleanup** – remove noise, close small gaps.
    4. **Skeletonize** – reduce cleaned walls to a medial-axis skeleton.

    Parameters
    ----------
    mask : np.ndarray
        2-D array representing a binary wall mask.
        Accepted encodings: bool, 0/1, 0/255.

    Returns
    -------
    np.ndarray
        Boolean 2-D array of the same shape as *mask* where ``True``
        marks skeleton pixels.

    Raises
    ------
    TypeError
        If *mask* is not a NumPy array.
    ValueError
        If *mask* is not 2-D or is empty.
    """
    # Step 1 – validate
    _validate_mask(mask)

    # Step 2 – normalize to bool
    binary_mask = _normalize_mask(mask)

    # If the mask is entirely empty after normalization, return zeros
    if not binary_mask.any():
        return np.zeros_like(binary_mask, dtype=bool)

    # Step 3 – morphological cleanup
    cleaned = _cleanup_wall_mask(binary_mask)

    # If cleanup removed everything (e.g. the input was only noise),
    # return an empty skeleton rather than erroring.
    if not cleaned.any():
        return np.zeros_like(binary_mask, dtype=bool)

    # Step 4 – skeletonize
    skeleton = skeletonize(cleaned)

    return skeleton.astype(bool)


# ---------------------------------------------------------------------------
# Phase 3 – Graph Extraction & Path Tracing Helpers
# ---------------------------------------------------------------------------

def _trace_skeleton_paths(skeleton: np.ndarray) -> list[list[tuple[int, int]]]:
    """Trace ordered paths of pixel coordinates between graph nodes.

    Uses 8-connectivity to classify pixels into:
    * endpoints (degree == 1)
    * normal path pixels (degree == 2)
    * junction pixels (degree >= 3)

    Junction pixels that are 8-connected are clustered into cohesive junction
    nodes. Paths are traced along degree-2 pixels between junction clusters,
    endpoints, and within closed loops. Each undirected edge is traversed at
    most once to eliminate duplicate reverse paths and infinite loops.
    """
    H, W = skeleton.shape
    kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int32)
    deg = ndi.convolve(skeleton.astype(np.int32), kernel, mode="constant", cval=0) * skeleton

    # Label connected components of junction pixels (degree >= 3)
    junc_mask = deg >= 3
    junc_labels, num_junc = ndi.label(junc_mask, structure=np.ones((3, 3)))

    # Representative point for each junction cluster
    junc_centers: dict[int, tuple[int, int]] = {}
    for j_id in range(1, num_junc + 1):
        pixels = list(zip(*np.where(junc_labels == j_id)))
        r_mean = float(np.mean([p[0] for p in pixels]))
        c_mean = float(np.mean([p[1] for p in pixels]))
        best_p = min(pixels, key=lambda p: (p[0] - r_mean) ** 2 + (p[1] - c_mean) ** 2)
        junc_centers[j_id] = (int(best_p[0]), int(best_p[1]))

    visited_edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    def edge_key(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
        return (min(p1, p2), max(p1, p2))

    def get_neighbors(r: int, c: int) -> list[tuple[int, int]]:
        nbrs: list[tuple[int, int]] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and skeleton[nr, nc]:
                    nbrs.append((nr, nc))
        return nbrs

    raw_paths: list[list[tuple[int, int]]] = []

    # 1. Trace branches leaving each junction cluster
    for j_id in range(1, num_junc + 1):
        j_pixels = set(zip(*np.where(junc_labels == j_id)))
        center = junc_centers[j_id]

        for p in j_pixels:
            p_tuple = (int(p[0]), int(p[1]))
            for q in get_neighbors(p_tuple[0], p_tuple[1]):
                if q in j_pixels:
                    continue
                ek = edge_key(p_tuple, q)
                if ek in visited_edges:
                    continue
                visited_edges.add(ek)

                path: list[tuple[int, int]] = [center, q]
                curr = q
                prev = p_tuple

                while deg[curr] == 2:
                    cands = [n for n in get_neighbors(curr[0], curr[1]) if n != prev]
                    if not cands:
                        break
                    nxt = cands[0]
                    nek = edge_key(curr, nxt)
                    if nek in visited_edges:
                        path.append(nxt)
                        break
                    visited_edges.add(nek)
                    prev = curr
                    curr = nxt
                    path.append(curr)

                    if junc_mask[curr]:
                        other_j_id = int(junc_labels[curr])
                        if other_j_id > 0:
                            path[-1] = junc_centers[other_j_id]
                        break

                raw_paths.append(path)

    # 2. Trace branches starting from endpoints (degree == 1)
    endpoints = list(zip(*np.where(deg == 1)))
    for ep in endpoints:
        ep_tuple = (int(ep[0]), int(ep[1]))
        nbrs = get_neighbors(ep_tuple[0], ep_tuple[1])
        if not nbrs:
            continue
        q = nbrs[0]
        ek = edge_key(ep_tuple, q)
        if ek in visited_edges:
            continue
        visited_edges.add(ek)

        path = [ep_tuple, q]
        curr = q
        prev = ep_tuple

        while deg[curr] == 2:
            cands = [n for n in get_neighbors(curr[0], curr[1]) if n != prev]
            if not cands:
                break
            nxt = cands[0]
            nek = edge_key(curr, nxt)
            if nek in visited_edges:
                path.append(nxt)
                break
            visited_edges.add(nek)
            prev = curr
            curr = nxt
            path.append(curr)

            if junc_mask[curr]:
                other_j_id = int(junc_labels[curr])
                if other_j_id > 0:
                    path[-1] = junc_centers[other_j_id]
                break

        raw_paths.append(path)

    # 3. Trace closed loops of normal path pixels (degree == 2 without endpoints/junctions)
    deg2_pixels = list(zip(*np.where(deg == 2)))
    for p in deg2_pixels:
        p_tuple = (int(p[0]), int(p[1]))
        for q in get_neighbors(p_tuple[0], p_tuple[1]):
            ek = edge_key(p_tuple, q)
            if ek in visited_edges:
                continue
            visited_edges.add(ek)

            path = [p_tuple, q]
            curr = q
            prev = p_tuple

            while curr != p_tuple:
                cands = [n for n in get_neighbors(curr[0], curr[1]) if n != prev]
                if not cands:
                    break
                nxt = cands[0]
                nek = edge_key(curr, nxt)
                if nek in visited_edges:
                    path.append(nxt)
                    break
                visited_edges.add(nek)
                prev = curr
                curr = nxt
                path.append(curr)

            raw_paths.append(path)

    return raw_paths


def _split_path_rdp(pts: np.ndarray, tolerance: float = 1.5) -> list[np.ndarray]:
    """Recursively split a polyline path at points of maximum deviation from the chord.

    Uses the Ramer-Douglas-Peucker algorithm. This splits non-collinear paths
    (such as L-corners and rectangular loop corners) into straight subpaths.
    """
    if len(pts) <= 2:
        return [pts]

    p1 = pts[0]
    p2 = pts[-1]
    chord = p2 - p1
    chord_len = float(np.linalg.norm(chord))

    if chord_len < 1e-6:
        # Closed loop where start and end points coincide
        dists = np.linalg.norm(pts - p1, axis=1)
        max_idx = int(np.argmax(dists))
        if dists[max_idx] > tolerance:
            sub1 = _split_path_rdp(pts[: max_idx + 1], tolerance)
            sub2 = _split_path_rdp(pts[max_idx:], tolerance)
            return sub1 + sub2
        return [pts]

    line_dir = chord / chord_len
    normal = np.array([-line_dir[1], line_dir[0]])
    dists = np.abs((pts - p1) @ normal)
    max_idx = int(np.argmax(dists))

    if dists[max_idx] > tolerance:
        sub1 = _split_path_rdp(pts[: max_idx + 1], tolerance)
        sub2 = _split_path_rdp(pts[max_idx:], tolerance)
        return sub1 + sub2

    return [pts]


def _fit_line_pca(
    pts: np.ndarray,
    idx: int,
    min_length_px: float = 3.0,
    min_pixels: int = 3,
) -> WallSegment | None:
    """Fit a geometric line to an ordered sequence of 2D points using PCA.

    Parameters
    ----------
    pts : np.ndarray
        Nx2 array of (x, y) coordinates where x is column and y is row.
    idx : int
        Index for generating the segment ID.
    min_length_px : float
        Minimum length threshold to keep the segment.
    min_pixels : int
        Minimum number of supporting points required.

    Returns
    -------
    WallSegment | None
        Fitted WallSegment object, or None if the segment is too short.
    """
    N = len(pts)
    if N < min_pixels:
        return None

    centroid = np.mean(pts, axis=0)
    centered = pts - centroid

    # Covariance matrix and principal direction via eigendecomposition
    cov = (centered.T @ centered) / N
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    # Dominant direction is the eigenvector for the maximum eigenvalue
    v = eigenvectors[:, -1]
    # Residual error is the perpendicular standard deviation (RMS error)
    residual = float(np.sqrt(max(0.0, float(eigenvalues[0]))))

    # Orient direction vector from start of path towards end
    start_to_end = pts[-1] - pts[0]
    if float(v @ start_to_end) < 0:
        v = -v

    # Project path points onto the dominant line axis
    projections = centered @ v
    t_min = float(np.min(projections))
    t_max = float(np.max(projections))

    start_pt = centroid + t_min * v
    end_pt = centroid + t_max * v
    length = float(t_max - t_min)

    if length < min_length_px:
        return None

    dx = float(end_pt[0] - start_pt[0])
    dy = float(end_pt[1] - start_pt[1])
    angle_deg = math.degrees(math.atan2(dy, dx))
    if angle_deg == -180.0:
        angle_deg = 180.0

    # Confidence calculation derived from:
    # 1. Line fitting residual: 1.0 / (1.0 + residual)
    # 2. Path length factor: scales smoothly from 0.5 up to 1.0 at 20px
    s_fit = 1.0 / (1.0 + residual)
    s_len = min(1.0, 0.5 + 0.5 * (length / 20.0))
    confidence = round(float(s_fit * s_len), 3)

    return WallSegment(
        id=f"wall_{idx}",
        start=(round(float(start_pt[0]), 2), round(float(start_pt[1]), 2)),
        end=(round(float(end_pt[0]), 2), round(float(end_pt[1]), 2)),
        length_px=round(float(length), 2),
        angle_deg=round(float(angle_deg), 2),
        confidence=confidence,
        source=["skeleton"],
    )


# ---------------------------------------------------------------------------
# Phase 3 Public API – Extract Wall Segments
# ---------------------------------------------------------------------------

def extract_wall_segments(
    skeleton: np.ndarray,
    *,
    min_length_px: float = 3.0,
    min_pixels: int = 3,
    rdp_tolerance: float = 1.5,
) -> list[WallSegment]:
    """Convert a binary one-pixel skeleton into geometric WallSegment objects.

    Full pipeline:

    1. **Validate & Normalize** – accept boolean, 0/1, or 0/255 2D NumPy arrays.
    2. **Detect Neighborhoods** – compute 8-connectivity degrees; classify
       endpoints (deg 1), path pixels (deg 2), and junction clusters (deg >= 3).
    3. **Trace Paths** – traverse connected pixel paths between graph nodes
       without duplicates or infinite loops; handle closed loops safely.
    4. **Split Non-Collinear Paths** – apply Ramer-Douglas-Peucker to partition
       corners and bends into straight subpaths.
    5. **Fit Geometric Lines** – use PCA on each straight subpath to calculate
       start, end, length, angle, residual, and confidence.

    Parameters
    ----------
    skeleton : np.ndarray
        2-D NumPy array representing a binary skeleton.
    min_length_px : float, optional
        Minimum length in pixels for a valid wall segment (default: 3.0).
    min_pixels : int, optional
        Minimum number of skeleton pixels supporting a segment (default: 3).
    rdp_tolerance : float, optional
        Tolerance in pixels for splitting non-straight paths (default: 1.5).

    Returns
    -------
    list[WallSegment]
        List of extracted geometric wall segments.

    Raises
    ------
    TypeError
        If *skeleton* is not a NumPy array.
    ValueError
        If *skeleton* is not 2-D or is empty.
    """
    _validate_mask(skeleton)
    skel = _normalize_mask(skeleton)

    if not skel.any():
        return []

    # 1. Trace connected paths through the skeleton graph
    raw_paths = _trace_skeleton_paths(skel)

    # 2. Partition bends / corners into straight subpaths using RDP
    subpaths: list[np.ndarray] = []
    for raw in raw_paths:
        if len(raw) < 2:
            continue
        # Convert (row, col) coordinates to (x, y) where x=col, y=row
        pts = np.array([(float(c), float(r)) for r, c in raw], dtype=np.float64)
        for sp in _split_path_rdp(pts, tolerance=rdp_tolerance):
            if len(sp) >= min_pixels:
                subpaths.append(sp)

    # 3. Fit geometric lines to each subpath using PCA
    segments: list[WallSegment] = []
    for pts in subpaths:
        seg = _fit_line_pca(
            pts,
            idx=len(segments),
            min_length_px=min_length_px,
            min_pixels=min_pixels,
        )
        if seg is not None:
            segments.append(seg)

    return segments


# ---------------------------------------------------------------------------
# Placeholders – later phases
# ---------------------------------------------------------------------------

def generate_wall_graph(skeleton: np.ndarray):  # noqa: D401
    """Generate a wall graph from a skeleton image.  *(Phase 4 placeholder)*"""
    pass


def polygonize_rooms(wall_graph):  # noqa: D401
    """Polygonize rooms from a wall graph.  *(Phase 5+ placeholder)*"""
    pass
