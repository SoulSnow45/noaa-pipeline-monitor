# noaa-pipeline-monitor

A hands-on simulation of operational NOAA satellite data pipeline monitoring,
built using real GOES-16 ABI data from NOAA's public S3 archive.

Demonstrates Tier 2 O&M skills directly mapped to an Application Support
Specialist role: data ingest, latency monitoring, NetCDF QC inspection,
automated scheduling, and operational logging.

---

## What this simulates

NOAA's GOES-16 satellite produces a new CONUS scan every 5-10 minutes, 24x7.
Operations teams must:

1. **Ingest** — pull new files from the distribution endpoint
2. **Monitor latency** — alert if files stop arriving within expected windows
3. **Validate** — inspect NetCDF structure and run QC checks
4. **Log** — maintain timestamped records for shift handoffs and auditing

This project implements each of those steps against a real NOAA L1b file.

---

## Project structure
