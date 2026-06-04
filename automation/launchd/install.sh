#!/bin/zsh
# Install/refresh the launchd job. Run:  zsh automation/launchd/install.sh
set -e
PLIST="com.optionharvest.history.plist"
SRC="/Users/victor_he/Downloads/Code/option-harvest/automation/launchd/$PLIST"
DEST="$HOME/Library/LaunchAgents/$PLIST"

cp "$SRC" "$DEST"
launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"
echo "Installed + loaded: $DEST"
echo "Status:  launchctl list | grep optionharvest"
echo "Run now: launchctl start com.optionharvest.history"
echo "Logs:    automation/logs/launchd.out  /  launchd.err"
echo "Uninstall: launchctl unload \"$DEST\" && rm \"$DEST\""
