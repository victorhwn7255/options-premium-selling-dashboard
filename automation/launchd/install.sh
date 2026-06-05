#!/bin/zsh
# Install/refresh the launchd job. Run:  zsh automation/launchd/install.sh
set -e
HERE="${0:A:h}"
PLIST="com.optionharvest.history.plist"
SRC="$HERE/$PLIST"
DEST="$HOME/Library/LaunchAgents/$PLIST"

# Build the signed wrapper app the plist points at (gives the job its
# "Theta Harvest" name + icon in Login Items & Extensions).
zsh "$HERE/build_app.sh"

cp "$SRC" "$DEST"
launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"
echo "Installed + loaded: $DEST"
echo ""
echo "⚠️  Grant Full Disk Access to ThetaHarvest.app (one-time — it is now the responsible"
echo "    process for reaching the repo under ~/Downloads):"
echo "    System Settings → Privacy & Security → Full Disk Access → + →"
echo "    $HERE/ThetaHarvest.app"
echo ""
echo "Status:  launchctl list | grep optionharvest"
echo "Run now: launchctl start com.optionharvest.history   (only after granting FDA)"
echo "Logs:    automation/logs/launchd.out  /  launchd.err"
echo "Uninstall: launchctl unload \"$DEST\" && rm \"$DEST\""
