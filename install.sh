#!/usr/bin/env bash

# Install server.py as a launchd user agent (run at login, keep alive).
# Run once per machine; re-run after moving the repo or changing python3.

set -euo pipefail

label="dev.session-index-viewer"
repo_dir="$(cd "$(dirname "$0")" && pwd)"
plist_path="$HOME/Library/LaunchAgents/$label.plist"
log_path="$HOME/Library/Logs/session-index-viewer.log"
python3_bin="$(command -v python3)"
frontend_dir="$repo_dir/frontend"

# Build the React frontend so server.py can serve frontend/dist/.
# Falls back to the legacy sessions-index.html if the build is skipped,
# so this is best-effort: a missing toolchain warns but does not abort.
build_frontend() {
  if [[ ! -d "$frontend_dir" ]]; then
    echo "  frontend/ not found — using legacy single-file viewer"
    return 0
  fi
  local pkg_mgr
  if command -v bun >/dev/null 2>&1; then
    pkg_mgr="bun"
  elif command -v npm >/dev/null 2>&1; then
    pkg_mgr="npm"
  else
    echo "  warn: neither bun nor npm found — skipping frontend build"
    echo "  server will fall back to sessions-index.html"
    return 0
  fi
  echo "  building frontend with $pkg_mgr …"
  ( cd "$frontend_dir" && "$pkg_mgr" install --silent && "$pkg_mgr" run build )
}

build_frontend

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$plist_path" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$python3_bin</string>
    <string>$repo_dir/server.py</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$log_path</string>
  <key>StandardErrorPath</key>
  <string>$log_path</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$UID/$label" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$plist_path"

echo "Installed $label"
echo "  plist: $plist_path"
echo "  log:   $log_path"
echo "  url:   http://localhost:7333"
if [[ -f "$frontend_dir/dist/index.html" ]]; then
  echo "  ui:    frontend/dist (React build)"
else
  echo "  ui:    sessions-index.html (legacy)"
fi
