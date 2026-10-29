# Changelog

## v1.0.1
- Corrected LOS geometry reprojection: native-grid theta/phi are converted to Cartesian E/N/U before resampling.
- Avoids direct interpolation of periodic phi across the -pi/+pi branch cut.
- Preserves Windows/Linux/WSL behavior and Matplotlib/stdlib plotting fallback.
- Existing unw/cc outputs remain reusable; only ancillary geometry needs refresh for stacks made with v1.0.0.

## 1.0.0
- Finalized complete LiCSAR-like GEOC output.
- Preserves native HyP3 INT40/INT80 posting by default.
- Common-reference harmonization for pair-specific HyP3 phase references.
- Real acquisition-level perpendicular-baseline inversion and residual QC.
- Generates MLI, HGT, E/N/U, metadata, baselines and network PNG.
- Added cross-platform `check_env.py`.
- Matplotlib is optional.
- `--plot-backend auto` uses Matplotlib/Agg when healthy and automatically
  falls back to a Python-stdlib PNG backend on missing/broken Matplotlib.
- Added Windows setup/launchers and Linux/WSL setup/launchers.
- Added end-to-end Linux tests for Matplotlib, stdlib and automatic fallback.
- Real MGX 504-pair production QC accepted.
