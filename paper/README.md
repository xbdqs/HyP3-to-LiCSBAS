# Paper figure reproduction

This directory contains compact derived data and standalone plotting scripts used to reproduce the six manuscript figures. The multi-gigabyte source HyP3 raster stack is not redistributed.

## Contents

- `figure_data/` — CSV inputs for each figure
- `figures/` — one standalone Python script per figure
- `outputs/` — preview PNGs included for convenient browsing on GitHub

## Reproduce a figure

From the repository root:

```bash
python -m pip install -e ".[plot]"
python paper/figures/plot_figure_01.py
```

Each plotting script reads only the corresponding CSV files and writes publication-ready outputs. The designs use a consistent colorblind-friendly palette, redundant marker/line encodings, and figure types chosen to match the data structure.

## Figures

1. Software architecture and workflow
2. Semantic HyP3-to-LiCSBAS2 mapping
3. Temporal/perpendicular-baseline network
4. Common-reference harmonization diagnostics
5. Baseline reconstruction and residual diagnostics
6. Validation/readiness summary

The compact figure data support reproducibility of the manuscript graphics; they are not a replacement for the original HyP3 source raster stack.
