#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys, tempfile
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description="HyP3-to-LiCSBAS environment check")
    ap.add_argument("--require-matplotlib",action="store_true",
                    help="Fail if Matplotlib/Agg is unavailable. Normally not needed because stdlib fallback exists.")
    args=ap.parse_args()

    print("Platform   :", sys.platform)
    print("Python     :", sys.version.replace("\n"," "))
    print("Executable :", sys.executable)
    print("CONDA_PREFIX:", os.environ.get("CONDA_PREFIX"))

    try:
        import numpy as np
        print("NumPy      :", np.__version__)
    except Exception as e:
        print("CORE CHECK: FAIL - NumPy:", repr(e))
        return 1

    try:
        import rasterio
        print("Rasterio   :", rasterio.__version__)
        print("GDAL       :", rasterio.__gdal_version__)
        print("PROJ       :", getattr(rasterio,"__proj_version__","unknown"))
        from rasterio.crs import CRS
        from rasterio.transform import from_origin
        from rasterio.warp import reproject
        from rasterio.enums import Resampling

        src=np.arange(100,dtype="float32").reshape(10,10)
        dst=np.zeros((10,10),dtype="float32")
        tr=from_origin(-125.0,66.0,0.001,0.001)
        reproject(source=src,destination=dst,
                  src_transform=tr,src_crs=CRS.from_epsg(4326),
                  dst_transform=tr,dst_crs=CRS.from_epsg(4326),
                  resampling=Resampling.nearest)
        assert np.isfinite(dst).all()
        print("rasterio.warp.reproject: OK")
    except Exception as e:
        print("CORE CHECK: FAIL - Rasterio/GDAL:", repr(e))
        return 1

    # The fallback backend is required and uses only stdlib + NumPy.
    try:
        import struct, zlib
        payload=zlib.compress(b"HyP3-to-LiCSBAS")
        assert payload and struct.pack(">I",len(payload))
        print("Plot fallback: stdlib zlib/struct OK")
    except Exception as e:
        print("CORE CHECK: FAIL - stdlib PNG fallback:",repr(e))
        return 1

    # Matplotlib is optional. Import failures (including DLL/pyexpat issues)
    # are deliberately non-fatal unless explicitly required.
    mpl_ok=False
    disable_mpl=os.environ.get("HYP3LICS_DISABLE_MATPLOTLIB","").strip().lower() in {"1","true","yes","on"}
    if disable_mpl:
        print("Matplotlib : disabled by HYP3LICS_DISABLE_MATPLOTLIB (NON-FATAL)")
        print("             auto backend will use stdlib PNG.")
    else:
        try:
            import matplotlib
            matplotlib.use("Agg",force=True)
            import matplotlib.pyplot as plt
            with tempfile.TemporaryDirectory() as td:
                fp=Path(td)/"test.png"
                fig,ax=plt.subplots()
                ax.plot([0,1],[0,1])
                fig.savefig(fp)
                plt.close(fig)
                assert fp.exists() and fp.stat().st_size>0
            print("Matplotlib :",matplotlib.__version__,"| Agg PNG: OK")
            mpl_ok=True
        except Exception as e:
            print("Matplotlib : unavailable/broken (NON-FATAL in auto mode)")
            print("             ",repr(e))
            print("             auto backend will use stdlib PNG.")

    if args.require_matplotlib and not mpl_ok:
        print("ENVIRONMENT CHECK: FAIL (--require-matplotlib)")
        return 1
    print("ENVIRONMENT CHECK: PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
