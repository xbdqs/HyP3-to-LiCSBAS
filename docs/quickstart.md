# Quick start

This guide shows the shortest supported workflow. Source HyP3 ZIPs are treated as read-only inputs.

## Windows

Create or activate a compatible environment, then verify Rasterio/GDAL reprojection support:

```bat
SETUP_WINDOWS.bat
conda activate hyp3lics
python check_env.py
```

Run the three main stages:

```bat
python hyp3lics.py preflight -i "D:\HyP3" -o "D:\HyP3_preflight"
python hyp3lics.py plan -i "D:\HyP3" -o "D:\HyP3_plan"
python hyp3lics.py prepare ^
  -i "D:\HyP3" ^
  -o "D:\HyP3_LiCSBAS" ^
  --plan-dir "D:\HyP3_plan" ^
  --extent-mode intersection ^
  --plot-backend auto
```

Interactive `.bat` launchers in the repository provide the same operations.

## Linux / WSL

```bash
bash setup_linux.sh
source .venv/bin/activate
python check_env.py

python hyp3lics.py preflight -i /data/HyP3 -o /data/preflight
python hyp3lics.py plan -i /data/HyP3 -o /data/plan
python hyp3lics.py prepare \
  -i /data/HyP3 \
  -o /data/HyP3_LiCSBAS \
  --plan-dir /data/plan \
  --extent-mode intersection \
  --plot-backend auto
```

## Resume

Do not delete a valid partial output simply because an ancillary or plotting step failed. Without `--overwrite`, existing unwrapped-phase and coherence GeoTIFFs are reused. The converter can therefore resume ancillary generation and validation without repeating the large interferogram reprojection stage.

## Plotting backend

`--plot-backend auto` tries headless Matplotlib first and falls back to the Python standard-library PNG writer if Matplotlib is missing or broken. The plotting backend changes only `network.png`; it does not change the scientific raster products.

## Successful completion

The final `_hyp3lics/validation.json` should contain:

```text
core_ready: true
full_GEOC_ready: true
ancillary_missing: []
ancillary_problems: []
```
