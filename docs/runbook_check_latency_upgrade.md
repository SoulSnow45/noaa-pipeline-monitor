# Deployment Runbook
## check_latency.sh — Version Upgrade
**Document ID:** RB-2026-001  
**System:** NOAA Pipeline Monitor  
**Change Type:** Script upgrade  
**Environment:** Production (WSL2 / Linux)  
**Estimated Duration:** 15 minutes  
**Rollback Time:** 5 minutes  
**Author:** D. Ahn  
**Last Updated:** 2026-06-09  

---

## 1. Pre-Conditions

Before beginning confirm all of the following:

- [ ] Change has been approved in the change management system (ticket #______)
- [ ] A backup of the current script exists (Step 3 below)
- [ ] The new script version has passed QA testing
- [ ] You have write access to `/home/dahn/noaa-pipeline-monitor/monitor/`
- [ ] A second engineer is available for verification (or on-call is notified)
- [ ] Maintenance window is active — notify stakeholders before proceeding

**Stop here if any pre-condition is not met.**

---

## 2. Contacts & Escalation

| Role | Name | Contact |
|---|---|---|
| Change owner | D. Ahn | dahn@example.com |
| On-call engineer | TBD | pagerduty/oncall |
| System owner | TBD | system-owner@example.com |

Escalation threshold: if any step fails or rollback is required, notify
the system owner immediately and do not proceed without guidance.

---

## 3. Pre-Deployment — Backup Current Version

```bash
# Step 3.1 — confirm current script version and capture checksum
md5sum ~/noaa-pipeline-monitor/monitor/check_latency.sh

# Step 3.2 — create timestamped backup
cp ~/noaa-pipeline-monitor/monitor/check_latency.sh \
   ~/noaa-pipeline-monitor/monitor/check_latency.sh.bak.$(date +%Y%m%d_%H%M%S)

# Step 3.3 — confirm backup exists
ls -lh ~/noaa-pipeline-monitor/monitor/

# Step 3.4 — suspend cron job to prevent execution during upgrade
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d).txt
crontab -r
crontab -l 2>&1 | grep "no crontab" && echo "Cron suspended OK"
```

**Expected output:** "no crontab for dahn" confirms cron is suspended.  
**If unexpected output:** Stop and investigate before proceeding.

---

## 4. Deployment — Install New Version

```bash
# Step 4.1 — copy new script into place
cp /path/to/new/check_latency.sh \
   ~/noaa-pipeline-monitor/monitor/check_latency.sh

# Step 4.2 — verify permissions are correct
chmod 755 ~/noaa-pipeline-monitor/monitor/check_latency.sh
ls -lh ~/noaa-pipeline-monitor/monitor/check_latency.sh

# Step 4.3 — verify checksum matches expected new version
md5sum ~/noaa-pipeline-monitor/monitor/check_latency.sh
# Compare against checksum provided in change ticket
```

**Expected output:** `-rwxr-xr-x` permissions, checksum matches ticket.  
**If unexpected:** Do not proceed — execute rollback (Section 6).

---

## 5. Post-Deployment Verification

```bash
# Step 5.1 — run manual smoke test (OK scenario)
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -d ~/noaa-pipeline-monitor/data/staging \
  -w 99999 -c 999999 -p "*.nc"
echo "Exit code: $?"

# Step 5.2 — run manual smoke test (CRITICAL scenario)
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -d /tmp -w 15 -c 30 -p "*.nc"
echo "Exit code: $?"

# Step 5.3 — restore cron job
crontab /tmp/crontab_backup_*.txt
crontab -l

# Step 5.4 — confirm next cron execution fires cleanly
tail -f ~/noaa-pipeline-monitor/logs/latency.log
# Wait for next 5-minute mark and confirm new log entry appears
```

**Expected results:**
- Step 5.1: prints OK, exit code 0
- Step 5.2: prints CRITICAL, exit code 2
- Step 5.3: crontab restored with original entry
- Step 5.4: new timestamped log entry appears within 5 minutes

**If any verification fails:** Execute rollback immediately (Section 6).

---

## 6. Rollback Procedure

Execute if any step in Sections 4 or 5 fails:

```bash
# Step R.1 — restore backed up script
cp ~/noaa-pipeline-monitor/monitor/check_latency.sh.bak.* \
   ~/noaa-pipeline-monitor/monitor/check_latency.sh

# Step R.2 — verify restored script checksum matches original
md5sum ~/noaa-pipeline-monitor/monitor/check_latency.sh
# Should match checksum captured in Step 3.1

# Step R.3 — restore cron job if suspended
crontab /tmp/crontab_backup_*.txt
crontab -l

# Step R.4 — verify system is operational
bash ~/noaa-pipeline-monitor/monitor/check_latency.sh \
  -d ~/noaa-pipeline-monitor/data/staging \
  -w 99999 -c 999999 -p "*.nc"
echo "Exit code: $?"

# Step R.5 — notify stakeholders of rollback
```

**Rollback complete when:** Exit code 0 confirmed and cron restored.  
**Notify:** System owner and on-call engineer immediately upon rollback.

---

## 7. Sign-Off

| Step | Completed by | Time | Notes |
|---|---|---|---|
| Pre-conditions verified | | | |
| Backup created | | | |
| New version installed | | | |
| Smoke tests passed | | | |
| Cron restored | | | |
| Log entry confirmed | | | |

**Deployment status:** [ ] Success  [ ] Rolled back  
**Completed by:** ________________  
**Completion time:** ________________  
**Ticket closed:** ________________
