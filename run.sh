#!/bin/bash
clear
echo "======================================"
echo "         🔥 DARKXPRIME 🔥"
echo "======================================"

# Auto update from GitHub before running
if [ -d .git ]; then
    echo "[UPDATER] Checking for updates..."
    git fetch origin
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "[UPDATER] Update found! Pulling latest changes..."
        git pull
    else
        echo "[UPDATER] Already up-to-date."
    fi
else
    echo "[UPDATER] Not a git repo! Please clone from GitHub."
fi

python main.py

