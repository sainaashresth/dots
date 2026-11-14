#!/usr/bin/env python3
"""Waybar centre module: windows on the focused workspace.

The focused window is shown as its application glyph in the accent colour;
every other window on the workspace is a dim dot.  The script stays alive and
re-renders on Hyprland events (window opened/closed/focused, workspace switch),
so the bar updates immediately instead of waiting for a poll interval.
"""

import json
import os
import select
import socket
import subprocess
import sys
import time

ACCENT = "#33ccff"
DIM = "#6c7086"
DOT = "\u2022"          # small dot for unfocused windows
FALLBACK = "\uf2d0"     # circle-question, used for unknown applications

# Substring of the Hyprland window class -> Nerd Font glyph.
# Order matters: the first match wins.
GLYPHS = (
    ("foot", "\uf120"),
    ("alacritty", "\uf120"),
    ("kitty", "\uf120"),
    ("wezterm", "\uf120"),
    ("konsole", "\uf120"),
    ("terminal", "\uf120"),
    ("helium", "\uf0ac"),
    ("firefox", "\uf269"),
    ("chrom", "\uf0ac"),
    ("brave", "\uf0ac"),
    ("dolphin", "\uf07b"),
    ("nautilus", "\uf07b"),
    ("thunar", "\uf07b"),
    ("nemo", "\uf07b"),
    ("file", "\uf07b"),
    ("code", "\uf121"),
    ("codium", "\uf121"),
    ("mpv", "\uf03d"),
    ("vlc", "\uf03d"),
    ("spotify", "\uf001"),
    ("mpd", "\uf001"),
    ("music", "\uf001"),
)

# Events that can change what this module displays.
EVENTS = {
    b"openwindow", b"closewindow", b"movewindow", b"activewindow",
    b"activewindowv2", b"workspace", b"createworkspace",
    b"destroyworkspace", b"renameworkspace", b"moveworkspace",
    b"focusedmon", b"urgent", b"fullscreen", b"changefloatingmode",
    b"activespecial", b"windowtitle",
}


def hypr_json(*args):
    """Run `hyprctl <args> -j` and return the parsed JSON, or None."""
    try:
        out = subprocess.run(
            ("hyprctl", *args, "-j"),
            capture_output=True, text=True, timeout=2,
        ).stdout
        return json.loads(out) if out.strip() else None
    except Exception:
        return None


def glyph_for(window_class):
    cls = (window_class or "").lower()
    for needle, glyph in GLYPHS:
        if needle in cls:
            return glyph
    return FALLBACK


def render():
    """Return one line of Pango markup for the bar (empty if no windows)."""
    workspace = hypr_json("activeworkspace")
    clients = hypr_json("clients")
    if not workspace or not clients:
        return ""

    active = hypr_json("activewindow") or {}
    focused_address = active.get("address")
    workspace_id = workspace.get("id")

    windows = [
        c for c in clients
        if c.get("mapped") and not c.get("hidden")
        and (c.get("workspace") or {}).get("id") == workspace_id
    ]
    # Left-to-right tiled order keeps the dots from jumping around.
    windows.sort(key=lambda c: (c.get("at") or [0, 0])[0])

    parts = []
    for c in windows:
        if c.get("address") == focused_address:
            parts.append(
                '<span foreground="%s">%s</span>'
                % (ACCENT, glyph_for(c.get("class")))
            )
        else:
            parts.append('<span foreground="%s">%s</span>' % (DIM, DOT))
    return " ".join(parts)


def emit():
    sys.stdout.write(render() + "\n")
    sys.stdout.flush()


def socket_path():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    runtime = os.environ.get("XDG_RUNTIME_DIR", "/run/user/%d" % os.getuid())
    return os.path.join(runtime, "hypr", sig, ".socket2.sock")


def main():
    emit()

    # Follow Hyprland's event socket; fall back to a slow poll if it is not
    # available (e.g. the compositor restarted under a new signature).
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(socket_path())
    except OSError:
        while True:
            time.sleep(1)
            emit()

    buf = b""
    while True:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            continue
        except OSError:
            break
        if not chunk:
            break

        buf += chunk
        *lines, buf = buf.split(b"\n")
        names = {line.split(b">>", 1)[0] for line in lines if line}
        if not names & EVENTS:
            continue

        # A drag or resize can produce a burst of events; drain them and
        # render once.
        while select.select([sock], [], [], 0.04)[0]:
            try:
                more = sock.recv(4096)
            except OSError:
                break
            if not more:
                break
            buf += more

        emit()


if __name__ == "__main__":
    try:
        main()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
