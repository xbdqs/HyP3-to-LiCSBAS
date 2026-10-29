#!/usr/bin/env python3
"""Synthetic integration test for ZIP discovery, preflight and reference planning.

The complete ancillary/prepare workflow is exercised separately by
``test_end_to_end_crossplatform.py``. Keeping this test focused makes it a fast
cross-platform CI check while still exercising real ZIP parsing and reference planning.
"""
import json, shutil, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin

HERE=Path(__file__).resolve().parents[1]
TMP=HERE/'tests'/'_tmp'
if TMP.exists(): shutil.rmtree(TMP)
INP=TMP/'input'; PREFLIGHT=TMP/'preflight'; PLAN=TMP/'plan'; INP.mkdir(parents=True)

dates=['20200101','20200113','20200125','20200206']
pairs=[(0,1),(1,2),(0,2),(2,3),(1,3),(0,3)]
tr=from_origin(500000,7250000,40,40)
h=w=80
Y,X=np.mgrid[0:h,0:w]
fields=[0.02*k*X+0.01*k*Y+0.3*k for k in range(len(dates))]

for n,(i,j) in enumerate(pairs):
    prefix=f'S1AA_{dates[i]}T010000_{dates[j]}T010000_VVP{(j-i)*12:03d}_INT40_G_TEST_{n:02d}'
    d=TMP/prefix; d.mkdir()
    raw=(fields[j]-fields[i]).astype('float32')
    ry=8+(n*7)%50; rx=9+(n*9)%50
    unw=raw-raw[ry,rx]
    coh=np.full((h,w),0.85,dtype='float32')
    coh[:3,:]=0; coh[-3:,:]=0; coh[:,:3]=0; coh[:,-3:]=0
    unw[coh==0]=np.nan
    prof=dict(driver='GTiff',height=h,width=w,count=1,dtype='float32',
              crs='EPSG:32610',transform=tr,compress='DEFLATE')
    with rasterio.open(d/f'{prefix}_unw_phase.tif','w',nodata=np.nan,**prof) as ds:
        ds.write(unw,1)
    with rasterio.open(d/f'{prefix}_corr.tif','w',nodata=0.0,**prof) as ds:
        ds.write(coh,1)
    ref_orbit=32000+i*175
    sec_orbit=32000+j*175
    meta=(
        'Reference Pass Direction: ASCENDING\n'
        f'Reference Orbit Number: {ref_orbit}\n'
        f'Secondary Orbit Number: {sec_orbit}\n'
        'Resolution of output (m): 40\n'
        'DEM source: GLO-30\n'
        'Unwrapping type: mcf\n'
        'Latitude of the reference point (WGS84): 65.0\n'
        'Longitude of the reference point (WGS84): -123.0\n'
    )
    (d/f'{prefix}.txt').write_text(meta)
    zp=INP/f'{prefix}.zip'
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
        for src in d.iterdir(): z.write(src,f'{prefix}/{src.name}')
    shutil.rmtree(d)

def run(*args):
    subprocess.run([sys.executable,str(HERE/'hyp3lics.py'),*args],check=True)

run('preflight','-i',str(INP),'-o',str(PREFLIGHT))
summary=json.loads((PREFLIGHT/'preflight_summary.json').read_text())
assert summary['products']==6
assert summary['acquisitions']==4
assert summary['network_connected'] is True
assert summary['cycle_rank']==3

run('plan','-i',str(INP),'-o',str(PLAN),
    '--ref-radius-px','3','--ref-min-pixels','5','--report-spacings','40','80')
plan=json.loads((PLAN/'reference_plan.json').read_text())
assert plan['failure_count']==0
assert plan['min_valid_pixels']>=5
rows=(PLAN/'reference_offsets.csv').read_text().strip().splitlines()
assert len(rows)==7  # header + six interferograms

shutil.rmtree(TMP)
print('PASS: synthetic ZIP preflight and common-reference planning')
