#!/bin/sh
# Fuzzel clipboard-history picker, wired to SUPER+SHIFT+V (copy mode) and
# SUPER+SHIFT+X (delete mode — removes the selected entry from the history).
#
# Depends on: cliphist (history daemon), wl-clipboard (wl-paste/wl-copy),
# fuzzel. The daemon side is started by the "hyprland.start" autostart block
# in hyprland.lua (`wl-paste --watch cliphist store`).
#
# Why the guards: Hyprland's exec cannot run [ ]-style shell tests, but inside
# a real /bin/sh script they are fine.

# copy (default): selecting an entry puts it back on the clipboard.
# delete        : selecting an entry removes it from the history.
mode=${1:-copy}
case "$mode" in copy|delete) ;; *) mode=copy ;; esac

# Tell the user loudly if dependencies are missing, instead of failing silently.
command -v wl-copy  >/dev/null 2>&1 && command -v wl-paste >/dev/null 2>&1 && command -v cliphist >/dev/null 2>&1 || {
    printf 'wl-clipboard and cliphist are required (pacman -S wl-clipboard cliphist)' |
        fuzzel --dmenu --prompt="clipboard: " -w 70 >/dev/null 2>&1
    exit 1
}

# Offer the stored history in fuzzel; dmenu mode keeps only one line.
#
# Appearance: matches fuzzel.ini's palette (JetBrainsMono Nerd Font, dark
# #1b1b1f capsule, #33ccff border) but tuned for a history list — wider,
# taller, rounded, roomier padding, and the cyan kept for prompt+border.
if [ "$mode" = delete ]; then
    prompt="delete: "
    placeholder="type to filter, enter removes the selected entry…"
else
    prompt="clipboard: "
    placeholder="start typing to filter your copies…"
fi
choice=$(cliphist list |
    fuzzel --dmenu --prompt="$prompt" \
        --font="JetBrainsMono Nerd Font:size=10" \
        --width=34 --lines=8 \
        --border-width=2 --border-radius=14 --border-color=33ccff66 \
        --background=1b1b1ff0 --text-color=cdd6f4ff \
        --prompt-color=33ccffff --match-color=33ccffff \
        --selection-color=33ccff33 --selection-text-color=ffffffff \
        --horizontal-pad=18 --vertical-pad=10 --inner-pad=5 \
        --placeholder="$placeholder")
[ -n "$choice" ] || exit 0

# cliphist expects the exact list line back to identify the matching entry.
if [ "$mode" = delete ]; then
    printf '%s' "$choice" | cliphist delete
else
    printf '%s' "$choice" | cliphist decode | wl-copy
fi
