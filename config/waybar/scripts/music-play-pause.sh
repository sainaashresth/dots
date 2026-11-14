#!/usr/bin/env bash
# Play/pause button for g4music
PLAYER="com.github.neithern.g4music"
STATUS=$(playerctl -p "$PLAYER" status 2>/dev/null)

if [ "$STATUS" = "Playing" ]; then
    echo "󰐊"  # pause icon
else
    echo "󰏤"  # play icon
fi
