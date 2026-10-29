#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HyP3-to-LiCSBAS (hyp3lics) v1.0.1.

Conservative adapter from ASF HyP3 GAMMA Sentinel-1 InSAR products to a
LiCSBAS2-ready GEOC stack. Source HyP3 files are never modified.
"""
from __future__ import annotations

import argparse, csv, json, math, os, re, sys, zipfile, struct, zlib
import shutil
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VERSION = "1.0.1"
UNW_SUFFIX = "_unw_phase.tif"
CORR_SUFFIX = "_corr.tif"
AMP_SUFFIX = "_amp.tif"
DEM_SUFFIX = "_dem.tif"
LV_THETA_SUFFIX = "_lv_theta.tif"
LV_PHI_SUFFIX = "_lv_phi.tif"
INC_ELL_SUFFIX = "_inc_map_ell.tif"
INC_LOCAL_SUFFIX = "_inc_map.tif"
WATER_SUFFIX = "_water_mask.tif"
README_SUFFIX = ".README.md.txt"
DATE_PAIR_RE = re.compile(r"(?P<d1>\d{8})T\d{6}[^_]*_(?P<d2>\d{8})T\d{6}")
DATE_PAIR_LOOSE_RE = re.compile(r"(?P<d1>20\d{6}).*?(?P<d2>20\d{6})")

try:
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.windows import Window
    from rasterio.warp import reproject, transform_bounds, transform as rio_transform
except Exception as exc:
    print("ERROR: the Rasterio binary stack could not be imported.\n"
          "On Windows, use the bundled SETUP_WINDOWS_ENV.bat to create a clean\n"
          "pip-wheel environment (Python 3.11 + NumPy 1.26.4 + Rasterio 1.4.4).\n"
          "Do not mix the PyPI Rasterio wheel with conda-forge GDAL/Rasterio in\n"
          "the same environment.\n"
          f"Import error: {exc}", file=sys.stderr)
    raise


def log(msg: str = "") -> None:
    print(msg, flush=True)


def parse_dates(name: str) -> Tuple[Optional[str], Optional[str]]:
    b = Path(name).name
    m = DATE_PAIR_RE.search(b) or DATE_PAIR_LOOSE_RE.search(b)
    if not m:
        return None, None
    d1, d2 = m.group("d1"), m.group("d2")
    try:
        datetime.strptime(d1, "%Y%m%d"); datetime.strptime(d2, "%Y%m%d")
    except ValueError:
        return None, None
    return d1, d2


def product_prefix_from_name(name: str) -> Optional[str]:
    b = Path(name).name
    for suf in (UNW_SUFFIX, CORR_SUFFIX, AMP_SUFFIX, DEM_SUFFIX,
                LV_THETA_SUFFIX, LV_PHI_SUFFIX, INC_ELL_SUFFIX,
                INC_LOCAL_SUFFIX, WATER_SUFFIX, README_SUFFIX):
        if b.endswith(suf):
            return b[:-len(suf)]
    if b.endswith(".txt") and not b.endswith(".tif.xml"):
        return b[:-4]
    return None


def parse_metadata_text(text: str) -> Dict[str, str]:
    out = {}
    for raw in text.splitlines():
        line = raw.strip().lstrip("\ufeff")
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
        elif "=" in line:
            k, v = line.split("=", 1)
        else:
            continue
        out[k.strip()] = v.strip()
    return out


def meta_get(meta: Dict[str, str], *names: str) -> Optional[str]:
    norm = {re.sub(r"\s+", " ", k.strip().lower()): v for k, v in meta.items()}
    for n in names:
        v = norm.get(re.sub(r"\s+", " ", n.strip().lower()))
        if v is not None:
            return v
    return None


def safe_float(v):
    try: return float(str(v).strip())
    except Exception: return None


def safe_int(v):
    try: return int(float(str(v).strip()))
    except Exception: return None


def sensor_from_prefix(prefix: str) -> Optional[str]:
    m = re.match(r"(S1[ABC])", prefix.upper())
    return m.group(1) if m else None


def relative_orbit(abs_orbit: Optional[int], sensor: Optional[str]) -> Optional[int]:
    if abs_orbit is None or sensor is None:
        return None
    if sensor == "S1A": return ((int(abs_orbit) - 73) % 175) + 1
    if sensor == "S1B": return ((int(abs_orbit) - 27) % 175) + 1
    return None


def decode_bytes(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try: return data.decode(enc)
        except UnicodeDecodeError: pass
    return data.decode("utf-8", errors="replace")


@dataclass
class Product:
    source_type: str
    container: str
    prefix: str
    date1: Optional[str]
    date2: Optional[str]
    unw: Optional[str]
    corr: Optional[str]
    meta: Optional[str]
    readme: Optional[str]
    amp: Optional[str] = None
    dem: Optional[str] = None
    lv_theta: Optional[str] = None
    lv_phi: Optional[str] = None
    inc_map_ell: Optional[str] = None
    inc_map: Optional[str] = None
    water_mask: Optional[str] = None
    baseline_m: Optional[float] = None
    utc_time_s: Optional[float] = None
    heading_deg: Optional[float] = None
    spacecraft_height_m: Optional[float] = None
    earth_radius_m: Optional[float] = None
    slant_range_near_m: Optional[float] = None
    slant_range_center_m: Optional[float] = None
    slant_range_far_m: Optional[float] = None
    range_looks: Optional[int] = None
    azimuth_looks: Optional[int] = None
    dem_resolution_m: Optional[float] = None
    reference_granule: Optional[str] = None
    secondary_granule: Optional[str] = None
    sensor: Optional[str] = None
    pass_direction: Optional[str] = None
    reference_orbit: Optional[int] = None
    secondary_orbit: Optional[int] = None
    relative_orbit_ref: Optional[int] = None
    relative_orbit_sec: Optional[int] = None
    output_resolution_m: Optional[float] = None
    dem_source: Optional[str] = None
    unwrapping_type: Optional[str] = None
    hyp3_ref_lat: Optional[float] = None
    hyp3_ref_lon: Optional[float] = None
    hyp3_ref_phase_original: Optional[float] = None
    unw_crs: Optional[str] = None
    unw_epsg: Optional[int] = None
    unw_width: Optional[int] = None
    unw_height: Optional[int] = None
    unw_res_x: Optional[float] = None
    unw_res_y: Optional[float] = None
    unw_left: Optional[float] = None
    unw_bottom: Optional[float] = None
    unw_right: Optional[float] = None
    unw_top: Optional[float] = None
    wgs84_left: Optional[float] = None
    wgs84_bottom: Optional[float] = None
    wgs84_right: Optional[float] = None
    wgs84_top: Optional[float] = None

    @property
    def pair_id(self) -> Optional[str]:
        return f"{self.date1}_{self.date2}" if self.date1 and self.date2 else None

    def src_uri(self, kind: str) -> str:
        mapping = {
            "unw": self.unw, "corr": self.corr, "amp": self.amp,
            "dem": self.dem, "lv_theta": self.lv_theta, "lv_phi": self.lv_phi,
            "inc_map_ell": self.inc_map_ell, "inc_map": self.inc_map,
            "water_mask": self.water_mask,
        }
        member = mapping.get(kind)
        if not member:
            raise ValueError(f"Missing {kind} for {self.prefix}")
        if self.source_type == "zip":
            zp = str(Path(self.container).resolve()).replace("\\", "/")
            mem = member.replace("\\", "/")
            return f"zip://{zp}!{mem}"
        return str(Path(member).resolve())


def apply_meta(p: Product, meta: Dict[str, str]) -> None:
    p.sensor = p.sensor or sensor_from_prefix(p.prefix)
    p.pass_direction = meta_get(meta, "Reference Pass Direction", "Pass Direction")
    p.reference_orbit = safe_int(meta_get(meta, "Reference Orbit Number"))
    p.secondary_orbit = safe_int(meta_get(meta, "Secondary Orbit Number"))
    p.relative_orbit_ref = relative_orbit(p.reference_orbit, p.sensor)
    p.relative_orbit_sec = relative_orbit(p.secondary_orbit, p.sensor)
    p.output_resolution_m = safe_float(meta_get(meta, "Resolution of output (m)"))
    p.dem_source = meta_get(meta, "DEM source")
    p.unwrapping_type = meta_get(meta, "Unwrapping type")
    p.hyp3_ref_lat = safe_float(meta_get(meta, "Latitude of the reference point (WGS84)"))
    p.hyp3_ref_lon = safe_float(meta_get(meta, "Longitude of the reference point (WGS84)"))
    p.hyp3_ref_phase_original = safe_float(meta_get(meta, "Phase at Reference Point"))
    p.reference_granule = meta_get(meta, "Reference Granule")
    p.secondary_granule = meta_get(meta, "Secondary Granule")
    p.baseline_m = safe_float(meta_get(meta, "Baseline"))
    p.utc_time_s = safe_float(meta_get(meta, "UTCTime", "UTC time"))
    p.heading_deg = safe_float(meta_get(meta, "Heading"))
    p.spacecraft_height_m = safe_float(meta_get(meta, "Spacecraft height"))
    p.earth_radius_m = safe_float(meta_get(meta, "Earth radius at nadir"))
    p.slant_range_near_m = safe_float(meta_get(meta, "Slant range near"))
    p.slant_range_center_m = safe_float(meta_get(meta, "Slant range center"))
    p.slant_range_far_m = safe_float(meta_get(meta, "Slant range far"))
    p.range_looks = safe_int(meta_get(meta, "Range looks"))
    p.azimuth_looks = safe_int(meta_get(meta, "Azimuth looks"))
    p.dem_resolution_m = safe_float(meta_get(meta, "DEM resolution"))


def scan_products(root: Path) -> List[Product]:
    products: List[Product] = []
    extracted = defaultdict(dict)
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() == ".zip":
            continue
        prefix = product_prefix_from_name(path.name)
        if prefix is None: continue
        key = (str(path.parent.resolve()), prefix)
        if path.name.endswith(UNW_SUFFIX): extracted[key]["unw"] = str(path.resolve())
        elif path.name.endswith(CORR_SUFFIX): extracted[key]["corr"] = str(path.resolve())
        elif path.name.endswith(AMP_SUFFIX): extracted[key]["amp"] = str(path.resolve())
        elif path.name.endswith(DEM_SUFFIX): extracted[key]["dem"] = str(path.resolve())
        elif path.name.endswith(LV_THETA_SUFFIX): extracted[key]["lv_theta"] = str(path.resolve())
        elif path.name.endswith(LV_PHI_SUFFIX): extracted[key]["lv_phi"] = str(path.resolve())
        elif path.name.endswith(INC_ELL_SUFFIX): extracted[key]["inc_map_ell"] = str(path.resolve())
        elif path.name.endswith(INC_LOCAL_SUFFIX): extracted[key]["inc_map"] = str(path.resolve())
        elif path.name.endswith(WATER_SUFFIX): extracted[key]["water_mask"] = str(path.resolve())
        elif path.name.endswith(README_SUFFIX): extracted[key]["readme"] = str(path.resolve())
        elif path.name == prefix + ".txt": extracted[key]["meta"] = str(path.resolve())
    for (parent, prefix), g in sorted(extracted.items()):
        if "unw" not in g and "corr" not in g: continue
        d1, d2 = parse_dates(prefix)
        p = Product("directory", parent, prefix, d1, d2, g.get("unw"), g.get("corr"), g.get("meta"), g.get("readme"),
                    amp=g.get("amp"), dem=g.get("dem"), lv_theta=g.get("lv_theta"), lv_phi=g.get("lv_phi"),
                    inc_map_ell=g.get("inc_map_ell"), inc_map=g.get("inc_map"), water_mask=g.get("water_mask"),
                    sensor=sensor_from_prefix(prefix))
        if p.meta:
            try: apply_meta(p, parse_metadata_text(decode_bytes(Path(p.meta).read_bytes())))
            except Exception: pass
        products.append(p)

    for zp in sorted(root.rglob("*.zip")):
        try:
            with zipfile.ZipFile(zp) as zf:
                groups = defaultdict(dict)
                for member in zf.namelist():
                    if member.endswith("/"): continue
                    name = Path(member.replace("\\", "/")).name
                    prefix = product_prefix_from_name(name)
                    if prefix is None: continue
                    key = (str(Path(member.replace("\\", "/")).parent), prefix)
                    if name.endswith(UNW_SUFFIX): groups[key]["unw"] = member
                    elif name.endswith(CORR_SUFFIX): groups[key]["corr"] = member
                    elif name.endswith(AMP_SUFFIX): groups[key]["amp"] = member
                    elif name.endswith(DEM_SUFFIX): groups[key]["dem"] = member
                    elif name.endswith(LV_THETA_SUFFIX): groups[key]["lv_theta"] = member
                    elif name.endswith(LV_PHI_SUFFIX): groups[key]["lv_phi"] = member
                    elif name.endswith(INC_ELL_SUFFIX): groups[key]["inc_map_ell"] = member
                    elif name.endswith(INC_LOCAL_SUFFIX): groups[key]["inc_map"] = member
                    elif name.endswith(WATER_SUFFIX): groups[key]["water_mask"] = member
                    elif name.endswith(README_SUFFIX): groups[key]["readme"] = member
                    elif name == prefix + ".txt": groups[key]["meta"] = member
                for (_, prefix), g in sorted(groups.items()):
                    if "unw" not in g and "corr" not in g: continue
                    d1, d2 = parse_dates(prefix)
                    p = Product("zip", str(zp.resolve()), prefix, d1, d2, g.get("unw"), g.get("corr"), g.get("meta"), g.get("readme"),
                                amp=g.get("amp"), dem=g.get("dem"), lv_theta=g.get("lv_theta"), lv_phi=g.get("lv_phi"),
                                inc_map_ell=g.get("inc_map_ell"), inc_map=g.get("inc_map"), water_mask=g.get("water_mask"),
                                sensor=sensor_from_prefix(prefix))
                    if p.meta:
                        try: apply_meta(p, parse_metadata_text(decode_bytes(zf.read(p.meta))))
                        except Exception: pass
                    products.append(p)
        except zipfile.BadZipFile:
            log(f"WARN: bad ZIP skipped: {zp}")

    rank = {"directory": 0, "zip": 1}
    best = {}
    for p in products:
        if p.prefix not in best or rank[p.source_type] < rank[best[p.prefix].source_type]:
            best[p.prefix] = p
    out = list(best.values())
    out.sort(key=lambda p: (p.date1 or "99999999", p.date2 or "99999999", p.prefix))
    return out


def inspect_product_raster(p: Product) -> List[str]:
    issues = []
    if not p.unw: return ["missing unwrapped phase"]
    if not p.corr: return ["missing coherence"]
    try:
        with rasterio.open(p.src_uri("unw")) as u, rasterio.open(p.src_uri("corr")) as c:
            if u.crs is None: issues.append("unwrapped raster has no CRS")
            if c.crs is None: issues.append("coherence raster has no CRS")
            if u.width != c.width or u.height != c.height: issues.append("unw/corr shape mismatch")
            if u.crs != c.crs: issues.append("unw/corr CRS mismatch")
            if not u.transform.almost_equals(c.transform): issues.append("unw/corr geotransform mismatch")
            p.unw_crs = u.crs.to_string() if u.crs else None
            p.unw_epsg = u.crs.to_epsg() if u.crs else None
            p.unw_width, p.unw_height = u.width, u.height
            p.unw_res_x, p.unw_res_y = abs(u.transform.a), abs(u.transform.e)
            p.unw_left, p.unw_bottom, p.unw_right, p.unw_top = u.bounds.left, u.bounds.bottom, u.bounds.right, u.bounds.top
            if u.crs:
                b = transform_bounds(u.crs, "EPSG:4326", *u.bounds, densify_pts=21)
                p.wgs84_left, p.wgs84_bottom, p.wgs84_right, p.wgs84_top = map(float, b)
    except Exception as exc:
        issues.append(f"cannot open raster: {exc}")
    return issues


def connected_components(products: List[Product]) -> List[List[str]]:
    adj = defaultdict(set)
    for p in products:
        if p.pair_id:
            adj[p.date1].add(p.date2); adj[p.date2].add(p.date1)
    seen, comps = set(), []
    for n in sorted(adj):
        if n in seen: continue
        q = deque([n]); seen.add(n); comp = []
        while q:
            x = q.popleft(); comp.append(x)
            for y in adj[x]:
                if y not in seen: seen.add(y); q.append(y)
        comps.append(sorted(comp))
    comps.sort(key=lambda x: -len(x))
    return comps


def count_triangles(products: List[Product]) -> int:
    adj = defaultdict(set)
    for p in products:
        if p.pair_id:
            a, b = p.date1, p.date2; adj[a].add(b); adj[b].add(a)
    n = 0
    for a in sorted(adj):
        for b in adj[a]:
            if b <= a: continue
            n += sum(1 for c in adj[a].intersection(adj[b]) if c > b)
    return n


def write_csv(path: Path, rows: List[Dict], fields: Optional[List[str]] = None) -> None:
    if fields is None:
        fields, seen = [], set()
        for r in rows:
            for k in r:
                if k not in seen: seen.add(k); fields.append(k)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def preflight(root: Path, out: Path) -> Tuple[List[Product], Dict]:
    out.mkdir(parents=True, exist_ok=True)
    log(f"Scanning HyP3 products in: {root}")
    products = scan_products(root)
    if not products:
        raise RuntimeError("No HyP3 GAMMA InSAR products found.")
    issues = []
    for i, p in enumerate(products, 1):
        if i == 1 or i % 25 == 0 or i == len(products): log(f"  Raster metadata {i}/{len(products)}")
        if not p.date1 or not p.date2: issues.append({"severity":"ERROR","pair":p.prefix,"code":"DATE_PARSE","message":"Could not parse date pair"})
        elif p.date1 >= p.date2: issues.append({"severity":"ERROR","pair":p.pair_id,"code":"DATE_ORDER","message":"Date order is not old->new"})
        if not p.unw: issues.append({"severity":"ERROR","pair":p.pair_id or p.prefix,"code":"MISSING_UNW","message":"Missing *_unw_phase.tif"})
        if not p.corr: issues.append({"severity":"ERROR","pair":p.pair_id or p.prefix,"code":"MISSING_CORR","message":"Missing *_corr.tif"})
        if p.unw and p.corr:
            for msg in inspect_product_raster(p):
                issues.append({"severity":"ERROR","pair":p.pair_id or p.prefix,"code":"RASTER","message":msg})

    dirs = sorted({str(p.pass_direction).upper() for p in products if p.pass_direction})
    rels = sorted({p.relative_orbit_ref for p in products if p.relative_orbit_ref is not None} | {p.relative_orbit_sec for p in products if p.relative_orbit_sec is not None})
    resolutions = sorted({round(p.output_resolution_m, 6) for p in products if p.output_resolution_m is not None})
    sensors = sorted({p.sensor for p in products if p.sensor})
    epsgs = sorted({p.unw_epsg for p in products if p.unw_epsg is not None})
    if len(dirs) > 1: issues.append({"severity":"ERROR","pair":"STACK","code":"MIXED_PASS","message":str(dirs)})
    if len(rels) > 1: issues.append({"severity":"ERROR","pair":"STACK","code":"MIXED_RELATIVE_ORBIT","message":str(rels)})
    if len(resolutions) > 1: issues.append({"severity":"ERROR","pair":"STACK","code":"MIXED_RESOLUTION","message":str(resolutions)})
    if len(sensors) > 1: issues.append({"severity":"WARN","pair":"STACK","code":"MIXED_SENSOR","message":str(sensors)})

    comps = connected_components(products)
    triangles = count_triangles(products)
    dates = sorted({d for p in products for d in (p.date1, p.date2) if d})
    degrees, tbas = Counter(), Counter()
    for p in products:
        if p.date1 and p.date2:
            degrees[p.date1] += 1; degrees[p.date2] += 1
            tbas[(datetime.strptime(p.date2, "%Y%m%d") - datetime.strptime(p.date1, "%Y%m%d")).days] += 1

    grid = None
    valid_bounds = [(p.wgs84_left,p.wgs84_bottom,p.wgs84_right,p.wgs84_top) for p in products if p.wgs84_left is not None]
    if valid_bounds:
        left = max(b[0] for b in valid_bounds); bottom = max(b[1] for b in valid_bounds)
        right = min(b[2] for b in valid_bounds); top = min(b[3] for b in valid_bounds)
        if right <= left or top <= bottom:
            issues.append({"severity":"ERROR","pair":"STACK","code":"NO_COMMON_FOOTPRINT","message":f"Intersection invalid: {left},{bottom},{right},{top}"})
        else:
            vals = [p.output_resolution_m for p in products if p.output_resolution_m is not None]
            target_m = float(np.median(vals)) if vals else 40.0
            center_lat = (bottom + top) / 2
            yres = target_m / 111320.0
            xres = target_m / (111320.0 * max(math.cos(math.radians(center_lat)), 0.01))
            snap_left = -180 + math.ceil((left+180)/xres - 1e-12) * xres
            snap_right = -180 + math.floor((right+180)/xres + 1e-12) * xres
            snap_bottom = -90 + math.ceil((bottom+90)/yres - 1e-12) * yres
            snap_top = -90 + math.floor((top+90)/yres + 1e-12) * yres
            width = int(math.floor((snap_right-snap_left)/xres + 1e-9))
            height = int(math.floor((snap_top-snap_bottom)/yres + 1e-9))
            if width <= 0 or height <= 0:
                issues.append({"severity":"ERROR","pair":"STACK","code":"EMPTY_MASTER_GRID","message":"Snapped common grid is empty"})
            else:
                grid = {"crs":"EPSG:4326","left":snap_left,"bottom":snap_bottom,"right":snap_left+width*xres,"top":snap_top,
                        "xres_deg":xres,"yres_deg":yres,"width":width,"height":height,"target_resolution_m":target_m,
                        "center_lat":center_lat,"extent_mode":"intersection"}

    summary = {
        "tool":"HyP3-to-LiCSBAS","version":VERSION,"input":str(root),"products":len(products),"acquisitions":len(dates),
        "date_start":dates[0] if dates else None,"date_end":dates[-1] if dates else None,
        "pass_directions":dirs,"sensors":sensors,"relative_orbits":rels,"output_resolutions_m":resolutions,"source_epsg_codes":epsgs,
        "network_components":len(comps),"network_connected":len(comps)==1,"triangular_loops":triangles,
        "cycle_rank":len(products)-len(dates)+len(comps) if dates else 0,
        "temporal_baseline_days":dict(sorted(tbas.items())),"min_degree":min(degrees.values()) if degrees else 0,
        "leaf_dates":[d for d,v in degrees.items() if v==1],"issues":dict(Counter(i["severity"] for i in issues)),"master_grid_proposal":grid,
    }
    write_csv(out/"preflight_inventory.csv", [{**asdict(p),"pair_id":p.pair_id} for p in products])
    write_csv(out/"preflight_issues.csv", issues, ["severity","pair","code","message"])
    (out/"preflight_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    log(json.dumps(summary, indent=2, ensure_ascii=False))
    return products, summary



def resampling_from_name(name: str):
    table = {
        "nearest": Resampling.nearest,
        "bilinear": Resampling.bilinear,
        "cubic": Resampling.cubic,
        "average": Resampling.average,
    }
    return table[name]


def footprint_diagnosis(products: List[Product]) -> Dict:
    valid = [p for p in products if None not in (p.unw_left,p.unw_bottom,p.unw_right,p.unw_top)]
    if not valid:
        return {}
    crss = sorted({p.unw_epsg for p in valid if p.unw_epsg is not None})
    left_i=max(p.unw_left for p in valid); right_i=min(p.unw_right for p in valid)
    bottom_i=max(p.unw_bottom for p in valid); top_i=min(p.unw_top for p in valid)
    left_u=min(p.unw_left for p in valid); right_u=max(p.unw_right for p in valid)
    bottom_u=min(p.unw_bottom for p in valid); top_u=max(p.unw_top for p in valid)
    areas=np.array([(p.unw_right-p.unw_left)*(p.unw_top-p.unw_bottom) for p in valid],dtype=np.float64)
    inter=max(0.0,right_i-left_i)*max(0.0,top_i-bottom_i)
    median=float(np.median(areas))
    rows=[]
    for p,a in zip(valid,areas):
        ratio=float(a/median) if median>0 else np.nan
        if ratio < 0.95:
            rows.append({"pair_id":p.pair_id,"width":p.unw_width,"height":p.unw_height,
                         "area_km2":float(a/1e6),"area_ratio_to_median":ratio,
                         "left":p.unw_left,"right":p.unw_right,"bottom":p.unw_bottom,"top":p.unw_top})
    def limiting(col, val):
        out=[]
        for p in valid:
            if abs(getattr(p,col)-val) < 1e-6:
                out.append(p.pair_id)
        return out
    return {
        "source_epsg_codes":crss,
        "median_product_area_km2":median/1e6,
        "min_product_area_km2":float(areas.min()/1e6),
        "max_product_area_km2":float(areas.max()/1e6),
        "intersection_bbox_source_crs":{
            "left":left_i,"right":right_i,"bottom":bottom_i,"top":top_i,
            "width_m":right_i-left_i,"height_m":top_i-bottom_i,
            "area_km2":inter/1e6,
        },
        "union_bbox_source_crs":{
            "left":left_u,"right":right_u,"bottom":bottom_u,"top":top_u,
            "width_m":right_u-left_u,"height_m":top_u-bottom_u,
            "area_km2":(right_u-left_u)*(top_u-bottom_u)/1e6,
        },
        "intersection_area_fraction_of_median":float(inter/median) if median>0 else None,
        "footprint_outlier_count_lt95pct_median":len(rows),
        "limiting_pairs":{
            "left_max":limiting("unw_left",left_i),
            "right_min":limiting("unw_right",right_i),
            "bottom_max":limiting("unw_bottom",bottom_i),
            "top_min":limiting("unw_top",top_i),
        },
        "outlier_rows":rows,
    }


def _snap_grid(left,bottom,right,top,xres,yres,mode):
    if mode == "intersection":
        sl=-180+math.ceil((left+180)/xres-1e-12)*xres
        sr=-180+math.floor((right+180)/xres+1e-12)*xres
        sb=-90+math.ceil((bottom+90)/yres-1e-12)*yres
        st=-90+math.floor((top+90)/yres+1e-12)*yres
    else:
        sl=-180+math.floor((left+180)/xres+1e-12)*xres
        sr=-180+math.ceil((right+180)/xres-1e-12)*xres
        sb=-90+math.floor((bottom+90)/yres+1e-12)*yres
        st=-90+math.ceil((top+90)/yres-1e-12)*yres
    width=int(round((sr-sl)/xres)); height=int(round((st-sb)/yres))
    if width<=0 or height<=0:
        raise RuntimeError("Requested grid is empty.")
    return sl,sb,sl+width*xres,st,width,height


def create_master_grid_v3(products: List[Product], extent_mode: str, target_spacing_m: float,
                          bbox: Optional[List[float]]=None) -> Dict:
    bounds=[(p.wgs84_left,p.wgs84_bottom,p.wgs84_right,p.wgs84_top)
            for p in products if p.wgs84_left is not None]
    if not bounds:
        raise RuntimeError("No WGS84 bounds available.")
    if extent_mode=="intersection":
        left=max(b[0] for b in bounds); bottom=max(b[1] for b in bounds)
        right=min(b[2] for b in bounds); top=min(b[3] for b in bounds)
    elif extent_mode=="union":
        left=min(b[0] for b in bounds); bottom=min(b[1] for b in bounds)
        right=max(b[2] for b in bounds); top=max(b[3] for b in bounds)
    elif extent_mode=="bbox":
        if not bbox or len(bbox)!=4:
            raise RuntimeError("--bbox WEST SOUTH EAST NORTH is required with --extent-mode bbox")
        left,bottom,right,top=map(float,bbox)
    else:
        raise RuntimeError(f"Unknown extent mode: {extent_mode}")
    if right<=left or top<=bottom:
        raise RuntimeError("Invalid output extent.")
    center_lat=(bottom+top)/2
    yres=target_spacing_m/111320.0
    xres=target_spacing_m/(111320.0*max(math.cos(math.radians(center_lat)),0.01))
    snap_mode="intersection" if extent_mode=="intersection" else "outward"
    sl,sb,sr,st,width,height=_snap_grid(left,bottom,right,top,xres,yres,snap_mode)
    pix=width*height
    return {
        "crs":"EPSG:4326","left":sl,"bottom":sb,"right":sr,"top":st,
        "xres_deg":xres,"yres_deg":yres,"width":width,"height":height,
        "target_spacing_m":target_spacing_m,"center_lat":center_lat,
        "extent_mode":extent_mode,"pixel_count":pix,
        "estimated_GEOC_uncompressed_GB_float32_unw_uint8_cc":pix*5/1e9*len(products),
        "estimated_LiCSBAS_cum_float32_GB":pix*4/1e9*len(sorted({d for p in products for d in (p.date1,p.date2)})),
    }


def source_common_bbox(products: List[Product]) -> Tuple[float,float,float,float,str,float]:
    epsgs=sorted({p.unw_epsg for p in products if p.unw_epsg is not None})
    if len(epsgs)!=1:
        raise RuntimeError(f"Reference planning currently requires one source EPSG; got {epsgs}")
    left=max(p.unw_left for p in products); right=min(p.unw_right for p in products)
    bottom=max(p.unw_bottom for p in products); top=min(p.unw_top for p in products)
    if right<=left or top<=bottom:
        raise RuntimeError("No common source-CRS bounding box.")
    spacings=[p.unw_res_x for p in products if p.unw_res_x]
    spacing=float(np.median(spacings))
    return left,bottom,right,top,f"EPSG:{epsgs[0]}",spacing


def coarse_reference_candidates_source(products: List[Product], factor:int=8, topk:int=30):
    left,bottom,right,top,crs,spacing=source_common_bbox(products)
    coarse=spacing*factor
    width=max(1,int(math.floor((right-left)/coarse)))
    height=max(1,int(math.floor((top-bottom)/coarse)))
    transform=from_origin(left,top,coarse,coarse)
    s=np.zeros((height,width),dtype=np.float64)
    n=np.zeros((height,width),dtype=np.uint16)
    for i,p in enumerate(products,1):
        if i==1 or i%25==0 or i==len(products):
            log(f"  Source coherence planning {i}/{len(products)}")
        dst=np.zeros((height,width),dtype=np.float32)
        with rasterio.open(p.src_uri("corr")) as src:
            reproject(source=rasterio.band(src,1),destination=dst,
                      src_transform=src.transform,src_crs=src.crs,
                      src_nodata=src.nodata,dst_transform=transform,dst_crs=crs,
                      dst_nodata=0.0,resampling=Resampling.average,
                      init_dest_nodata=True,num_threads=2)
        valid=np.isfinite(dst)&(dst>0)
        s[valid]+=dst[valid]; n[valid]+=1
    mean=np.zeros_like(s); m=n>0; mean[m]=s[m]/n[m]
    vf=n.astype(np.float32)/len(products)
    # Prefer coherent pixels observed in every pair; fall back smoothly if necessary.
    score=mean*(vf**4)
    if height>2 and width>2:
        score[[0,-1],:]=-1; score[:,[0,-1]]=-1
    candidates=[]
    flat=np.argsort(score.ravel())[::-1]
    for idx in flat:
        y,x=np.unravel_index(idx,score.shape)
        if score[y,x]<0: continue
        px=left+(x+0.5)*coarse
        py=top-(y+0.5)*coarse
        candidates.append({"score":float(score[y,x]),"x":float(px),"y":float(py),
                           "mean_coherence":float(mean[y,x]),"valid_fraction":float(vf[y,x])})
        if len(candidates)>=topk: break
    return candidates, {"crs":crs,"left":left,"bottom":bottom,"right":right,"top":top,
                        "coarse_spacing_m":coarse,"width":width,"height":height}


def evaluate_source_reference(products: List[Product], x:float, y:float, radius_px:int,
                              coh_min:float, min_pixels:int, collect_offsets:bool=True) -> Dict:
    failures=[]; offsets=[]; min_valid=10**9; pair_medcoh=[]
    for p in products:
        with rasterio.open(p.src_uri("unw")) as u, rasterio.open(p.src_uri("corr")) as c:
            row,col=u.index(x,y)
            r=radius_px
            y1=max(0,row-r); y2=min(u.height,row+r+1)
            x1=max(0,col-r); x2=min(u.width,col+r+1)
            if y2<=y1 or x2<=x1:
                failures.append(p.pair_id); continue
            win=Window(x1,y1,x2-x1,y2-y1)
            a=u.read(1,window=win).astype(np.float32)
            q=c.read(1,window=win).astype(np.float32)
        valid=np.isfinite(a)&np.isfinite(q)&(q>=coh_min)
        if u.nodata is not None:
            valid &= (a != u.nodata)
        nv=int(valid.sum()); min_valid=min(min_valid,nv)
        if nv < min_pixels:
            failures.append(p.pair_id)
            continue
        off=float(np.median(a[valid]))
        medq=float(np.median(q[valid]))
        mad=float(np.median(np.abs(a[valid]-off)))
        pair_medcoh.append(medq)
        if collect_offsets:
            offsets.append({"pair_id":p.pair_id,"offset_rad":off,"n_ref_pixels":nv,
                            "ref_median_coherence":medq,"phase_mad_rad":mad})
    return {
        "x":float(x),"y":float(y),"failure_count":len(failures),"failures":failures,
        "min_valid_pixels":int(min_valid if min_valid<10**9 else 0),
        "median_of_pair_median_coherence":float(np.median(pair_medcoh)) if pair_medcoh else 0.0,
        "offsets":offsets,
    }


def make_reference_plan(products: List[Product], outdir: Path, ref_x: Optional[float]=None,
                        ref_y: Optional[float]=None, radius_px:int=4, coh_min:float=0.20,
                        min_pixels:int=9, scan_factor:int=8) -> Dict:
    outdir.mkdir(parents=True,exist_ok=True)
    left,bottom,right,top,src_crs,spacing=source_common_bbox(products)
    if (ref_x is None) ^ (ref_y is None):
        raise RuntimeError("Specify both --ref-x and --ref-y, or neither.")
    if ref_x is not None:
        candidates=[{"score":None,"x":float(ref_x),"y":float(ref_y),
                     "mean_coherence":None,"valid_fraction":None}]
        coarse_meta=None
        mode="user"
    else:
        candidates,coarse_meta=coarse_reference_candidates_source(products,scan_factor,30)
        mode="auto"
    best=None
    for rank,cand in enumerate(candidates,1):
        log(f"  Test reference candidate {rank}: x={cand['x']:.1f}, y={cand['y']:.1f}, "
            f"score={cand['score'] if cand['score'] is not None else 'user'}")
        ev=evaluate_source_reference(products,cand["x"],cand["y"],radius_px,coh_min,min_pixels,True)
        ev.update({"candidate_rank":rank,"candidate_score":cand["score"],
                   "candidate_mean_coherence":cand["mean_coherence"],
                   "candidate_valid_fraction":cand["valid_fraction"]})
        key=(ev["failure_count"],-ev["min_valid_pixels"],-ev["median_of_pair_median_coherence"])
        if best is None or key<best[0]: best=(key,ev)
        if ev["failure_count"]==0: break
    if best is None or best[1]["failure_count"]>0:
        ev=best[1] if best else {}
        raise RuntimeError(
            f"Could not find a common source-grid reference window valid for every interferogram. "
            f"Best candidate failed {ev.get('failure_count','?')} pairs. "
            "Increase --ref-radius-px / lower --ref-coh-min, or provide a user reference."
        )
    ev=best[1]
    lon,lat=rio_transform(src_crs,"EPSG:4326",[ev["x"]],[ev["y"]])
    offsets=ev.pop("offsets")
    plan={
        **ev,"mode":mode,"source_crs":src_crs,"source_pixel_spacing_m":spacing,
        "lon":float(lon[0]),"lat":float(lat[0]),"radius_px":radius_px,
        "coherence_min":coh_min,"min_pixels":min_pixels,"coarse_scan":coarse_meta,
        "note":"This common point/window only harmonizes HyP3 pair-specific phase references; LiCSBAS2 will still determine its own stable reference later."
    }
    (outdir/"reference_plan.json").write_text(json.dumps(plan,indent=2),encoding="utf-8")
    write_csv(outdir/"reference_offsets.csv",offsets)
    geojson={"type":"FeatureCollection","features":[{"type":"Feature",
             "properties":{"purpose":"HyP3 pair-reference harmonization","source_crs":src_crs,
                           "radius_px":radius_px},
             "geometry":{"type":"Point","coordinates":[plan["lon"],plan["lat"]]}}]}
    (outdir/"common_reference.geojson").write_text(json.dumps(geojson,indent=2),encoding="utf-8")
    return plan


def load_reference_offsets(path: Path) -> Dict[str,Dict]:
    rows=list(csv.DictReader(path.open(encoding="utf-8-sig")))
    out={}
    for r in rows:
        out[r["pair_id"]]={
            "offset_rad":float(r["offset_rad"]),
            "n_ref_pixels":int(float(r["n_ref_pixels"])),
            "ref_median_coherence":float(r["ref_median_coherence"]),
            "phase_mad_rad":float(r["phase_mad_rad"]),
        }
    return out


def warp_pair_v3(p: Product, geoc: Path, grid: Dict, ref_plan: Dict, ref_info: Dict,
                 phase_resampling: str, coh_resampling: str, coherence_uint8: bool=True,
                 overwrite: bool=False) -> Tuple[Path,Path]:
    pair=p.pair_id; od=geoc/pair; od.mkdir(parents=True,exist_ok=True)
    outu=od/f"{pair}.geo.unw.tif"; outc=od/f"{pair}.geo.cc.tif"
    if outu.exists() and outc.exists() and not overwrite:
        return outu,outc
    h,w=grid["height"],grid["width"]
    tr=from_origin(grid["left"],grid["top"],grid["xres_deg"],grid["yres_deg"])
    phase=np.full((h,w),np.nan,dtype=np.float32)
    coh=np.zeros((h,w),dtype=np.float32)
    with rasterio.open(p.src_uri("unw")) as su:
        reproject(source=rasterio.band(su,1),destination=phase,
                  src_transform=su.transform,src_crs=su.crs,src_nodata=su.nodata,
                  dst_transform=tr,dst_crs="EPSG:4326",dst_nodata=np.nan,
                  resampling=resampling_from_name(phase_resampling),
                  init_dest_nodata=True,num_threads=2)
    with rasterio.open(p.src_uri("corr")) as sc:
        reproject(source=rasterio.band(sc,1),destination=coh,
                  src_transform=sc.transform,src_crs=sc.crs,src_nodata=sc.nodata,
                  dst_transform=tr,dst_crs="EPSG:4326",dst_nodata=0.0,
                  resampling=resampling_from_name(coh_resampling),
                  init_dest_nodata=True,num_threads=2)
    coh=np.clip(coh,0.0,1.0)
    finite=np.isfinite(phase)
    phase[finite]-=np.float32(ref_info["offset_rad"])
    phase[(coh<=0)|~np.isfinite(phase)]=np.nan

    base={"driver":"GTiff","height":h,"width":w,"count":1,"crs":"EPSG:4326","transform":tr,
          "tiled":True,"compress":"DEFLATE","BIGTIFF":"IF_SAFER"}
    tmpu=outu.with_suffix(outu.suffix+".tmp"); tmpc=outc.with_suffix(outc.suffix+".tmp")
    with rasterio.open(tmpu,"w",dtype="float32",nodata=np.nan,predictor=3,**base) as ds:
        ds.write(phase,1)
        ds.update_tags(HYP3LICS_VERSION=VERSION,HYP3LICS_PHASE_UNITS="radian",
                       HYP3LICS_REFERENCED="1",HYP3LICS_REFERENCE_OFFSET_RAD=f"{ref_info['offset_rad']:.12g}",
                       HYP3LICS_REFERENCE_LON=f"{ref_plan['lon']:.10f}",
                       HYP3LICS_REFERENCE_LAT=f"{ref_plan['lat']:.10f}",
                       HYP3LICS_SOURCE=p.prefix)
    if coherence_uint8:
        q=np.rint(coh*255.0).astype(np.uint8)
        with rasterio.open(tmpc,"w",dtype="uint8",nodata=0,predictor=2,**base) as ds:
            ds.write(q,1)
            ds.update_tags(HYP3LICS_VERSION=VERSION,HYP3LICS_COHERENCE_SCALE="0-255_uint8",
                           HYP3LICS_SOURCE=p.prefix)
    else:
        with rasterio.open(tmpc,"w",dtype="float32",nodata=0.0,predictor=3,**base) as ds:
            ds.write(coh,1)
            ds.update_tags(HYP3LICS_VERSION=VERSION,HYP3LICS_COHERENCE_SCALE="0-1_float32",
                           HYP3LICS_SOURCE=p.prefix)
    os.replace(tmpu,outu); os.replace(tmpc,outc)
    return outu,outc


def validate_geoc_v3(geoc: Path, products: List[Product], grid: Dict) -> Dict:
    problems=[]; referenced=0; cc_dtypes=Counter()
    expected=(grid["height"],grid["width"])
    for p in products:
        pair=p.pair_id; uf=geoc/pair/f"{pair}.geo.unw.tif"; cf=geoc/pair/f"{pair}.geo.cc.tif"
        if not uf.exists(): problems.append(f"missing {uf}"); continue
        if not cf.exists(): problems.append(f"missing {cf}"); continue
        with rasterio.open(uf) as u,rasterio.open(cf) as c:
            if (u.height,u.width)!=expected or (c.height,c.width)!=expected:
                problems.append(f"shape mismatch {pair}")
            if str(u.crs)!="EPSG:4326" or str(c.crs)!="EPSG:4326":
                problems.append(f"CRS mismatch {pair}")
            if not u.transform.almost_equals(c.transform):
                problems.append(f"transform mismatch {pair}")
            if u.tags().get("HYP3LICS_REFERENCED")=="1": referenced+=1
            cc_dtypes[c.dtypes[0]]+=1
    return {"pair_count":len(products),"referenced_pair_count":referenced,
            "expected_shape":list(expected),"coherence_dtypes":dict(cc_dtypes),
            "problems":problems,
            "licsbas2_ready":len(problems)==0 and referenced==len(products)}



def _format_center_time(seconds: float) -> str:
    seconds = float(seconds) % 86400.0
    hh = int(seconds // 3600)
    mm = int((seconds - hh*3600) // 60)
    ss = seconds - hh*3600 - mm*60
    return f"{hh}:{mm:02d}:{ss:09.6f}"


def _select_master(products: List[Product]) -> str:
    degree = Counter()
    dates = sorted({d for p in products for d in (p.date1, p.date2) if d})
    for p in products:
        if p.date1 and p.date2:
            degree[p.date1] += 1
            degree[p.date2] += 1
    if not dates:
        raise RuntimeError("No acquisition dates available for master selection.")
    mid = datetime.strptime(dates[len(dates)//2], "%Y%m%d")
    maxdeg = max(degree.values())
    candidates = [d for d in dates if degree[d] >= maxdeg-1 and any(p.date1 == d and p.amp for p in products)]
    if not candidates:
        candidates = [d for d in dates if any(p.date1 == d and p.amp for p in products)]
    return min(candidates, key=lambda d: abs((datetime.strptime(d, "%Y%m%d") - mid).days))


def _invert_acquisition_baselines(products: List[Product], master: str):
    dates = sorted({d for p in products for d in (p.date1,p.date2) if d})
    idx = {d:i for i,d in enumerate(dates)}
    mi = idx[master]
    A=[]; y=[]; meta=[]
    for p in products:
        if p.baseline_m is None or not p.date1 or not p.date2:
            continue
        row=np.zeros(len(dates)-1,dtype=np.float64)
        for d,coef in ((p.date1,-1.0),(p.date2,1.0)):
            ii=idx[d]
            if ii==mi: continue
            jj=ii if ii<mi else ii-1
            row[jj]+=coef
        A.append(row); y.append(float(p.baseline_m)); meta.append(p)
    if len(A) < len(dates)-1:
        raise RuntimeError("Insufficient HyP3 baseline equations for acquisition-level inversion.")
    A=np.vstack(A); y=np.asarray(y,dtype=np.float64)
    xred,_,rank,_=np.linalg.lstsq(A,y,rcond=None)
    if rank < len(dates)-1:
        raise RuntimeError(f"Baseline inversion rank deficient: rank={rank}, required={len(dates)-1}")
    x=np.zeros(len(dates),dtype=np.float64)
    for d,ii in idx.items():
        if ii==mi: continue
        jj=ii if ii<mi else ii-1
        x[ii]=xred[jj]
    pred=A@xred
    resid=y-pred
    b={d:float(x[idx[d]]) for d in dates}
    residual_rows=[]
    for p,obs,pr,re in zip(meta,y,pred,resid):
        residual_rows.append({
            "pair_id":p.pair_id,
            "observed_hyp3_baseline_m":float(obs),
            "reconstructed_pair_baseline_m":float(pr),
            "residual_m":float(re),
        })
    stats={
        "equation":"bperp_secondary - bperp_reference = HyP3 pair Baseline",
        "master":master,
        "pair_count":len(y),
        "acquisition_count":len(dates),
        "rank":int(rank),
        "rms_m":float(np.sqrt(np.mean(resid**2))),
        "median_abs_m":float(np.median(np.abs(resid))),
        "max_abs_m":float(np.max(np.abs(resid))),
    }
    return b,residual_rows,stats


def _grid_transform(grid: Dict):
    return from_origin(grid["left"],grid["top"],grid["xres_deg"],grid["yres_deg"])


def _warp_single_band(src_uri: str, grid: Dict, resampling: Resampling,
                      dst_nodata: float=np.nan) -> np.ndarray:
    dst=np.full((grid["height"],grid["width"]),dst_nodata,dtype=np.float32)
    with rasterio.open(src_uri) as src:
        reproject(
            source=rasterio.band(src,1),destination=dst,
            src_transform=src.transform,src_crs=src.crs,src_nodata=src.nodata,
            dst_transform=_grid_transform(grid),dst_crs="EPSG:4326",
            dst_nodata=dst_nodata,resampling=resampling,
            init_dest_nodata=True,num_threads=2
        )
    return dst


def _warp_los_components_from_angles(theta_uri: str, phi_uri: str, grid: Dict,
                                     resampling: Resampling=Resampling.bilinear):
    """Convert HyP3 angular look vectors on the native grid, then warp E/N/U.

    This avoids interpolating the periodic azimuth/orientation angle ``phi``
    directly across its -pi/+pi branch cut.  HyP3 defines theta as the
    elevation angle of the ground-to-sensor look vector and phi as its
    horizontal orientation measured from East toward North, both in radians.
    """
    dst_shape=(grid["height"],grid["width"])
    dst_transform=_grid_transform(grid)
    outputs=[]
    with rasterio.open(theta_uri) as th, rasterio.open(phi_uri) as ph:
        if th.crs != ph.crs or th.transform != ph.transform or th.shape != ph.shape:
            raise RuntimeError("HyP3 lv_theta and lv_phi rasters are not co-registered.")
        theta_ma=th.read(1,masked=True).astype(np.float32)
        phi_ma=ph.read(1,masked=True).astype(np.float32)
        theta=np.asarray(theta_ma.filled(np.nan),dtype=np.float32)
        phi=np.asarray(phi_ma.filled(np.nan),dtype=np.float32)
        valid=(~np.ma.getmaskarray(theta_ma)) & (~np.ma.getmaskarray(phi_ma)) & np.isfinite(theta) & np.isfinite(phi)
        cos_theta=np.cos(theta).astype(np.float32,copy=False)
        for component in ("E","N","U"):
            src=np.full(theta.shape,np.nan,dtype=np.float32)
            if component=="E":
                src[valid]=cos_theta[valid]*np.cos(phi[valid])
            elif component=="N":
                src[valid]=cos_theta[valid]*np.sin(phi[valid])
            else:
                src[valid]=np.sin(theta[valid])
            dst=np.full(dst_shape,np.nan,dtype=np.float32)
            reproject(
                source=src,destination=dst,
                src_transform=th.transform,src_crs=th.crs,src_nodata=np.nan,
                dst_transform=dst_transform,dst_crs="EPSG:4326",dst_nodata=np.nan,
                resampling=resampling,init_dest_nodata=True,num_threads=2
            )
            outputs.append(dst)
            del src
        del theta,phi,cos_theta
    E,N,U=outputs
    good=np.isfinite(E)&np.isfinite(N)&np.isfinite(U)
    norm=np.sqrt(E*E+N*N+U*U)
    good &= norm>0
    E[good]/=norm[good]; N[good]/=norm[good]; U[good]/=norm[good]
    E[~good]=0.0; N[~good]=0.0; U[~good]=0.0
    max_err=float(np.max(np.abs(np.sqrt(E[good]**2+N[good]**2+U[good]**2)-1.0))) if np.any(good) else None
    return E,N,U,good,max_err


def _write_float_geotiff(path: Path, arr: np.ndarray, grid: Dict, nodata=0.0, tags=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    data=np.asarray(arr,dtype=np.float32)
    if np.isnan(nodata):
        out=data
    else:
        out=data.copy()
        out[~np.isfinite(out)] = np.float32(nodata)
    profile={
        "driver":"GTiff","height":grid["height"],"width":grid["width"],"count":1,
        "dtype":"float32","crs":"EPSG:4326","transform":_grid_transform(grid),
        "nodata":nodata,"tiled":True,"compress":"DEFLATE","predictor":3,"BIGTIFF":"IF_SAFER",
    }
    tmp=path.with_suffix(path.suffix+".tmp")
    with rasterio.open(tmp,"w",**profile) as ds:
        ds.write(out,1)
        if tags: ds.update_tags(**{k:str(v) for k,v in tags.items()})
    os.replace(tmp,path)


def _find_master_reference_product(products: List[Product], master: str) -> Product:
    cand=[p for p in products if p.date1==master and p.amp and p.dem and p.lv_theta and p.lv_phi and p.inc_map_ell]
    if not cand:
        raise RuntimeError(
            f"No product with {master} as HyP3 reference contains AMP+DEM+look vectors+ellipsoid incidence."
        )
    # Prefer largest native footprint.
    def area(p):
        if None in (p.unw_left,p.unw_bottom,p.unw_right,p.unw_top): return 0.0
        return (p.unw_right-p.unw_left)*(p.unw_top-p.unw_bottom)
    return max(cand,key=area)


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)


def _write_rgb_png(path: Path, rgb: np.ndarray, text: Optional[Dict[str,str]]=None) -> None:
    """Write an 8-bit RGB PNG using only Python stdlib + NumPy."""
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("RGB array must be uint8 HxWx3")
    h,w,_=rgb.shape
    raw=b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))
    out=[b"\x89PNG\r\n\x1a\n"]
    out.append(_png_chunk(b"IHDR", struct.pack(">IIBBBBB", w,h,8,2,0,0,0)))
    if text:
        for k,v in text.items():
            kk=str(k).encode('latin-1','replace')[:79]
            vv=str(v).encode('latin-1','replace')
            out.append(_png_chunk(b"tEXt", kk+b"\x00"+vv))
    out.append(_png_chunk(b"IDAT", zlib.compress(raw, level=6)))
    out.append(_png_chunk(b"IEND", b""))
    path.write_bytes(b"".join(out))


def _draw_line(img: np.ndarray, x0:int, y0:int, x1:int, y1:int, value:int, width:int=1) -> None:
    """Integer Bresenham line, grayscale value replicated to RGB."""
    h,w,_=img.shape
    dx=abs(x1-x0); sx=1 if x0<x1 else -1
    dy=-abs(y1-y0); sy=1 if y0<y1 else -1
    err=dx+dy
    r=max(0,width//2)
    while True:
        xa=max(0,x0-r); xb=min(w,x0+r+1); ya=max(0,y0-r); yb=min(h,y0+r+1)
        if xa<xb and ya<yb: img[ya:yb,xa:xb,:]=value
        if x0==x1 and y0==y1: break
        e2=2*err
        if e2>=dy: err+=dy; x0+=sx
        if e2<=dx: err+=dx; y0+=sy


def _draw_disc(img: np.ndarray, cx:int, cy:int, radius:int, value:int) -> None:
    h,w,_=img.shape
    y0=max(0,cy-radius); y1=min(h,cy+radius+1)
    x0=max(0,cx-radius); x1=min(w,cx+radius+1)
    if x0>=x1 or y0>=y1: return
    yy,xx=np.ogrid[y0:y1,x0:x1]
    mask=(xx-cx)**2+(yy-cy)**2 <= radius*radius
    block=img[y0:y1,x0:x1]
    block[mask]=value



def _create_network_png_stdlib(path: Path, products: List[Product], bperp: Dict[str,float], master: str):
    """
    Create a LiCSAR-style diagnostic network PNG without Matplotlib/Pillow.

    This intentionally uses only NumPy + Python's zlib/struct so Windows
    plotting-library DLL problems cannot block scientific processing.
    """
    dates=sorted(bperp)
    if not dates:
        raise RuntimeError("Cannot create network.png: no acquisition baselines")
    dt={d:datetime.strptime(d,"%Y%m%d") for d in dates}
    ords={d:dt[d].toordinal() for d in dates}
    xmin=min(ords.values()); xmax=max(ords.values())
    ys=np.asarray([bperp[d] for d in dates],dtype=float)
    ymin=float(np.min(ys)); ymax=float(np.max(ys))
    if ymax<=ymin: ymax=ymin+1.0
    ypad=max(10.0,0.08*(ymax-ymin)); ymin-=ypad; ymax+=ypad

    W,H=1600,900
    L,R,T,B=100,40,55,80
    pw=W-L-R; ph=H-T-B
    img=np.full((H,W,3),255,dtype=np.uint8)

    def px(d):
        return L + int(round((ords[d]-xmin)/max(1,xmax-xmin)*pw))
    def py(v):
        return T + int(round((ymax-v)/(ymax-ymin)*ph))

    # Year guide lines.
    y0=dt[dates[0]].year; y1=dt[dates[-1]].year
    for yr in range(y0,y1+1):
        d=datetime(yr,1,1).toordinal()
        if xmin<=d<=xmax:
            x=L+int(round((d-xmin)/max(1,xmax-xmin)*pw))
            _draw_line(img,x,T,x,T+ph,235,1)

    # Horizontal baseline guide lines at sensible rounded spacing.
    span=ymax-ymin
    raw_step=span/8.0
    mag=10**math.floor(math.log10(max(raw_step,1e-9)))
    norm=raw_step/mag
    step=(1 if norm<=1 else 2 if norm<=2 else 5 if norm<=5 else 10)*mag
    gy=math.ceil(ymin/step)*step
    while gy<=ymax+1e-9:
        _draw_line(img,L,py(gy),L+pw,py(gy),240 if abs(gy)>1e-9 else 190,1)
        gy+=step

    # Plot border.
    _draw_line(img,L,T,L+pw,T,80,1); _draw_line(img,L,T+ph,L+pw,T+ph,80,1)
    _draw_line(img,L,T,L,T+ph,80,1); _draw_line(img,L+pw,T,L+pw,T+ph,80,1)

    # Interferogram edges first.
    edge_count=0
    for p in products:
        if p.date1 in bperp and p.date2 in bperp:
            _draw_line(img,px(p.date1),py(bperp[p.date1]),px(p.date2),py(bperp[p.date2]),185,1)
            edge_count+=1

    # Acquisition nodes.
    for d in dates:
        _draw_disc(img,px(d),py(bperp[d]),3,40)
    # Master: larger ring-like marker (dark outer, white center).
    if master in bperp:
        _draw_disc(img,px(master),py(bperp[master]),8,20)
        _draw_disc(img,px(master),py(bperp[master]),3,255)

    meta={
        "Title":f"HyP3 SBAS network; master={master}",
        "Acquisitions":str(len(dates)),
        "Interferograms":str(edge_count),
        "DateStart":dates[0],
        "DateEnd":dates[-1],
        "BperpMin_m":f"{min(bperp.values()):.6f}",
        "BperpMax_m":f"{max(bperp.values()):.6f}",
        "Generator":f"HyP3-to-LiCSBAS {VERSION}; stdlib PNG backend",
    }
    _write_rgb_png(path,img,meta)
    if not path.exists() or path.stat().st_size==0:
        raise RuntimeError("network.png writer returned an empty file")
    return "stdlib"



def _create_network_png_matplotlib(path: Path, products: List[Product], bperp: Dict[str,float], master: str):
    """
    Create the network plot with Matplotlib when the local installation is healthy.
    Uses Agg explicitly so Linux/headless servers and Windows do not need a GUI.
    """
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    dates=sorted(bperp)
    if not dates:
        raise RuntimeError("Cannot create network.png: no acquisition baselines")
    x={d:datetime.strptime(d,"%Y%m%d") for d in dates}

    fig,ax=plt.subplots(figsize=(13,7))
    for p in products:
        if p.date1 in bperp and p.date2 in bperp:
            ax.plot([x[p.date1],x[p.date2]],
                    [bperp[p.date1],bperp[p.date2]],
                    linewidth=0.7,alpha=0.45)
    ax.scatter([x[d] for d in dates],[bperp[d] for d in dates],s=18,zorder=3)
    if master in bperp:
        ax.scatter([x[master]],[bperp[master]],s=75,zorder=4,
                   facecolors="none",edgecolors="black",linewidths=1.2)
    ax.axhline(0,linewidth=0.8)
    ax.set_xlabel("Acquisition date")
    ax.set_ylabel("Perpendicular baseline relative to master (m)")
    ax.set_title(
        f"HyP3 SBAS network | master={master} | "
        f"{len(dates)} acquisitions | {len(products)} interferograms"
    )
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path,dpi=150,metadata={
        "Software":f"HyP3-to-LiCSBAS {VERSION}",
        "Description":"Acquisition-level perpendicular-baseline network reconstructed from HyP3 pair baselines",
    })
    plt.close(fig)
    if not path.exists() or path.stat().st_size==0:
        raise RuntimeError("Matplotlib network.png writer returned an empty file")
    return "matplotlib"


def _create_network_png(path: Path, products: List[Product], bperp: Dict[str,float],
                        master: str, backend: str="auto"):
    """
    Cross-platform network plot dispatcher.

    backend:
      auto       -> try Matplotlib/Agg, fall back to stdlib PNG on *any* import/runtime error.
      matplotlib -> require Matplotlib/Agg; fail if unavailable/broken.
      stdlib     -> NumPy + Python stdlib zlib/struct only.

    The broad Exception catch in auto mode is intentional: broken binary/DLL
    Matplotlib installations must never block the scientific conversion.
    """
    backend=(backend or "auto").lower()
    if backend not in {"auto","matplotlib","stdlib"}:
        raise ValueError(f"Unknown plot backend: {backend}")

    disable_mpl = os.environ.get("HYP3LICS_DISABLE_MATPLOTLIB","").strip().lower() in {"1","true","yes","on"}
    if backend in {"auto","matplotlib"} and not (backend=="auto" and disable_mpl):
        try:
            used=_create_network_png_matplotlib(path,products,bperp,master)
            log("network.png backend: matplotlib/Agg")
            return used
        except Exception as exc:
            if backend=="matplotlib":
                raise RuntimeError(
                    "Matplotlib plotting was explicitly requested but failed: "
                    + repr(exc)
                ) from exc
            log("network.png: Matplotlib unavailable/broken; using stdlib fallback.")
            log(f"  Matplotlib error: {exc!r}")
    elif backend=="auto" and disable_mpl:
        log("network.png: Matplotlib disabled by HYP3LICS_DISABLE_MATPLOTLIB; using stdlib fallback.")

    used=_create_network_png_stdlib(path,products,bperp,master)
    log("network.png backend: stdlib zlib/struct")
    return used


def create_complete_ancillaries(geoc: Path, qc: Path, products: List[Product], grid: Dict, plot_backend: str="auto") -> Dict:
    """
    Build LiCSAR-like ancillary files using only real HyP3 inputs.
    No unsupported LiCSAR-specific metadata field is fabricated.
    """
    master=_select_master(products)
    source=_find_master_reference_product(products,master)
    log(f"\nAncillary source product: {source.pair_id} (reference acquisition {master})")
    log(f"Derived LiCSBAS baseline master: {master}")

    bperp,residual_rows,bstats=_invert_acquisition_baselines(products,master)
    master_dt=datetime.strptime(master,"%Y%m%d")
    with (geoc/"baselines").open("w",encoding="utf-8") as f:
        for d in sorted(bperp):
            dt=(datetime.strptime(d,"%Y%m%d")-master_dt).days
            f.write(f"{master} {d} {bperp[d]:.6f} {dt}\n")
    write_csv(qc/"baseline_pair_residuals.csv",residual_rows)
    (qc/"baseline_inversion_summary.json").write_text(json.dumps(bstats,indent=2),encoding="utf-8")
    network_backend=_create_network_png(geoc/"network.png",products,bperp,master,plot_backend)

    # Native HyP3 ancillary rasters are smooth geometry/background products.
    # Bilinear interpolation is suitable when retaining native posting.
    # At coarser output posting average is used for amp/dem/incidence; angles
    # remain bilinear because averaging angles can be unsafe around wrap boundaries.
    source_spacing=float(np.median([p.unw_res_x for p in products if p.unw_res_x]))
    coarse=grid["target_spacing_m"] >= 1.5*source_spacing
    scalar_resamp=Resampling.average if coarse else Resampling.bilinear

    log("Create geo.mli from HyP3 calibrated reference amplitude...")
    amp=_warp_single_band(source.src_uri("amp"),grid,scalar_resamp,dst_nodata=np.nan)
    amp[~np.isfinite(amp)]=0.0
    _write_float_geotiff(
        geoc/"MGX.geo.mli.tif",amp,grid,nodata=0.0,
        tags={"SOURCE":"HyP3 _amp.tif","SOURCE_PAIR":source.pair_id,
              "DESCRIPTION":"Reference-granule calibrated sigma-nought power used as LiCSBAS background MLI"}
    )
    del amp

    log("Create geo.hgt from HyP3 processing DEM...")
    hgt=_warp_single_band(source.src_uri("dem"),grid,scalar_resamp,dst_nodata=np.nan)
    valid_hgt=np.isfinite(hgt)
    avg_height=float(np.nanmean(hgt[valid_hgt])) if np.any(valid_hgt) else None
    hgt_out=hgt.copy(); hgt_out[~valid_hgt]=0.0
    _write_float_geotiff(
        geoc/"MGX.geo.hgt.tif",hgt_out,grid,nodata=0.0,
        tags={"SOURCE":"HyP3 _dem.tif","SOURCE_PAIR":source.pair_id,
              "DEM_SOURCE":source.dem_source or "unknown",
              "DESCRIPTION":"HyP3 processing DEM, geoid-corrected and supplied by ASF"}
    )
    del hgt,hgt_out

    log("Create geo.E/N/U from HyP3 look-vector theta/phi (wrap-safe component-first resampling)...")
    E,N,U,good,unit_err=_warp_los_components_from_angles(
        source.src_uri("lv_theta"),source.src_uri("lv_phi"),grid,Resampling.bilinear
    )
    for name,arr in (("E",E),("N",N),("U",U)):
        _write_float_geotiff(
            geoc/f"MGX.geo.{name}.tif",arr,grid,nodata=0.0,
            tags={"SOURCE":"HyP3 _lv_theta.tif + _lv_phi.tif",
                  "SOURCE_PAIR":source.pair_id,
                  "VECTOR_DIRECTION":"ground_to_sensor",
                  "RESAMPLING":"native-grid E/N/U components -> bilinear warp -> unit renormalization",
                  "DESCRIPTION":f"LOS unit-vector {name} component"}
        )
    del E,N,U,good

    log("Read ellipsoid incidence map for frame metadata...")
    inc=_warp_single_band(source.src_uri("inc_map_ell"),grid,Resampling.bilinear,dst_nodata=np.nan)
    valid_inc=np.isfinite(inc)
    avg_inc_deg=float(np.degrees(np.nanmean(inc[valid_inc]))) if np.any(valid_inc) else None
    del inc

    # Master acquisition fields: HyP3 UTCTime/Heading belong to the reference granule.
    master_rows=[p for p in products if p.date1==master]
    def med(vals):
        vals=[float(v) for v in vals if v is not None and np.isfinite(v)]
        return float(np.median(vals)) if vals else None
    center_s=med([p.utc_time_s for p in master_rows])
    heading=med([p.heading_deg for p in master_rows])
    centre_range=med([p.slant_range_center_m for p in master_rows])
    dem_source=Counter([p.dem_source for p in products if p.dem_source]).most_common(1)
    dem_source=dem_source[0][0] if dem_source else None

    metadata_lines=[]
    def put(k,v):
        if v is not None:
            metadata_lines.append(f"{k}={v}")
    put("master",master)
    put("center_time",_format_center_time(center_s) if center_s is not None else None)
    put("heading",f"{heading:.9f}" if heading is not None else None)
    put("avg_incidence_angle",f"{avg_inc_deg:.6f}" if avg_inc_deg is not None else None)
    put("centre_range_m",f"{centre_range:.4f}" if centre_range is not None else None)
    put("avg_height",f"{avg_height:.6f}" if avg_height is not None else None)
    put("applied_DEM",dem_source)
    put("radar_freq","5.405e9")
    (geoc/"metadata.txt").write_text("\n".join(metadata_lines)+"\n",encoding="utf-8")

    missing_licsar_fields={
        "azimuth_resolution":"Not present in standard HyP3 GAMMA pair package; omitted rather than guessed.",
        "range_resolution":"Not present in standard HyP3 GAMMA pair package; omitted rather than guessed.",
        "centre_range_ok_m":"LiCSAR-specific processing quantity with no documented direct HyP3 mapping; omitted rather than fabricated.",
    }
    provenance={
        "tool":"HyP3-to-LiCSBAS",
        "version":VERSION,
        "ancillary_source_pair":source.pair_id,
        "ancillary_reference_acquisition":master,
        "metadata_semantics":{
            "master":"Derived real acquisition used only as acquisition-level Bperp zero datum and MLI/geometry reference.",
            "center_time":"HyP3 UTCTime for products where master is the reference acquisition.",
            "heading":"HyP3 Heading for the master reference acquisition.",
            "avg_incidence_angle":"Mean of HyP3 ellipsoid incidence-angle raster on final grid, converted rad->deg.",
            "centre_range_m":"HyP3 Slant range center for the master reference acquisition.",
            "avg_height":"Mean valid pixel value of final HyP3-derived geo.hgt raster.",
            "applied_DEM":"HyP3 DEM source.",
            "radar_freq":"Sentinel-1 C-band compatibility value used by LiCSBAS2."
        },
        "intentionally_omitted_licsar_fields":missing_licsar_fields,
        "baseline_inversion":bstats,
        "look_vector_formula":{
            "E":"cos(theta)*cos(phi)",
            "N":"cos(theta)*sin(phi)",
            "U":"sin(theta)",
            "theta":"HyP3 elevation angle of ground-to-sensor look vector, radians",
            "phi":"HyP3 orientation measured from East toward North, radians",
            "resampling":"E/N/U are computed on the native HyP3 grid before bilinear reprojection; phi itself is never interpolated, avoiding the -pi/+pi branch cut.",
            "max_unit_norm_error_after_renormalization":unit_err,
        },
        "mli_note":"HyP3 _amp.tif is calibrated sigma-nought power from the reference granule. It is used as the LiCSBAS display/background MLI analogue, not claimed to be numerically identical to LiCSAR GAMMA MLI.",
        "dem_note":"HyP3 _dem.tif is the actual DEM used in HyP3 processing; ASF documents geoid correction and resampling in the delivered optional DEM.",
        "network_plot_backend":network_backend,
    }
    (qc/"ancillary_provenance.json").write_text(json.dumps(provenance,indent=2),encoding="utf-8")
    return {
        "master":master,
        "source_pair":source.pair_id,
        "metadata_file":str(geoc/"metadata.txt"),
        "baseline_file":str(geoc/"baselines"),
        "network_png":str(geoc/"network.png"),
        "network_plot_backend":network_backend,
        "mli":str(geoc/"MGX.geo.mli.tif"),
        "hgt":str(geoc/"MGX.geo.hgt.tif"),
        "E":str(geoc/"MGX.geo.E.tif"),
        "N":str(geoc/"MGX.geo.N.tif"),
        "U":str(geoc/"MGX.geo.U.tif"),
        "avg_height_m":avg_height,
        "avg_incidence_angle_deg":avg_inc_deg,
        "baseline_residual_rms_m":bstats["rms_m"],
        "baseline_residual_max_abs_m":bstats["max_abs_m"],
        "look_vector_max_unit_norm_error":unit_err,
    }


def validate_complete_geoc(geoc: Path, products: List[Product], grid: Dict) -> Dict:
    core=validate_geoc_v3(geoc,products,grid)
    ancillary_required=[
        "metadata.txt","baselines","network.png",
        "MGX.geo.mli.tif","MGX.geo.hgt.tif","MGX.geo.E.tif","MGX.geo.N.tif","MGX.geo.U.tif"
    ]
    missing=[x for x in ancillary_required if not (geoc/x).exists()]
    ancillary_problems=[]
    expected=(grid["height"],grid["width"])
    for fn in ["MGX.geo.mli.tif","MGX.geo.hgt.tif","MGX.geo.E.tif","MGX.geo.N.tif","MGX.geo.U.tif"]:
        fp=geoc/fn
        if not fp.exists(): continue
        with rasterio.open(fp) as ds:
            if (ds.height,ds.width)!=expected: ancillary_problems.append(f"{fn}: shape mismatch")
            if str(ds.crs)!="EPSG:4326": ancillary_problems.append(f"{fn}: CRS mismatch")
    # ENU norm check on a decimated read to avoid unnecessary memory.
    e=geoc/"MGX.geo.E.tif"; n=geoc/"MGX.geo.N.tif"; u=geoc/"MGX.geo.U.tif"
    enu_stat=None
    if e.exists() and n.exists() and u.exists():
        with rasterio.open(e) as de, rasterio.open(n) as dn, rasterio.open(u) as du:
            step=max(1,int(max(de.height,de.width)/1000))
            E=de.read(1)[::step,::step]; N=dn.read(1)[::step,::step]; U=du.read(1)[::step,::step]
            good=(E!=0)|(N!=0)|(U!=0)
            if np.any(good):
                norms=np.sqrt(E[good]**2+N[good]**2+U[good]**2)
                enu_stat={"median_norm":float(np.median(norms)),
                          "max_abs_norm_error":float(np.max(np.abs(norms-1.0)))}
                if enu_stat["max_abs_norm_error"]>1e-3:
                    ancillary_problems.append("ENU unit-vector norm check failed")
    return {
        **core,
        "ancillary_required":ancillary_required,
        "ancillary_missing":missing,
        "ancillary_problems":ancillary_problems,
        "enu_norm_check":enu_stat,
        "core_ready":core["licsbas2_ready"],
        "full_GEOC_ready":core["licsbas2_ready"] and not missing and not ancillary_problems,
    }


def make_metadata(geoc: Path):
    # Deprecated compatibility stub. Complete metadata is created by
    # create_complete_ancillaries() after the IFG stack is written.
    return None


def validate_geoc(geoc: Path, products: List[Product], grid: Dict) -> Dict:
    problems=[]; shapes=[]; crss=[]; referenced=0
    for p in products:
        pair=p.pair_id; uf=geoc/pair/f"{pair}.geo.unw.tif"; cf=geoc/pair/f"{pair}.geo.cc.tif"
        if not uf.exists(): problems.append(f"missing {uf}"); continue
        if not cf.exists(): problems.append(f"missing {cf}"); continue
        with rasterio.open(uf) as u, rasterio.open(cf) as c:
            shapes.append((u.height,u.width)); crss.append(u.crs.to_string() if u.crs else None)
            if (u.height,u.width)!=(c.height,c.width): problems.append(f"shape mismatch {pair}")
            if u.crs!=c.crs: problems.append(f"CRS mismatch {pair}")
            if not u.transform.almost_equals(c.transform): problems.append(f"transform mismatch {pair}")
            if u.tags().get("HYP3LICS_REFERENCED")=="1": referenced+=1
    expected=(grid["height"],grid["width"])
    if any(s!=expected for s in shapes): problems.append("not all rasters match master-grid shape")
    if any(c!="EPSG:4326" for c in crss): problems.append("not all rasters are EPSG:4326")
    return {"pair_count":len(products),"referenced_pair_count":referenced,"expected_shape":expected,"problems":problems,
            "licsbas2_ready":len(problems)==0 and referenced==len(products)}



def _write_footprint_files(qc: Path, products: List[Product]) -> Dict:
    fd=footprint_diagnosis(products)
    outliers=fd.pop("outlier_rows",[]) if fd else []
    (qc/"footprint_diagnosis.json").write_text(json.dumps(fd,indent=2),encoding="utf-8")
    write_csv(qc/"footprint_outliers.csv",outliers)
    return fd


def cmd_preflight(args):
    products,summary=preflight(Path(args.input).expanduser().resolve(),
                               Path(args.output).expanduser().resolve())
    fd=_write_footprint_files(Path(args.output).expanduser().resolve(),products)
    if fd:
        log("\nFootprint diagnosis:")
        log(json.dumps(fd,indent=2))
    return 2 if summary["issues"].get("ERROR",0) else 0


def cmd_plan(args):
    root=Path(args.input).expanduser().resolve()
    out=Path(args.output).expanduser().resolve(); out.mkdir(parents=True,exist_ok=True)
    products,summary=preflight(root,out)
    if summary["issues"].get("ERROR",0):
        raise RuntimeError("Preflight contains ERROR issues.")
    fd=_write_footprint_files(out,products)
    log("\nPlanning one common HyP3 harmonization reference directly in the source UTM stack...")
    ref=make_reference_plan(products,out,args.ref_x,args.ref_y,args.ref_radius_px,
                            args.ref_coh_min,args.ref_min_pixels,args.ref_scan_factor)
    grids=[]
    for spacing in args.report_spacings:
        for mode in ("intersection","union"):
            g=create_master_grid_v3(products,mode,float(spacing))
            grids.append(g)
    (out/"grid_options.json").write_text(json.dumps(grids,indent=2),encoding="utf-8")
    log("\nREFERENCE PLAN:")
    log(json.dumps(ref,indent=2))
    log("\nGRID OPTIONS:")
    log(json.dumps(grids,indent=2))
    if fd and fd.get("intersection_area_fraction_of_median",1)<0.90:
        log("\nWARNING: full-stack bounding-box intersection keeps less than 90% of a typical product footprint.")
        log("This is caused by a small number of reduced-footprint interferograms. Do not exclude them automatically.")
        log("Use intersection for strict common support, union to preserve all spatial coverage, or bbox for a study AOI.")
    return 0



def reuse_reference_plan(plan_dir: Path, products: List[Product], qc: Path) -> Tuple[Dict, Dict[str,Dict]]:
    """Validate and reuse an already-computed v0.3+ reference plan."""
    plan_dir = plan_dir.expanduser().resolve()
    rp = plan_dir / "reference_plan.json"
    ro = plan_dir / "reference_offsets.csv"
    pi = plan_dir / "preflight_inventory.csv"
    if not rp.exists() or not ro.exists():
        raise RuntimeError(
            f"Plan directory must contain reference_plan.json and reference_offsets.csv: {plan_dir}"
        )

    ref = json.loads(rp.read_text(encoding="utf-8"))
    offsets = load_reference_offsets(ro)

    current_pairs = {p.pair_id for p in products}
    planned_pairs = set(offsets)
    if current_pairs != planned_pairs:
        missing = sorted(current_pairs - planned_pairs)
        extra = sorted(planned_pairs - current_pairs)
        raise RuntimeError(
            "The supplied PLAN does not match the current HyP3 stack.\n"
            f"Missing offsets for current pairs: {missing[:10]}\n"
            f"Extra planned pairs: {extra[:10]}"
        )
    if len(offsets) != len(products):
        raise RuntimeError(
            f"Reference offset count mismatch: plan={len(offsets)}, products={len(products)}"
        )
    if int(ref.get("failure_count", -1)) != 0:
        raise RuntimeError("Supplied reference plan contains failed interferograms.")

    # Optional stronger cross-check against the plan's inventory.
    if pi.exists():
        rows = list(csv.DictReader(pi.open(encoding="utf-8-sig")))
        inv_pairs = {
            f"{r.get('date1')}_{r.get('date2')}"
            for r in rows if r.get("date1") and r.get("date2")
        }
        if inv_pairs and inv_pairs != current_pairs:
            raise RuntimeError("The supplied PLAN preflight inventory differs from the current stack.")

    qc.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rp, qc / "reference_plan.json")
    shutil.copy2(ro, qc / "reference_offsets.csv")
    for optional in ("common_reference.geojson", "grid_options.json",
                     "footprint_diagnosis.json", "footprint_outliers.csv"):
        q = plan_dir / optional
        if q.exists():
            shutil.copy2(q, qc / f"plan_{optional}")

    (qc / "reference_plan_reuse.json").write_text(
        json.dumps({
            "reused": True,
            "source_plan_dir": str(plan_dir),
            "pair_count": len(offsets),
            "reference_lon": ref.get("lon"),
            "reference_lat": ref.get("lat"),
            "failure_count": ref.get("failure_count"),
        }, indent=2),
        encoding="utf-8",
    )
    return ref, offsets


def cmd_prepare(args):
    root=Path(args.input).expanduser().resolve()
    out=Path(args.output).expanduser().resolve(); out.mkdir(parents=True,exist_ok=True)
    qc=out/"_hyp3lics"; qc.mkdir(exist_ok=True)
    products,summary=preflight(root,qc)
    if summary["issues"].get("ERROR",0):
        raise RuntimeError("Preflight contains ERROR issues; see _hyp3lics/preflight_issues.csv")
    if not summary["network_connected"]:
        raise RuntimeError("SBAS network is disconnected.")
    fd=_write_footprint_files(qc,products)

    if args.extent_mode=="intersection" and fd.get("intersection_area_fraction_of_median",1)<0.90:
        log(f"\nNOTICE: intersection retains only {100*fd['intersection_area_fraction_of_median']:.1f}% "
            "of the median source-product rectangle for this stack.")
        log("This is intentional only if you want strict common spatial support.")

    if args.target_spacing_m is None:
        vals=[p.output_resolution_m for p in products if p.output_resolution_m is not None]
        if not vals:
            raise RuntimeError("Cannot infer native HyP3 output spacing; specify --target-spacing-m.")
        args.target_spacing_m=float(np.median(vals))
        log(f"Native HyP3 posting selected automatically: {args.target_spacing_m:g} m")
    grid=create_master_grid_v3(products,args.extent_mode,args.target_spacing_m,args.bbox)
    (qc/"master_grid.json").write_text(json.dumps(grid,indent=2),encoding="utf-8")
    log("\nMaster grid:")
    log(json.dumps(grid,indent=2))

    # Reuse a validated PLAN when provided; otherwise compute from source data.
    if args.plan_dir:
        log("\nStage 1/3: Validate and reuse existing common-reference PLAN")
        ref, offsets = reuse_reference_plan(Path(args.plan_dir), products, qc)
        log(f"  Reused reference offsets for {len(offsets)} interferograms")
        log(f"  Common reference: lon={ref.get('lon')}, lat={ref.get('lat')}")
    else:
        log("\nStage 1/3: Plan common reference directly from source HyP3 products")
        ref=make_reference_plan(products,qc,args.ref_x,args.ref_y,args.ref_radius_px,
                                args.ref_coh_min,args.ref_min_pixels,args.ref_scan_factor)
        offsets=load_reference_offsets(qc/"reference_offsets.csv")

    # If target is coarser than source, averaging unwrapped phase is equivalent in spirit
    # to multilooking and avoids throwing away 3/4 of the samples.
    phase_resampling=args.phase_resampling
    coh_resampling=args.coherence_resampling
    src_spacing=float(np.median([p.unw_res_x for p in products if p.unw_res_x]))
    if phase_resampling=="auto":
        phase_resampling="average" if args.target_spacing_m >= 1.5*src_spacing else "nearest"
    if coh_resampling=="auto":
        coh_resampling="average" if args.target_spacing_m >= 1.5*src_spacing else "bilinear"
    log(f"  Phase resampling    : {phase_resampling}")
    log(f"  Coherence resampling: {coh_resampling}")

    geoc=out/"GEOC"; geoc.mkdir(exist_ok=True)
    log("\nStage 2/3: Reproject, harmonize reference, and write LiCSBAS2 GEOC")
    rows=[]
    for i,p in enumerate(products,1):
        log(f"  [{i:4d}/{len(products)}] {p.pair_id}")
        if p.pair_id not in offsets:
            raise RuntimeError(f"No reference offset for {p.pair_id}")
        u,c=warp_pair_v3(p,geoc,grid,ref,offsets[p.pair_id],
                         phase_resampling,coh_resampling,
                         coherence_uint8=not args.keep_float_coherence,
                         overwrite=args.overwrite)
        rows.append({"pair_id":p.pair_id,"unw":str(u),"corr":str(c),
                     "offset_rad":offsets[p.pair_id]["offset_rad"]})
    write_csv(qc/"conversion_files.csv",rows)

    log("\nStage 3/4: Build complete LiCSAR-like ancillary package from real HyP3 inputs")
    ancillary=create_complete_ancillaries(geoc,qc,products,grid,args.plot_backend)
    (qc/"ancillary_summary.json").write_text(json.dumps(ancillary,indent=2),encoding="utf-8")

    log("\nStage 4/4: Validate complete LiCSBAS2 GEOC stack")
    val=validate_complete_geoc(geoc,products,grid)
    (qc/"validation.json").write_text(json.dumps(val,indent=2),encoding="utf-8")
    next_n=1
    text=(
        "# Run in LiCSBAS2 under Linux/WSL\n"
        "# The adapter has already applied the selected target spacing.\n"
        f"LiCSBAS02_ml_prep.py -i GEOC -n {next_n}\n\n"
        "# Continue with LiCSBAS11_check_unw.py, LiCSBAS12_loop_closure.py,\n"
        "# LiCSBAS13_sb_inv.py, and Steps 14-16.\n"
        "# Do NOT multiply HyP3 phase by -1; ordinary HyP3 GAMMA phase sign is already compatible.\n"
    )
    (out/"NEXT_LICSBAS2.txt").write_text(text,encoding="utf-8")
    log(json.dumps(val,indent=2))
    if not val["full_GEOC_ready"]:
        raise RuntimeError("Complete GEOC validation failed; see _hyp3lics/validation.json")
    log("\nSUCCESS: complete LiCSAR-like, LiCSBAS2-ready GEOC stack created.")
    return 0


def cmd_validate(args):
    out=Path(args.output).expanduser().resolve(); qc=out/"_hyp3lics"; geoc=out/"GEOC"
    inv=list(csv.DictReader((qc/"preflight_inventory.csv").open(encoding="utf-8-sig")))
    products=[]
    for r in inv:
        products.append(Product(r.get("source_type",""),r.get("container",""),r.get("prefix",""),
                                r.get("date1") or None,r.get("date2") or None,
                                r.get("unw") or None,r.get("corr") or None,
                                r.get("meta") or None,r.get("readme") or None))
    grid=json.loads((qc/"master_grid.json").read_text(encoding="utf-8"))
    val=validate_complete_geoc(geoc,products,grid)
    log(json.dumps(val,indent=2))
    return 0 if val["full_GEOC_ready"] else 2


def build_parser():
    p=argparse.ArgumentParser(prog="hyp3lics",
        description="ASF HyP3 GAMMA InSAR -> LiCSBAS2 GEOC adapter")
    p.add_argument("--version",action="version",version=VERSION)
    sp=p.add_subparsers(dest="cmd",required=True)

    q=sp.add_parser("preflight")
    q.add_argument("-i","--input",required=True); q.add_argument("-o","--output",required=True)
    q.set_defaults(func=cmd_preflight)

    q=sp.add_parser("plan",help="Read-only footprint/reference/grid planning; writes no GEOC stack")
    q.add_argument("-i","--input",required=True); q.add_argument("-o","--output",required=True)
    q.add_argument("--ref-x",type=float,default=None,help="Optional source-CRS reference X")
    q.add_argument("--ref-y",type=float,default=None,help="Optional source-CRS reference Y")
    q.add_argument("--ref-radius-px",type=int,default=4)
    q.add_argument("--ref-coh-min",type=float,default=0.20)
    q.add_argument("--ref-min-pixels",type=int,default=9)
    q.add_argument("--ref-scan-factor",type=int,default=8)
    q.add_argument("--report-spacings",type=float,nargs="+",default=[40,80,120])
    q.set_defaults(func=cmd_plan)

    q=sp.add_parser("prepare")
    q.add_argument("-i","--input",required=True); q.add_argument("-o","--output",required=True)
    q.add_argument("--plan-dir",default=None,
                   help="Reuse a previously completed v0.3+ PLAN directory; product pairs are strictly validated before reuse.")
    q.add_argument("--extent-mode",choices=["intersection","union","bbox"],default="intersection")
    q.add_argument("--bbox",type=float,nargs=4,metavar=("WEST","SOUTH","EAST","NORTH"),default=None)
    q.add_argument("--target-spacing-m",type=float,default=None,
                   help="Target approximate WGS84 pixel spacing. Default: preserve HyP3 native posting (INT40->40 m, INT80->80 m).")
    q.add_argument("--phase-resampling",choices=["auto","nearest","bilinear","cubic","average"],default="auto")
    q.add_argument("--coherence-resampling",choices=["auto","nearest","bilinear","cubic","average"],default="auto")
    q.add_argument("--ref-x",type=float,default=None); q.add_argument("--ref-y",type=float,default=None)
    q.add_argument("--ref-radius-px",type=int,default=4)
    q.add_argument("--ref-coh-min",type=float,default=0.20)
    q.add_argument("--ref-min-pixels",type=int,default=9)
    q.add_argument("--ref-scan-factor",type=int,default=8)
    q.add_argument("--plot-backend",choices=["auto","matplotlib","stdlib"],default="auto",
                   help="network.png backend. auto tries Matplotlib/Agg then falls back to stdlib PNG; default auto.")
    q.add_argument("--keep-float-coherence",action="store_true",
                   help="Keep 0-1 float32 coherence. Default writes 0-255 uint8, which LiCSBAS2 accepts and greatly reduces disk.")
    q.add_argument("--overwrite",action="store_true")
    q.set_defaults(func=cmd_prepare)

    q=sp.add_parser("validate")
    q.add_argument("-o","--output",required=True); q.set_defaults(func=cmd_validate)
    return p

def main():
    args=build_parser().parse_args()
    try: return args.func(args)
    except KeyboardInterrupt: log("\nInterrupted by user."); return 130
    except Exception as exc: log(f"\nERROR: {exc}"); return 2

if __name__ == "__main__": sys.exit(main())
