#!/bin/sh
# Reference-image popup: opens an image as a floating, PINNED-on-top window so
# you can draw/work underneath while keeping the picture visible.
#
# Usage:
#   reference.sh              -> fuzzel picker of images from ~/Downloads
#   reference.sh FILE         -> shows FILE directly
#
# The float comes from the "reference-image-float-pin" window rule in
# hyprland.lua (matches class pixie-ref). The pin is applied here because
# Hyprland's lua window_rule API has no pin field yet.
#
# Close the reference with q (swayimg's quit key).

IMG="${1:-}"
if [ -z "$IMG" ]; then
    command -v fuzzel >/dev/null 2>&1 || exit 1
    IMG=$(find "$HOME/Downloads" -maxdepth 1 -type f \
          \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.gif' \) |
          fuzzel --dmenu --prompt="reference: " \
              --font="JetBrainsMono Nerd Font:size=10" \
              --width=60 --lines=10 \
              --border-width=2 --border-radius=14 --border-color=33ccff66 \
              --background=1b1b1ff0 --prompt-color=33ccffff)
    [ -n "$IMG" ] || exit 0
fi
[ -f "$IMG" ] || exit 1

# Spawn detached so it survives this script. The "reference-image-float-pin"
# window rule in hyprland.lua (class pixie-ref_*) floats AND pins it on map.
swayimg --appid=pixie-ref --position=880,60 --size=420,520 "$IMG" >/dev/null 2>&1 &
