#!/usr/bin/env bash
# Music player control via MPRIS for g4music
PLAYER="com.github.neithern.g4music"
ACTION="$1"

case "$ACTION" in
    status)
        playerctl -p "$PLAYER" status 2>/dev/null || echo "stopped"
        ;;
    toggle)
        playerctl -p "$PLAYER" play-pause 2>/dev/null
        ;;
    previous)
        playerctl -p "$PLAYER" previous 2>/dev/null
        ;;
    next)
        playerctl -p "$PLAYER" next 2>/dev/null
        ;;
    track)
        playerctl -p "$PLAYER" metadata --format "{{ artist }} - {{ title }}" 2>/dev/null || echo ""
        ;;
esac
