#!/usr/bin/env python3
from pathlib import Path
import tempfile
import sys
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.enums import Resampling

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import hyp3lics

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    transform=from_origin(0.0,1.0,1.0,1.0)
    profile=dict(driver='GTiff',height=1,width=2,count=1,dtype='float32',crs='EPSG:4326',transform=transform,nodata=np.nan)
    theta=np.deg2rad(np.array([[30.0,30.0]],dtype=np.float32))
    phi=np.deg2rad(np.array([[179.0,-179.0]],dtype=np.float32))
    for name,arr in [('theta.tif',theta),('phi.tif',phi)]:
        with rasterio.open(td/name,'w',**profile) as ds: ds.write(arr,1)
    grid=dict(left=0.0,right=2.0,bottom=0.0,top=1.0,xres_deg=2.0,yres_deg=1.0,width=1,height=1,target_spacing_m=1.0)
    E,N,U,good,err=hyp3lics._warp_los_components_from_angles(str(td/'theta.tif'),str(td/'phi.tif'),grid,Resampling.average)
    assert good[0,0]
    # 179 and -179 deg point almost due west. Direct angle averaging would incorrectly point east.
    assert E[0,0] < -0.8, (E,N,U)
    assert abs(N[0,0]) < 0.05, (E,N,U)
    assert U[0,0] > 0.45, (E,N,U)
    assert err is not None and err < 1e-6
print('PASS: look-vector phi branch-cut regression')
