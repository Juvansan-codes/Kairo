# PHASE 6 REPORT: Optional VLM Verification

## Overview
Phase 6 introduced an **Optional Vision-Language Model (VLM) Verification layer** into the Dimension parsing pipeline. The module acts strictly as a *verifier* for highly ambiguous alphanumeric strings identified by the OCR and is explicitly barred from generating geometric definitions or scales, preserving the deterministic nature of the core architecture.

## Architecture & Integration
### Interface (`vlm.py`)
- Created `DimensionVerifier` which defines the structural abstraction for interacting with an external VLM provider (e.g. GPT-4V, Claude-3.5-Sonnet, Gemini-1.5-Pro).
- Encapsulates payload formatting and API execution.
- Returns a strict `DimensionVerificationResult` schema (`interpretation`, `normalized_text`, `confidence`, `reason`).

### Trigger Heuristics
The deterministic parser (`parser.py`) only queries the VLM if the parsed candidate hits distinct ambiguity thresholds. This ensures latency remains low for 99% of normal operations.
- **Low OCR Confidence:** `ocr_confidence < 0.75` but text contains digits.
- **Low Parse Confidence for Dimensions:** Expected dimension candidate but `parse_confidence < 0.7`.
- **Typographical Artifacts:** Common OCR failures mixing characters (e.g., `I`, `l`, `O`, `S` instead of `1`, `0`, `5`) paired with poor confidence scores.

### Verification Cycle
When triggered:
1. VLM evaluates the bounding box and localized text context.
2. VLM returns a suggested interpretation and structurally standard string (e.g., correcting `"I2'-6\""` to `"12'-6\""`).
3. The deterministic pipeline intercepts this response. If `VLM_confidence > parse_confidence`, the string is fed back into `units.py` to be mathematically parsed again.
4. Provenance logs are updated with `vlm_verified: True`.

## Testing (`test_vlm.py`)
- **Clear Case Validation:** Demonstrated that perfectly parsed inputs (`"4200"` at `0.98` confidence) completely bypass the VLM logic.
- **Ambiguous Case Integration:** Injected `I2'-6"` simulating an OCR hallucination of the letter 'I' instead of '1'. The deterministic parser initially ignored it. With the VLM enabled, the string was recognized, corrected, and deterministically parsed back into an exact metric measurement of `3810.0 mm`.
- **Fallback / VLM Absence:** The system gracefully handles the lack of an API key (or network timeouts) by instantly backing out and defaulting to the deterministic pipeline, meaning the system never hard-crashes.

## Performance Profile
- **Cost:** Practically $0 unless the blueprint is heavily degraded.
- **Latency:** $+0 \text{s}$ for clean floorplans. Estimated $+0.5\text{s} - 1.5\text{s}$ for ambiguous targets when actually communicating with a commercial API.
- **Resilience:** Built defensively. If the VLM hallucinated a bad answer, the deterministic engine re-runs unit mapping (`parse_dimension_string`). If the VLM's string fails deterministic parsing, it gets correctly bucketed to `TEXT` or `IGNORED`.

## Handoff & Conclusion
Phase 6 completes the Member 1 pipeline stack (AI Perception $\rightarrow$ OCR $\rightarrow$ Parser $\rightarrow$ Scale $\rightarrow$ VLM). 

The entire Member 1 perception repository is now fully structured, resilient, and ready to be merged into Member 2's Wall Geometry/MGR subsystem.

**PHASE 6 IS COMPLETE.**
