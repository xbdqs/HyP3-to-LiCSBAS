# MGX production validation — HyP3-to-LiCSBAS

Assessment basis: final v1.0.1 `_hyp3lics` QC package produced from the real MGX stack on 28 October 2026.

## Result

**Adapter / GEOC production: PASSED**

The converter output is internally consistent and ready to proceed to
LiCSBAS2 Step 02. Downstream LiCSBAS quality control (Steps 11-12) remains
required and is a separate stage.

## Real MGX stack

- interferograms: 504
- acquisitions: 182
- date range: 2019-12-26 to 2025-12-30
- Sentinel-1A, ascending
- relative orbit: 166
- HyP3 input posting: 40 m
- source CRS: EPSG:32610
- output grid: EPSG:4326
- output shape: 7113 × 4457
- output pixels: 31,702,641
- network connected: yes
- triangular loops: 470
- cycle rank: 323

## Final validation

- pair_count: 504
- referenced_pair_count: 504
- coherence dtype: 504 × uint8
- core problems: none
- ancillary missing: none
- ancillary problems: none
- core_ready: true
- full_GEOC_ready: true

## ENU geometry

- median vector norm: 1.0
- maximum absolute norm error: 1.1920928955078125e-07

This is a numerical unit-vector structural check and is not an independent validation of absolute LOS-geometry accuracy.

## Baseline inversion

- pair equations: 504
- acquisitions: 182
- rank: 181 / 181
- RMS residual: 0.0155341981 m
- median absolute residual: 0.0007671181 m
- maximum absolute residual: 0.1514294739 m

The acquisition-level perpendicular-baseline reconstruction is internally
consistent and suitable for the LiCSBAS `baselines` file. The residuals quantify
network internal consistency; they are not an external orbit-accuracy estimate.

## Reference harmonization

- plan reused: yes
- pair offsets: 504 / 504
- common reference longitude: -126.6675820147799
- common reference latitude: 65.33591747519878
- failed reference pairs: 0

## Ancillary source

- baseline / geometry reference acquisition: 2023-01-15
- source pair: 20230115_20230127
- mean height: 238.8014069 m
- mean ellipsoid incidence angle: 38.3876114 degrees

## Ancillary availability in original HyP3 stack

- unw: 504/504
- coherence: 504/504
- amplitude: 504/504
- DEM: 504/504
- look theta: 504/504
- look phi: 504/504
- ellipsoid incidence map: 504/504
- local incidence map: 504/504
- water mask: 504/504

## Spatial-support note

The strict all-pair rectangular intersection retains approximately 72.7% of
the median source-product rectangular footprint. This is intentional for the
current first production stack and is not a validation failure.

## Next step

Run LiCSBAS2 Step 02 on the completed `GEOC` directory, then perform the
standard Step 11/12 interferogram and loop-closure quality control before SBAS
inversion.

## v1.0.1 LOS reprojection

The production rerun used wrap-safe component-first resampling: native-grid
`theta/phi` were converted to Cartesian `E/N/U`, the three components were
bilinearly reprojected, and the resulting vectors were renormalized. The periodic
`phi` angle was therefore never directly interpolated across the `-pi/+pi` branch cut.
