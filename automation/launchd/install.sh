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
echo "ℹ️  Full Disk Access is NOT required — the repo lives under ~/Projects, which is not a"
echo "    TCC-protected folder. (FDA would only be needed if the repo were moved back under a"
echo "    protected folder like ~/Downloads, ~/Desktop, or ~/Documents.)"
echo ""
echo "Status:  launchctl list | grep optionharvest"
echo "Run now: launchctl start com.optionharvest.history"
echo "Logs:    automation/logs/launchd.out  /  launchd.err"
echo "Uninstall: launchctl unload \"$DEST\" && rm \"$DEST\""
