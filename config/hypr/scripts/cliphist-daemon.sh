#!/bin/sh
# Clipboard history daemon (cliphist), started once per session from the
# hyprland.start autostart block.
#
# Why a wrapper: Hyprland's exec_cmd cannot evaluate pgrep guards reliably
# (args like -f 'pattern' get mangled), but inside a real /bin/sh script the
# single-instance guard below is safe.
#
# The daemon records every selection (text and images) into ~/.cache/cliphist/db
# so the SUPER+SHIFT+V / SUPER+SHIFT+X pickers have something to show.

# Single instance: real forked process name matching is exact.
pgrep -x wl-paste >/dev/null 2>&1 && exit 0

exec wl-paste --watch cliphist store
