# System Integration Test Plan
## NOAA Pipeline Monitor — v1.0 to v1.1 Upgrade
**Document ID:** SIT-2026-001  
**System:** NOAA Pipeline Monitor  
**Test Environment:** QA  
**Test Type:** System Integration Test  
**Author:** D. Ahn  
**Date:** 2026-06-09  
**Status:** Draft  

---

## 1. Purpose & Scope

This SIT plan validates the upgrade of the NOAA Pipeline Monitor from v1.0
to v1.1 in the QA environment prior to production deployment.

**In scope:**
- check_latency.sh script functionality and exit code behavior
- Cron scheduling and log output
- Integration with upstream data staging directory
- Log file write behavior and timestamp accuracy

**Out of scope:**
- Network connectivity to NOAA S3 (tested separately)
- Azure blob ingest script (unchanged in v1.1)
- Production environment (covered by deployment runbook RB-2026-001)

---

## 2. Test Environment

| Component | Details |
|---|---|
| OS | Ubuntu 24.04 (WSL2) |
| Host | David-PC |
| Test user | dahn |
| Script path | ~/noaa-pipeline-monitor/monitor/check_latency.sh |
| Staging dir | ~/noaa-pipeline-monitor/data/staging/ |
| Log file | ~/noaa-pipeline-monitor/logs/latency.log |
| Cron schedule | */5 * * * * |

**Pre-test setup:**
```bash
# System Integration Test Plan
## NOAA Pipeline Monitor — v1.0 to v1.1 Upgrade
**Document ID:** SIT-2026-001  
**System:** NOAA Pipeline Monitor  
**Test Environment:** QA  
**Test Type:** System Integration Test  
**Author:** D. Ahn  
**Date:** 2026-06-09  
**Status:** Draft  

---

## 1. Purpose & Scope

This SIT plan validates the upgrade of the NOAA Pipeline Monitor from v1.0
to v1.1 in the QA environment prior to production deployment.

**In scope:**
- check_latency.sh script functionality and exit code behavior
- Cron scheduling and log output
- Integration with upstream data staging directory
- Log file write behavior and timestamp accuracy

**Out of scope:**
- Network connectivity to NOAA S3 (tested separately)
- Azure blob ingest script (unchanged in v1.1)
- Production environment (covered by deployment runbook RB-2026-001)

---

## 2. Test Environment

| Component | Details |
|---|---|
| OS | Ubuntu 24.04 (WSL2) |
| Host | David-PC |
| Test user | dahn |
| Script path | ~/noaa-pipeline-monitor/monitor/check_latency.sh |
| Staging dir | ~/noaa-pipeline-monitor/data/staging/ |
| Log file | ~/noaa-pipeline-monitor/logs/latency.log |
| Cron schedule | */5 * * * * |

**Pre-test setup:**
```bash
# Confirm script version
head -3 ~/noaa-pipeline-monitor/monitor/check_latency.sh

# Confirm test file exists in staging
ls -lh ~/noaa-pipeline-monitor/data/staging/

# Confirm log file is writable
touch ~/noaa-pipeline-monitor/logs/latency.log && echo "Log writable"
```

---

## 3. Test Cases

---

### TC-01: OK status — file within warning threshold

**Objective:** Verify script returns OK and exit code 0 when newest file
is within the warning threshold.

**Pre-condition:** At least one .nc file exists in staging directory.

**Steps:**
```bash
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -d ~/noaa-pipeline-monitor/data/staging \
  -w 99999 -c 999999 -p "*.nc" \
  -l ~/noaa-pipeline-monitor/logs/latency.log
echo "Exit code: $?"
```

**Expected result:**
- Output contains `OK:`
- Exit code = 0
- Log file contains new timestamped OK entry

**Actual result:** OK: latest=real_goes16_ABI_L1b.nc | age=8486min | thresholds=99999/999999min — Exit 0_______________  
**Pass / Fail:** **Pass**
**Tested by:** dahn
**Date/Time:** 6/9/2026 7:17PM EST

---

### TC-02: WARNING status — file age exceeds warn threshold

**Objective:** Verify script returns WARNING and exit code 1 when file
age exceeds warning but not critical threshold.

**Pre-condition:** Staging directory contains a file older than 0 minutes.

**Steps:**
```bash
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -d ~/noaa-pipeline-monitor/data/staging \
  -w 0 -c 999999 -p "*.nc" \
  -l ~/noaa-pipeline-monitor/logs/latency.log
