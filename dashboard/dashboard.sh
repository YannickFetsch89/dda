#!/bin/bash
# Startet das Dashboard (Streamlit) auf 127.0.0.1:8502, falls es nicht läuft.
# Aufruf per Cron (Watchdog) und nach Deploy mit "neustart".
# Im Jail gibt es kein pkill/ps, daher merken wir uns die PID in einer Datei.
PORT=8502
DIR=/home/dies_das_duesseldorfadmin/dda
LOG=$DIR/logs/dashboard.log
PIDDATEI=$DIR/logs/dashboard.pid
export LD_LIBRARY_PATH="/home/dies_das_duesseldorfadmin/.local/lib:$LD_LIBRARY_PATH"

laeuft() { curl -s -o /dev/null -m 5 "http://127.0.0.1:$PORT/_stcore/health"; }

if [ "$1" = "neustart" ]; then
  if [ -f "$PIDDATEI" ] && kill "$(cat "$PIDDATEI")" 2>/dev/null; then
    # warten, bis der Port frei ist
    for i in {1..10}; do laeuft || break; sleep 1; done
  fi
elif laeuft; then
  exit 0
fi

cd "$DIR" || exit 1
echo "$(date "+%F %T") Dashboard wird gestartet" >> "$LOG"
"$DIR/venv/bin/streamlit" run dashboard/app.py \
  --server.port $PORT \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false \
  >> "$LOG" 2>&1 < /dev/null &
echo $! > "$PIDDATEI"
disown
