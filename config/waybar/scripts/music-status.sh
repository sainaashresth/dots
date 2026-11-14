#!/usr/bin/env bash
# Chip text for the single music module (JSON for waybar).
# Shows a music glyph, tooltip with track info, and a class for CSS colour.
PLAYER="com.github.neithern.g4music"

STATUS=$(playerctl -p "$PLAYER" status 2>/dev/null)
META=$(playerctl -p "$PLAYER" metadata --format '{{artist}} — {{title}}' 2>/dev/null)

case "$STATUS" in
    Playing)
        ICON="󰝚"
        CLASS="playing"
        STATE="▶ Playing"
        ;;
    Paused)
        ICON="󰝚"
        CLASS="paused"
        STATE="⏸ Paused"
        ;;
    Stopped)
        ICON="󰝚"
        CLASS="stopped"
        STATE="■ Stopped"
        ;;
    *)
        ICON="󰝚"
        CLASS="stopped"
        STATE="No player"
        META=""
        ;;
esac

[ -z "$META" ] && META="$STATE"

printf '{"text": "<span font_family=\\\"JetBrainsMono Nerd Font\\\">%s</span>", "tooltip": "%s", "class": "%s"}\n' \
    "$ICON" "$(printf '%s' "$META" | sed 's/"/\\\\"/g')" "$CLASS"
