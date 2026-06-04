"""
azure_goes16_ingest.py
Pulls latest GOES-16 ABI CONUS data from NOAA's public Azure blob storage.
No credentials required - anonymous public access.
"""

import logging
import os
import sys
from datetime import datetime, timezone

import netCDF4 as nc
import numpy as np
from azure.storage.blob import ContainerClient

ACCOUNT_URL = "https://goeseuwest.blob.core.windows.net"
CONTAINER   = "noaa-goes16"
PRODUCT     = "ABI-L2-MCMIPC"
STAGING_DIR = os.path.expanduser("~/noaa-pipeline-monitor/data/staging")
LOG_DIR     = os.path.expanduser("~/noaa-pipeline-monitor/logs")
LOG_FILE    = os.path.join(LOG_DIR, "ingest.log")

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def get_blob_prefix(dt: datetime) -> str:
    """
    GOES-16 Azure path: PRODUCT/YYYY/DDD/HH/
    DDD = Julian day-of-year (001-366)
    """
    jday = dt.timetuple().tm_yday
    return f"{PRODUCT}/{dt.year}/{jday:03d}/{dt.hour:02d}/"


def list_files(dt: datetime, max_results: int = 5) -> list:
    client = ContainerClient(
        account_url=ACCOUNT_URL,
        container_name=CONTAINER,
        credential=None,
    )
    prefix = get_blob_prefix(dt)
    log.info("Querying: %s/%s/%s", ACCOUNT_URL, CONTAINER, prefix)
    blobs = list(client.list_blobs(name_starts_with=prefix))
    blobs.sort(key=lambda b: b.last_modified, reverse=True)
    return blobs[:max_results]


def download(blob_name: str) -> str:
    local_path = os.path.join(STAGING_DIR, os.path.basename(blob_name))
    if os.path.exists(local_path):
        log.info("Already cached: %s", os.path.basename(blob_name))
        return local_path
    client = ContainerClient(
        account_url=ACCOUNT_URL,
        container_name=CONTAINER,
        credential=None,
    )
    log.info("Downloading: %s", os.path.basename(blob_name))
    with open(local_path, "wb") as f:
        f.write(client.get_blob_client(blob_name).download_blob().readall())
    size_mb = os.path.getsize(local_path) / 1024 / 1024
    log.info("Saved %.1f MB → %s", size_mb, local_path)
    return local_path


def decode_filename(filename: str) -> dict:
    """
    GOES-16 filename format:
    OR_ABI-L2-MCMIPC-M6_G16_s20261541430000_e20261541439000_c20261541440000.nc
    s = scan start (sYYYYJJJHHMMSSs), e = scan end, c = file created
    """
    base   = os.path.basename(filename).replace(".nc", "")
    parts  = base.split("_")
    result = {}
    try:
        result["platform"] = parts[2]
        result["start"]    = datetime.strptime(parts[3][1:14], "%Y%j%H%M%S").strftime("%Y-%m-%d %H:%M:%S UTC")
        result["end"]      = datetime.strptime(parts[4][1:14], "%Y%j%H%M%S").strftime("%Y-%m-%d %H:%M:%S UTC")
        result["created"]  = datetime.strptime(parts[5][1:14], "%Y%j%H%M%S").strftime("%Y-%m-%d %H:%M:%S UTC")
    except (IndexError, ValueError) as e:
        log.warning("Filename parse error: %s", e)
    return result


def inspect(filepath: str) -> dict:
    ds  = nc.Dataset(filepath, "r")
    info = {
        "platform":  getattr(ds, "platform_ID",        "unknown"),
        "orbital":   getattr(ds, "orbital_slot",        "unknown"),
        "scene":     getattr(ds, "scene_id",            "unknown"),
        "start":     getattr(ds, "time_coverage_start", "unknown"),
        "variables": sorted(ds.variables.keys()),
        "qc_pass":   True,
        "qc_issues": [],
    }

    # QC 1: data quality flag - need >= 80% good pixels
    for v in [x for x in ds.variables if x.startswith("DQF")]:
        dqf      = ds.variables[v][:]
        pct_good = round(int(np.sum(dqf == 0)) / dqf.size * 100, 1)
        info[f"{v}_pct_good"] = pct_good
        if pct_good < 80.0:
            info["qc_pass"] = False
            info["qc_issues"].append(f"{v}: {pct_good}% good pixels (min 80%)")

    # QC 2: IR brightness temp must be physically plausible
    if "CMI_C13" in ds.variables:
        ir = ds.variables["CMI_C13"][:]
        info["ir_min_K"]  = round(float(ir.min()),  1)
        info["ir_max_K"]  = round(float(ir.max()),  1)
        info["ir_mean_K"] = round(float(ir.mean()), 1)
        if ir.min() < 150 or ir.max() > 340:
            info["qc_pass"] = False
            info["qc_issues"].append(f"CMI_C13 out of range: {ir.min():.1f}-{ir.max():.1f}K")

    ds.close()
    return info


def main():
    now = datetime.now(timezone.utc)
    log.info("=" * 55)
    log.info("GOES-16 Ingest  —  %s", now.strftime("%Y-%m-%d %H:00 UTC"))
    log.info("=" * 55)

    blobs = list_files(now)
    if not blobs:
        log.error("No files found. Try a different hour.")
        sys.exit(1)

    log.info("Found %d file(s):", len(blobs))
    for b in blobs:
        log.info("  %s  (%.1f MB)", os.path.basename(b.name), b.size / 1024 / 1024)

    local = download(blobs[0].name)

    meta = decode_filename(local)
    log.info("Platform: %s | Scan: %s → %s",
             meta.get("platform"), meta.get("start"), meta.get("end"))

    info = inspect(local)
    log.info("Variables: %s", info["variables"])
    if "ir_min_K" in info:
        log.info("IR temp: %sK – %sK (mean %sK)",
                 info["ir_min_K"], info["ir_max_K"], info["ir_mean_K"])
    for k, v in info.items():
        if "pct_good" in k:
            log.info("%s: %s%%", k, v)

    if info["qc_pass"]:
        log.info("QC PASS — file valid.")
    else:
        log.warning("QC FAIL:")
        for issue in info["qc_issues"]:
            log.warning("  - %s", issue)


if __name__ == "__main__":
    main()
