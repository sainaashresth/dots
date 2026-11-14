#!/bin/sh
# Screenshot tool: grim + slurp, matching the rice (cyan #33ccff, dark pill).
#
#   screenshot.sh area   -> drag-select a region (default)
#   screenshot.sh full   -> whole screen
#
# Every shot is saved under ~/Pictures/Screenshots AND copied to the clipboard,
# so you can paste images straight into apps. Wired to:
#   PRINT        = area select
#   SHIFT+PRINT  = full screen

set -u
mode=${1:-area}
case "$mode" in area|full) ;; *) mode=area ;; esac

mkdir -p "$HOME/Pictures/Screenshots"
out="$HOME/Pictures/Screenshots/shot-$(date +%Y%m%d-%H%M%S).png"

# Toast, only if libnotify is installed (cosmetic; shots work without it).
blob() {
    command -v notify-send >/dev/null 2>&1 || return 0
    notify-send -a screenshot "$1"
}

if [ "$mode" = full ]; then
    # plain grim captures every connected output.
    grim "$out" >/dev/null 2>&1 || { blob "screenshot failed"; exit 1; }
else
    # slurp style options: translucent dark backdrop, cyan selector.
    geom=$(slurp -b 1b1b1f40 -c 33ccff -w 2 -d) || exit 0   # Esc = cancel
    [ -n "$geom" ] || exit 0
    grim -g "$geom" "$out" >/dev/null 2>&1 || { blob "screenshot failed"; exit 1; }
fi
wl-copy -t image/png < "$out"
blob "screenshot saved (copied to clipboard): $(basename "$out")"
