#!/bin/bash
# Startet die Website (Next.js) auf 127.0.0.1:3847, falls sie nicht läuft.
# Aufruf per Cron alle 5 Minuten (Watchdog) und nach Deploy mit "neustart".
PORT=3847
DIR=/home/dies_das_duesseldorfadmin/dda/web
LOG=/home/dies_das_duesseldorfadmin/dda/logs/website.log
PIDDATEI=/home/dies_das_duesseldorfadmin/dda/logs/website.pid
export NODE_OPTIONS="--require /home/dies_das_duesseldorfadmin/bin/jail-shim.cjs"
export NEXT_TELEMETRY_DISABLED=1 NODE_ENV=production

laeuft() { curl -s -o /dev/null -m 5 "http://127.0.0.1:$PORT/"; }

if [ "$1" = "neustart" ]; then
  [ -f "$PIDDATEI" ] && kill "$(cat "$PIDDATEI")" 2>/dev/null && sleep 3
elif laeuft; then
  exit 0
fi

cd "$DIR" || exit 1
echo "$(date "+%F %T") Website wird gestartet" >> "$LOG"
./node_modules/.bin/next start -H 127.0.0.1 -p $PORT >> "$LOG" 2>&1 < /dev/null &
echo $! > "$PIDDATEI"
disown
