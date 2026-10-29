# Paper figure reproduction

This directory contains the compact derived data, standalone plotting scripts, and preview PNGs for the six figures used in the SoftwareX manuscript. The large HyP3 raster stack is not redistributed.

## Contents
- `figure_data/` — CSV inputs for each figure
- `figures/` — one standalone Python plotting script per figure
- `outputs/` — final preview PNGs
- `Figure_Captions.txt` — captions synchronized with the submission manuscript

## Reproduce a figure
From the repository root:
```bash
python -m pip install -e ".[plot]"
python paper/figures/plot_figure_01.py
```
Each script reads only the corresponding CSV file(s) and writes publication-ready outputs.
