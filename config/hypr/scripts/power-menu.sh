#!/usr/bin/env bash
# fuzzel power menu -- bound to SUPER+Escape in hyprland.lua
#
# Icons must come from breeze-dark: the plain "breeze" theme ships dark glyphs
# (max luminance 53/255) that are invisible on this dark menu.
#
# Entry format must be printf format strings. A bash $'Lock\0icon\x1f...'
# string silently loses the NUL byte and the menu ends up with no icons.

set -u

choice=$(
    {
        printf 'Lock\0icon\x1fsystem-lock-screen\n'
        printf 'Log out\0icon\x1fsystem-log-out\n'
        printf 'Suspend\0icon\x1fsystem-suspend\n'
        printf 'Restart\0icon\x1fsystem-reboot\n'
        printf 'Shut down\0icon\x1fsystem-shutdown\n'
    } | fuzzel --dmenu --icon-theme=breeze-dark --lines=5 --minimal-lines \
               --width=24 --prompt="  "
) || exit 0

# fuzzel prints nothing when dismissed with Escape.
[ -n "$choice" ] || exit 0

case "$choice" in
    Lock)        exec env TZ=Asia/Kathmandu gtklock ;;
    "Log out")   exec hyprctl dispatch 'hl.dsp.exit()' ;;
    Suspend)     exec systemctl suspend ;;
    Restart)     exec systemctl reboot ;;
    "Shut down") exec systemctl poweroff ;;
esac
