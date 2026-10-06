#!/usr/bin/env bash
set -euo pipefail
# Run within dbus-run-session + xvfb-run on the hosted GitHub runner only.
export LANG=C.UTF-8 LC_ALL=C.UTF-8 QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
export QT_ACCESSIBILITY=1 QT_QPA_PLATFORM=xcb
export XDG_RUNTIME_DIR="${RUNNER_TEMP:?}/pattern-ferry-runtime"
mkdir -p "$XDG_RUNTIME_DIR" evidence ci-home/work
chmod 700 "$XDG_RUNTIME_DIR"
export HOME="$PWD/ci-home"
cat > "$HOME/.lmmsrc.xml" <<EOF
<?xml version="1.0"?>
<lmms version="1.3.0-alpha.2" configversion="3">
 <paths workingdir="$PWD/ci-home/work/"/>
 <audioengine audiodev="Dummy (no sound output)" mididev="Dummy"/>
 <app nommpz="1"/>
 <ui language="en" compacttrackbuttons="0"/>
</lmms>
EOF
openbox >evidence/openbox.log 2>&1 &
WM_PID=$!
"$PWD/.native/squashfs-root/AppRun" --geometry 1440x1000+0+0 "$PWD/evidence/source-input.mmp" >evidence/lmms.log 2>&1 &
APP_PID=$!
trap 'kill "$APP_PID" "$WM_PID" 2>/dev/null || true' EXIT
/usr/bin/python3 scripts/native_gate.py
/usr/bin/python3 scripts/oracle.py
