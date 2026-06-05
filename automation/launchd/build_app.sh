#!/bin/zsh
# Build (or rebuild) Theta Harvest.app — the signed wrapper that makes the launchd
# history job appear as "Theta Harvest" (with the brand θ icon) in
# System Settings → Login Items & Extensions, instead of "Python Software Foundation".
#
# Run:  zsh automation/launchd/build_app.sh
# Called automatically by install.sh.
set -e

HERE="${0:A:h}"                 # absolute path of automation/launchd
APP="$HERE/ThetaHarvest.app"
PY="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

echo "Building $APP"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cp "$HERE/app/Info.plist" "$APP/Contents/Info.plist"

# The main executable is a Mach-O binary named "Theta Harvest": for ad-hoc-signed (free)
# background items, Login Items & Extensions shows the executable's FILENAME, so this is what
# makes the row read "Theta Harvest". (A custom icon would require a Developer ID signature or
# SMAppService; with ad-hoc signing the icon stays generic — see README.)
clang -O2 -Wall -o "$APP/Contents/MacOS/Theta Harvest" "$HERE/app/launcher.c"

"$PY" "$HERE/make_icon.py" "$APP/Contents/Resources/AppIcon.icns"

# Ad-hoc sign the bundle so macOS attributes the background item to THIS app
# (its CFBundleName + icon), not to the python.org signing identity.
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP" && echo "✅ signature OK (ad-hoc)"

echo "✅ Built $APP"
echo "   Display name : Theta Harvest  (from the executable filename, ad-hoc)"
echo "   Executable   : Contents/MacOS/Theta Harvest"
echo "   Icon         : Contents/Resources/AppIcon.icns  (shows only if Developer-ID signed)"
