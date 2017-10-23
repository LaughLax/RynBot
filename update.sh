#!/usr/bin/env bash

echo Waiting for bot to close...
tail --pid=$PPID -f /dev/null

echo Pulling git repo...
git pull

echo Starting bot...
python3 Bot_Main.py &
