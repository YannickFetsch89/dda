#!/bin/bash
# Website (Next.js) auf 127.0.0.1:3847 – mit Selbstheilung.
#
# Next.js läuft in einer Schleife (Wächter-Schleife): Stürzt der Prozess ab (z.B. Speicher voll), startet
# die Schleife ihn nach 3 Sekunden neu – unabhängig vom Cron. (Ausfälle 2026-11: Prozess war per
# „heap out of memory“ abgestürzt, der Cron-Wächter hat ihn nicht neu gestartet → stundenlang 502.)
#
# Aufrufe:
#   website.sh            Wächter (z.B. per Cron alle 5 Min): startet, falls nichts läuft; hängt die
#                         Website (antwortet nicht), wird der Next-Prozess beendet und von der Schleife neu gestartet
#   website.sh neustart   nach Deploy: Schleife und Next-Prozess beenden, neu starten
#   website.sh stopp      alles beenden
PORT=3847
DIR=/home/dies_das_duesseldorfadmin/dda/web
LOGDIR=/home/dies_das_duesseldorfadmin/dda/logs
LOG=$LOGDIR/website.log
PIDDATEI=$LOGDIR/website.pid          # PID des Next-Prozesses
SCHLEIFE_PID=$LOGDIR/website-schleife.pid
# Speichergrenze für Node: lieber früh und sauber neu starten als den Server auszulasten
SPEICHER_MB=1536
LOG_MAX_BYTES=$((20 * 1024 * 1024))

export NODE_OPTIONS="--require /home/dies_das_duesseldorfadmin/bin/jail-shim.cjs --max-old-space-size=$SPEICHER_MB"
export NEXT_TELEMETRY_DISABLED=1 NODE_ENV=production

mkdir -p "$LOGDIR"

# Antwortet die Website? Zweiter Versuch nach 5 s, damit eine kurz ausgelastete Website nicht neu startet
laeuft() {
  curl -s -o /dev/null -m 15 "http://127.0.0.1:$PORT/robots.txt" && return 0
  sleep 5
  curl -s -o /dev/null -m 15 "http://127.0.0.1:$PORT/robots.txt"
}
# nohup gibt es im Jail evtl. nicht – dann reicht disown (wie bisher)
NOHUP=$(command -v nohup || true)
lebt() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }

log_rotieren() {
  if [ -f "$LOG" ] && [ "$(stat -c %s "$LOG" 2>/dev/null || echo 0)" -gt "$LOG_MAX_BYTES" ]; then
    mv -f "$LOG" "$LOG.1"
  fi
}

stoppen() {
  lebt "$SCHLEIFE_PID" && kill "$(cat "$SCHLEIFE_PID")" 2>/dev/null
  lebt "$PIDDATEI" && kill "$(cat "$PIDDATEI")" 2>/dev/null
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    lebt "$PIDDATEI" || break
    sleep 1
  done
  lebt "$PIDDATEI" && kill -9 "$(cat "$PIDDATEI")" 2>/dev/null
  rm -f "$SCHLEIFE_PID"
}

starten() {
  cd "$DIR" || exit 1
  log_rotieren
  # Schleife im Hintergrund: Next starten, auf Ende warten, neu starten
  $NOHUP bash -c '
    while true; do
      echo "$(date "+%F %T") Website wird gestartet" >> "'"$LOG"'"
      ./node_modules/.bin/next start -H 127.0.0.1 -p '"$PORT"' >> "'"$LOG"'" 2>&1 < /dev/null &
      echo $! > "'"$PIDDATEI"'"
      wait $!
      code=$?
      echo "$(date "+%F %T") Website beendet (Code $code) – Neustart in 3 s" >> "'"$LOG"'"
      sleep 3
    done
  ' > /dev/null 2>&1 < /dev/null &
  echo $! > "$SCHLEIFE_PID"
  disown
}

case "$1" in
  neustart)
    stoppen
    starten
    ;;
  stopp)
    stoppen
    ;;
  *)
    # Wächter-Aufruf
    if laeuft; then
      log_rotieren
      exit 0
    fi
    if lebt "$SCHLEIFE_PID"; then
      # Schleife lebt, Website antwortet aber nicht: hängt → Next beenden, Schleife startet neu
      echo "$(date "+%F %T") Wächter: Website antwortet nicht – Next-Prozess wird neu gestartet" >> "$LOG"
      lebt "$PIDDATEI" && kill -9 "$(cat "$PIDDATEI")" 2>/dev/null
    else
      echo "$(date "+%F %T") Wächter: keine Schleife aktiv – starte" >> "$LOG"
      stoppen
      starten
    fi
    ;;
esac
