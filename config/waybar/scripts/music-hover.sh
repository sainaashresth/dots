#!/usr/bin/env bash
# Helper for the waybar music drawer. Prints text only, changes nothing.
# usage: music-hover.sh title | state
case "${1:-}" in
  title)
    status=$(playerctl status 2>/dev/null) || { echo "Nothing playing"; exit 0; }
    text=$(playerctl metadata --format '{{ artist }} - {{ title }}' 2>/dev/null)
    text=${text# - }
    if [ -n "${text// /}" ]; then echo "$text"; else echo "$status"; fi
    ;;
  state)
    if [ "$(playerctl status 2>/dev/null)" = "Playing" ]; then
      echo "❚❚"
    else
      echo "▶"
    fi
    ;;
esac
exit 0
