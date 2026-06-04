#!/usr/bin/env bash
# =============================================================
# check_latency.sh — NOAA data pipeline latency monitor
# =============================================================
# Checks staging directory for fresh files and reports status.
# Exit codes follow Nagios/Xymon convention:
#   0 = OK       file within warn threshold
#   1 = WARNING  file age exceeds warn threshold
#   2 = CRITICAL file age exceeds crit threshold or no files
#   3 = UNKNOWN  bad arguments or unreadable directory
#
# Usage:
#   ./check_latency.sh -d /data/staging -w 15 -c 30 -p "*.nc"
#
# Cron (every 5 min):
#   */5 * * * * /path/to/check_latency.sh -d /data/staging -w 15 -c 30 -l /logs/latency.log
# =============================================================

set -euo pipefail

DIR=""
WARN_MIN=15
CRIT_MIN=30
PATTERN="*.nc"
LOG_FILE=""

usage() {
    echo "Usage: $0 -d DIRECTORY [-w WARN_MIN] [-c CRIT_MIN] [-p PATTERN] [-l LOG_FILE]"
    exit 3
}

while getopts "d:w:c:p:l:h" opt; do
    case $opt in
        d) DIR="$OPTARG" ;;
        w) WARN_MIN="$OPTARG" ;;
        c) CRIT_MIN="$OPTARG" ;;
        p) PATTERN="$OPTARG" ;;
        l) LOG_FILE="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

[[ -z "$DIR" ]]   && { echo "UNKNOWN: -d directory is required"; exit 3; }
[[ ! -d "$DIR" ]] && { echo "UNKNOWN: directory not found: $DIR"; exit 3; }

NOW=$(date '+%Y-%m-%d %H:%M:%S')
NOW_EPOCH=$(date +%s)

NEWEST=$(find "$DIR" -maxdepth 1 -name "$PATTERN" -printf "%T@ %p\n" 2>/dev/null \
         | sort -n | tail -1)

if [[ -z "$NEWEST" ]]; then
    MSG="CRITICAL: No files matching '$PATTERN' found in $DIR"
    echo "$MSG"
    [[ -n "$LOG_FILE" ]] && echo "[$NOW] $MSG" >> "$LOG_FILE"
    exit 2
fi

FILE_EPOCH=$(echo "$NEWEST" | awk '{print int($1)}')
FILE_NAME=$(echo  "$NEWEST" | awk '{print $2}' | xargs basename)
FILE_AGE_SEC=$(( NOW_EPOCH - FILE_EPOCH ))
FILE_AGE_MIN=$(( FILE_AGE_SEC / 60 ))

if   (( FILE_AGE_MIN >= CRIT_MIN )); then STATUS="CRITICAL"; EXIT=2
elif (( FILE_AGE_MIN >= WARN_MIN )); then STATUS="WARNING";  EXIT=1
else                                      STATUS="OK";        EXIT=0
fi

MSG="${STATUS}: latest=${FILE_NAME} | age=${FILE_AGE_MIN}min | thresholds=${WARN_MIN}/${CRIT_MIN}min | dir=${DIR}"
echo "$MSG"
[[ -n "$LOG_FILE" ]] && echo "[$NOW] $MSG" >> "$LOG_FILE"

exit $EXIT
