# Scientific method

HyP3-to-LiCSBAS is an interoperability adapter. Its role is to translate data organization while preserving the scientific meaning needed by LiCSBAS2.

## 1. Preflight and network audit

The preflight stage inventories input products, acquisitions, pass direction, orbit, nominal posting, source CRS, network connectivity, temporal baselines, loops, leaf acquisitions and footprint overlap. The target grid is explicit and shared by all interferograms.

## 2. Common-reference harmonization

HyP3 interferograms may be independently phase referenced. A common high-coherence reference window is therefore selected for the stack. Each interferogram receives one additive re-referencing shift derived from that common window.

This operation aligns the phase datum across the network. It does not repair unwrapping errors or remove atmospheric signals.

## 3. Common grid

All core rasters are written on one EPSG:4326 grid. The default `intersection` mode retains spatial support common to every input pair. Because the target grid is geographic, the requested metre-scale posting is interpreted approximately near the stack centre rather than as a globally constant metric pixel size.

## 4. Baseline reconstruction

For pair `i -> j`, the observation equation is

```text
b_j - b_i = B_ij
```

where `B_ij` is the HyP3 pairwise perpendicular baseline and `b_i`, `b_j` are acquisition-level values. The overdetermined connected system is solved with one acquisition fixed to zero. Residuals quantify internal consistency of the redundant pair network; they are not an external orbit-accuracy estimate.

## 5. LOS vector reconstruction

HyP3 supplies look-vector elevation `theta` and orientation `phi`. The adapter computes

```text
E = cos(theta) * cos(phi)
N = cos(theta) * sin(phi)
U = sin(theta)
```

on the native source grid, reprojects E/N/U separately, and renormalizes the Cartesian vector. This component-first procedure avoids direct interpolation of periodic `phi` values across the `-pi/+pi` branch cut.

## 6. Ancillary layers and metadata

Amplitude is converted to a LiCSBAS-compatible background MLI analogue and the HyP3 processing DEM is used for the height layer. Metadata fields are written only when directly available or transparently derived. Processor-specific values without a documented HyP3 equivalent are omitted rather than fabricated.

## 7. Validation boundary

The adapter checks file structure, pair completeness, common referencing, raster shape/dtype, ancillary presence, baseline inversion and LOS-vector numerical structure. These checks establish converter readiness. They do not replace LiCSBAS2's downstream interferogram-quality screening, loop-closure assessment or stable-reference selection.
