# Validation status

## Real MGX production validation

The final production run used HyP3-to-LiCSBAS 1.0.1 and reported:

- 504 / 504 interferograms present
- 504 / 504 common-referenced
- 504 coherence rasters written as uint8
- baseline inversion rank: 181 / 181
- baseline residual RMS: 0.0155341981 m
- ENU median vector norm: 1.0
- ENU maximum absolute norm error: 1.1920928955078125e-07
- ancillary missing: none
- ancillary problems: none
- `core_ready = true`
- `full_GEOC_ready = true`

Final Windows production environment:

- Python 3.11.15
- NumPy 2.4.6
- Rasterio 1.4.4
- GDAL 3.10.3
- PROJ 9.6.0
- Matplotlib unavailable in that environment; the stdlib PNG fallback was used successfully

## Automated tests

The repository includes three complementary tests:

1. `test_look_vector_branchcut.py` — LOS azimuth branch-cut regression.
2. `test_synthetic_zip_stack.py` — synthetic ZIP discovery, preflight, network and common-reference planning.
3. `test_end_to_end_crossplatform.py` — complete synthetic prepare/ancillary/validation workflow, including stdlib, Matplotlib and automatic plotting backends.

The full end-to-end test reaches `core_ready=true` and `full_GEOC_ready=true`.

GitHub Actions runs the fast core tests on both Windows and Linux and the complete end-to-end scientific workflow on Linux.
