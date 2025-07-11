#!/bin/bash
set -e

TLDR_DIR="$(pwd)/tldr_reddit"
PROFILER_DIR="$(pwd)/reddit_profiler"
SYSTEMD_USER="$HOME/.config/systemd/user"

for DIR in "$TLDR_DIR" "$PROFILER_DIR"; do
  if [ ! -d "$DIR/.venv" ]; then
    echo "Création du venv dans $DIR"
    python3 -m venv "$DIR/.venv"
    source "$DIR/.venv/bin/activate"
    if [ -f "$DIR/requirements.txt" ]; then
      python3 -m pip install --upgrade pip
      python3 -m pip install -r "$DIR/requirements.txt"
    fi
    deactivate
  fi
  echo "Venv OK pour $DIR"
done

cat > tldr-reddit.service <<EOF
[Unit]
Description=TLDR Reddit Flask Backend

[Service]
WorkingDirectory=$TLDR_DIR
ExecStart=$TLDR_DIR/.venv/bin/python3 $TLDR_DIR/app.py
Restart=always

[Install]
WantedBy=default.target
EOF

cat > reddit-profiler.service <<EOF
[Unit]
Description=Reddit Profiler Flask Backend

[Service]
WorkingDirectory=$PROFILER_DIR
ExecStart=$PROFILER_DIR/.venv/bin/python3 $PROFILER_DIR/app.py
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user stop tldr-reddit.service || true
systemctl --user stop reddit-profiler.service || true

mkdir -p "$SYSTEMD_USER"
cp tldr-reddit.service "$SYSTEMD_USER/tldr-reddit.service"
cp reddit-profiler.service "$SYSTEMD_USER/reddit-profiler.service"

chmod 644 "$SYSTEMD_USER/tldr-reddit.service" "$SYSTEMD_USER/reddit-profiler.service"

systemctl --user daemon-reload
systemctl --user enable --now tldr-reddit.service
systemctl --user enable --now reddit-profiler.service

echo "Services lancés !"
