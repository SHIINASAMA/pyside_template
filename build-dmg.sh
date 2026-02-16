#!/bin/zsh
set -e

mkdir -p release

create-dmg \
  --filesystem APFS \
  --volname "${APP_NAME} Installer" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --app-drop-link 450 185 \
  "./release/${APP_NAME}Installer.dmg" ./build/${APP_NAME}.app
