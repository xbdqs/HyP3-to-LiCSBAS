# Validation and interpretation

## Production stack

The production-scale validation used a Sentinel-1A ascending HyP3 stack on relative orbit 166:

- 504 interferograms
- 182 acquisitions
- 2019-12-26 to 2025-12-30
- one connected network
- 470 triangular loops
- cycle rank 323

All 504 interferograms were assigned the common harmonization reference. The acquisition-level baseline inversion was full rank after fixing one datum (`181/181`).

## Baseline diagnostics

- RMS residual: 0.015534198 m
- median absolute residual: approximately 0.000767 m
- maximum absolute residual: 0.151429474 m

These values describe internal agreement among redundant pairwise baseline observations. They should not be interpreted as absolute orbit accuracy.

## LOS-vector diagnostics

The final E/N/U layers produced:

- median vector norm: 1.0
- maximum absolute unit-norm error: 1.1920928955078125e-07

This is a numerical structural check of the reconstruction and normalization procedure, not an independent external geometry benchmark.

## Final structural status

```text
pair_count = 504
referenced_pair_count = 504
problems = []
ancillary_missing = []
ancillary_problems = []
core_ready = true
full_GEOC_ready = true
```

## Spatial support

For this production stack, strict all-pair intersection retained about 72.7% of the median rectangular source-product footprint. This is a deliberate trade-off: every output pair has identical spatial support, but some edge coverage is discarded.

## Downstream responsibility

`full_GEOC_ready=true` means that the adapter output passed converter-level structural and internal-consistency checks. LiCSBAS2 Step 11/12 quality control, loop closure, masking, inversion and final stable-reference selection remain required for scientific time-series analysis.
