#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin

HERE=Path(__file__).resolve().parents[1]
TMP=HERE/"tests"/"_tmp_v1"
if TMP.exists(): shutil.rmtree(TMP)
INP=TMP/"input"; PLAN=TMP/"plan"; INP.mkdir(parents=True)

dates=["20200101","20200113","20200125","20200206"]
pairs=[(0,1),(1,2),(0,2),(2,3),(1,3),(0,3)]
bperp=[0.0,25.0,-14.0,40.0]
tr=from_origin(500000,7250000,40,40)
h=w=80
Y,X=np.mgrid[0:h,0:w]
fields=[0.02*k*X+0.01*k*Y+0.3*k for k in range(len(dates))]
theta=np.full((h,w),0.9,dtype="float32")
phi=np.full((h,w),2.4,dtype="float32")
inc=np.full((h,w),0.65,dtype="float32")
dem=(200+0.2*X+0.1*Y).astype("float32")
water=np.ones((h,w),dtype="uint8")

for n,(i,j) in enumerate(pairs):
    prefix=f"S1AA_{dates[i]}T010000_{dates[j]}T010000_VVP{(j-i)*12:03d}_INT40_G_TEST_{n:02d}"
    d=TMP/prefix; d.mkdir()
    raw=(fields[j]-fields[i]).astype("float32")
    ry=8+(n*7)%50; rx=9+(n*9)%50
    unw=raw-raw[ry,rx]
    coh=np.full((h,w),0.85,dtype="float32")
    coh[:3,:]=0; coh[-3:,:]=0; coh[:,:3]=0; coh[:,-3:]=0
    unw[coh==0]=np.nan
    amp=(1.0+0.001*X+0.002*Y+0.01*i).astype("float32")

    prof=dict(driver="GTiff",height=h,width=w,count=1,dtype="float32",
              crs="EPSG:32610",transform=tr,compress="DEFLATE")
    for suffix,arr,nodata in [
        ("_unw_phase.tif",unw,np.nan),("_corr.tif",coh,0.0),
        ("_amp.tif",amp,0.0),("_dem.tif",dem,np.nan),
        ("_lv_theta.tif",theta,np.nan),("_lv_phi.tif",phi,np.nan),
        ("_inc_map_ell.tif",inc,np.nan),("_inc_map.tif",inc,np.nan),
    ]:
        with rasterio.open(d/f"{prefix}{suffix}","w",nodata=nodata,**prof) as ds:
            ds.write(arr,1)
    prof8=dict(driver="GTiff",height=h,width=w,count=1,dtype="uint8",
               crs="EPSG:32610",transform=tr,compress="DEFLATE")
    with rasterio.open(d/f"{prefix}_water_mask.tif","w",nodata=0,**prof8) as ds:
        ds.write(water,1)

    ref_orbit=32000+i*175
    sec_orbit=32000+j*175
    meta=(
        f"Reference Granule: S1A_TEST_{dates[i]}T010000\n"
        f"Secondary Granule: S1A_TEST_{dates[j]}T010000\n"
        "Reference Pass Direction: ASCENDING\n"
        f"Reference Orbit Number: {ref_orbit}\n"
        "Secondary Pass Direction: ASCENDING\n"
        f"Secondary Orbit Number: {sec_orbit}\n"
        f"Baseline: {bperp[j]-bperp[i]:.6f}\n"
        "UTCTime: 3600.0\n"
        "Heading: -10.0\n"
        "Spacecraft height: 700000.0\n"
        "Earth radius at nadir: 6370000.0\n"
        "Slant range near: 800000.0\n"
        "Slant range center: 880000.0\n"
        "Slant range far: 960000.0\n"
        "Range looks: 10\n"
        "Azimuth looks: 2\n"
        "Resolution of output (m): 40\n"
        "DEM source: GLO-30\n"
        "DEM resolution: 80\n"
        "Unwrapping type: mcf\n"
        "Phase at Reference Point: 2.0\n"
        "Latitude of the reference point (WGS84): 65.0\n"
        "Longitude of the reference point (WGS84): -123.0\n"
    )
    (d/f"{prefix}.txt").write_text(meta)
    zp=INP/f"{prefix}.zip"
    with zipfile.ZipFile(zp,"w",zipfile.ZIP_DEFLATED) as z:
        for f in d.iterdir():
            z.write(f,f"{prefix}/{f.name}")
    shutil.rmtree(d)

def run(*args):
    print("RUN:",*args)
    subprocess.run([sys.executable,str(HERE/"hyp3lics.py"),*args],check=True)

run("plan","-i",str(INP),"-o",str(PLAN),
    "--ref-radius-px","3","--ref-min-pixels","5","--report-spacings","40","80")

for backend in ("stdlib","matplotlib","auto"):
    out=TMP/f"output_{backend}"
    run("prepare","-i",str(INP),"-o",str(out),
        "--plan-dir",str(PLAN),"--target-spacing-m","40",
        "--ref-radius-px","3","--ref-min-pixels","5",
        "--plot-backend",backend)
    val=json.loads((out/"_hyp3lics"/"validation.json").read_text())
    anc=json.loads((out/"_hyp3lics"/"ancillary_summary.json").read_text())
    assert val["full_GEOC_ready"] is True
    assert val["referenced_pair_count"]==len(pairs)
    assert val["ancillary_missing"]==[]
    assert abs(val["enu_norm_check"]["median_norm"]-1.0)<1e-6
    assert (out/"GEOC"/"metadata.txt").exists()
    assert (out/"GEOC"/"baselines").exists()
    assert (out/"GEOC"/"network.png").exists()
    assert anc["network_plot_backend"] in ("stdlib","matplotlib")
    if backend=="stdlib":
        assert anc["network_plot_backend"]=="stdlib"
    if backend=="matplotlib":
        assert anc["network_plot_backend"]=="matplotlib"

print("END-TO-END CROSS-PLATFORM TEST PASSED")