echo "Exit code: $?"
```

**Expected result:**
- Output contains `WARNING:`
- Exit code = 1
- Log file contains new timestamped WARNING entry

**Actual result:** WARNING: latest=real_goes16_ABI_L1b.nc | age=8486min | thresholds=0/999999min — Exit 1
**Pass / Fail:** **Pass**
**Tested by:** dahn
**Date/Time:** 6/9/2026 7:18PM EST

---

### TC-03: CRITICAL status — file age exceeds critical threshold

**Objective:** Verify script returns CRITICAL and exit code 2 when file
age exceeds critical threshold.

**Pre-condition:** Staging directory contains a file older than 0 minutes.

**Steps:**
```bash
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -d ~/noaa-pipeline-monitor/data/staging \
  -w 0 -c 0 -p "*.nc" \
  -l ~/noaa-pipeline-monitor/logs/latency.log
echo "Exit code: $?"
```

**Expected result:**
- Output contains `CRITICAL:`
- Exit code = 2
- Log file contains new timestamped CRITICAL entry

**Actual result:** CRITICAL: latest=real_goes16_ABI_L1b.nc | age=8486min | thresholds=0/0min — Exit 2
**Pass / Fail:** **Pass**
**Tested by:** dahn
**Date/Time:** 6/9/2026 7:18PM EST

---

### TC-04: CRITICAL status — no files found

**Objective:** Verify script correctly handles empty directory condition.

**Pre-condition:** Target directory exists but contains no .nc files.

**Steps:**
```bash
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -d /tmp \
  -w 15 -c 30 -p "*.nc" \
  -l ~/noaa-pipeline-monitor/logs/latency.log
echo "Exit code: $?"
```

**Expected result:**
- Output contains `CRITICAL: No files matching`
- Exit code = 2
- Log file contains new timestamped CRITICAL entry

**Actual result:** CRITICAL: No files matching '*.nc' found in /tmp — Exit 2
**Pass / Fail:** **Pass**
**Tested by:** dahn
**Date/Time:** 6/9/2026 7:18PM EST

---

### TC-05: UNKNOWN status — missing required argument

**Objective:** Verify script handles missing -d argument gracefully.

**Steps:**
```bash
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -w 15 -c 30 -p "*.nc"
echo "Exit code: $?"
```

**Expected result:**
- Output contains `UNKNOWN:`
- Exit code = 3
- No log entry written (log path not provided)

**Actual result:** UNKNOWN: -d directory is required — Exit 3
**Pass / Fail:** **Pass**
**Tested by:** dahn
**Date/Time:** 6/9/2026 7:18PM EST

---

### TC-06: UNKNOWN status — directory does not exist

**Objective:** Verify script handles nonexistent directory gracefully.

**Steps:**
```bash
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -d /nonexistent/path \
  -w 15 -c 30 -p "*.nc"
echo "Exit code: $?"
```

**Expected result:**
- Output contains `UNKNOWN: directory not found`
- Exit code = 3

**Actual result:** UNKNOWN: directory not found: /nonexistent/path — Exit 3
**Pass / Fail:** **Pass**
**Tested by:** dahn
**Date/Time:** 6/9/2026 7:18PM EST

---

### TC-07: Cron integration — automated execution and logging

**Objective:** Verify cron executes the script on schedule and log entries
are written correctly with accurate timestamps.

**Pre-condition:** Cron job is active with */5 schedule.

**Steps:**
```bash
# Confirm cron entry exists
crontab -l | grep check_latency

# Wait for next 5-minute mark, then check log
tail -5 ~/noaa-pipeline-monitor/logs/latency.log

# Confirm timestamp in log matches current time within 1 minute
date
```

**Expected result:**
- Cron entry present
- New log entry appears within 5 minutes
- Log timestamp matches system time within 1 minute

**Actual result:** _______________  
**Pass / Fail:** _______________  
**Tested by:** _______________  
**Date/Time:** _______________  

---

## 4. Pass/Fail Criteria

**Overall pass criteria:** All 7 test cases must return Pass.

Any single Fail result blocks promotion to production until the defect
is resolved and the affected test case is re-executed and passes.

| Test Case | Result |
|---|---|
| TC-01 OK status | |
| TC-02 WARNING status | |
| TC-03 CRITICAL status | |
| TC-04 No files found | |
| TC-05 Missing argument | |
| TC-06 Bad directory | |
| TC-07 Cron integration | |
| **Overall** | |

---

## 5. Defect Tracking

| ID | TC | Description | Severity | Status |
|---|---|---|---|---|
| | | | | |

Defects logged in: [Jira / Redmine / Bugzilla ticket #______]

---

## 6. Sign-Off

Promotion to production is authorized only after all test cases pass
and both signatures are obtained.

| Role | Name | Signature | Date |
|---|---|---|---|
| Test executor | D. Ahn | | |
| System owner | | | |
