#!/usr/bin/env python3
"""Hide Waybar when a single window sits on the active workspace.

Rationale: when you are just working in one full-screen-ish app, the bar is
dead weight.  This script watches Hyprland's event socket and hides the bar
after HIDE_AFTER seconds of "one window on the focused workspace" (windows
that are mapped and not hidden).  Any window/workspace/focus change brings it
back immediately, and while hidden the bar reappears when the pointer touches
the top edge of the screen.

Waybar toggles visibility on SIGUSR1 and releases its reserved space while
hidden, so the focused window really does gain the pixels.

Tunables:
    WAYBAR_AUTOHIDE_SECONDS   idle time before hiding (default 30)

The script is single-instance (flock) and restores the bar on exit.
"""

import errno
import fcntl
import json
import os
import select
import signal
import socket
import subprocess
import sys
import time

HIDE_AFTER = float(os.environ.get("WAYBAR_AUTOHIDE_SECONDS", "30"))
EDGE_Y = 2            # pointer this close to the top edge reveals the bar
POLL = 0.35           # seconds between cursor checks while hidden
DEBUG = os.environ.get("WAYBAR_AUTOHIDE_DEBUG") == "1"


def log(*args):
    if DEBUG:
        print("%s" % time.strftime("%H:%M:%S"), *args, file=sys.stderr, flush=True)

# Hyprland events that mean "the workspace/layout changed".  Window title
# changes are deliberately excluded: terminals retitle constantly and the bar
# would never stay hidden.
EVENTS = {
    b"openwindow", b"closewindow", b"movewindow", b"activewindow",
    b"activewindowv2", b"workspace", b"createworkspace",
    b"destroyworkspace", b"renameworkspace", b"moveworkspace",
    b"focusedmon", b"urgent", b"fullscreen", b"changefloatingmode",
    b"activespecial", b"movewindowv2",
}


def hypr_json(*args):
    """Run `hyprctl <args> -j` and return parsed JSON, or None."""
    try:
        out = subprocess.run(
            ("hyprctl", *args, "-j"),
            capture_output=True, text=True, timeout=2,
        ).stdout
        return json.loads(out) if out.strip() else None
    except Exception:
        return None


def cursor_y():
    """Pointer y coordinate, or None if unavailable."""
    try:
        out = subprocess.run(
            ("hyprctl", "cursorpos"),
            capture_output=True, text=True, timeout=2,
        ).stdout.strip()
        return int(out.split(",")[1])
    except Exception:
        return None


def find_waybar(cached=None):
    """PID of the running Waybar process, or None.

    The previously found pid is re-checked first (one tiny read) so the full
    /proc scan only happens when Waybar actually started or restarted.
    """
    if cached:
        try:
            with open("/proc/%d/comm" % cached) as f:
                if f.read().strip() == "waybar":
                    return cached
        except OSError:
            pass
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open("/proc/%s/comm" % entry) as f:
                if f.read().strip() == "waybar":
                    return int(entry)
        except OSError:
            continue
    return None


def window_count():
    """Visible windows on the focused workspace, or None if unknown."""
    ws = hypr_json("activeworkspace")
    clients = hypr_json("clients")
    if not ws or clients is None:
        return None
    ws_id = ws.get("id")
    return sum(
        1 for c in clients
        if c.get("mapped") and not c.get("hidden")
        and (c.get("workspace") or {}).get("id") == ws_id
    )


def socket_path():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    runtime = os.environ.get("XDG_RUNTIME_DIR", "/run/user/%d" % os.getuid())
    return os.path.join(runtime, "hypr", sig, ".socket2.sock")


class AutoHide:
    def __init__(self):
        self.visible = True
        self.pid = None
        self.count = None
        self.since = None       # start of the current one-window idle period
        self.prev_y = None      # pointer y at the previous hidden poll

    # -- visibility -----------------------------------------------------
    def hide(self):
        if not self.visible or not self.pid:
            return
        try:
            os.kill(self.pid, signal.SIGUSR1)
        except OSError:
            return
        self.visible = False
        self.since = None
        self.prev_y = cursor_y()
        log("hide  pid=%s count=%s" % (self.pid, self.count))

    def show(self):
        if not self.pid:
            return
        if self.visible:
            return
        try:
            os.kill(self.pid, signal.SIGUSR1)
        except OSError:
            return
        self.visible = True
        self.prev_y = None
        self.since = time.monotonic() if self.count == 1 else None
        log("show  pid=%s count=%s" % (self.pid, self.count))

    # -- state ----------------------------------------------------------
    def refresh(self):
        """Recompute the window count; called on Hyprland events."""
        # A restarted bar always starts visible.
        pid = find_waybar(self.pid)
        if pid != self.pid:
            self.pid = pid
            self.visible = True
            self.prev_y = None

        count = window_count()
        if count is None:
            return
        self.count = count

        # Any real layout/focus change brings the bar back.
        self.show()
        if count == 1:
            self.since = time.monotonic()
        else:
            self.since = None
        log("refresh count=%s visible=%s pid=%s" % (count, self.visible, self.pid))

    def tick(self):
        """Periodic work: bar restarts, hide timer, edge reveal."""
        pid = find_waybar(self.pid)
        if pid != self.pid:
            log("bar pid changed %s -> %s" % (self.pid, pid))
            self.pid = pid
            self.visible = True
            self.prev_y = None
            self.since = None
            # Re-sync the timer with the current workspace state, e.g. when
            # this script started before Waybar did.
            if pid is not None:
                self.refresh()
                return

        if self.visible:
            if self.since is not None and time.monotonic() - self.since >= HIDE_AFTER:
                self.hide()
            return

        # Hidden: reveal when the pointer arrives at the top edge.
        y = cursor_y()
        if y is not None:
            if (self.prev_y is not None and self.prev_y > EDGE_Y and y <= EDGE_Y):
                self.show()
            self.prev_y = y


def main():
    # Single instance: a stray SIGUSR1 pair from two copies would fight.
    lock_path = os.path.join(
        os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "waybar-autohide.lock")
    lock = open(lock_path, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
        if e.errno in (errno.EACCES, errno.EAGAIN):
            return
        raise

    state = AutoHide()

    def cleanup(signum, frame):
        state.show()
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    state.refresh()

    failures = 0            # consecutive failed connects
    last_refresh = 0.0
    pending = False         # an event arrived inside the debounce window

    while True:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(1.0)
            sock.connect(socket_path())
        except OSError:
            sock.close()
            failures += 1
            # The socket path is tied to this Hyprland instance. If it is gone
            # for good, the session ended: restore the bar and exit so we do not
            # linger as an orphan holding the lock (which would stop the next
            # session's copy from starting).
            if failures >= 15 and not os.path.exists(socket_path()):
                state.show()
                return
            time.sleep(1)
            continue
        failures = 0

        buf = b""
        try:
            while True:
                try:
                    ready, _, _ = select.select([sock], [], [], POLL)
                except OSError:
                    break

                if ready:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    buf += chunk
                    *lines, buf = buf.split(b"\n")
                    names = {
                        line.split(b">>", 1)[0]
                        for line in lines if line
                    }
                    if names & EVENTS:
                        pending = True

                # Debounce: each refresh spawns two hyprctl processes, so a
                # burst of events is collapsed into one refresh per 0.25 s.
                now = time.monotonic()
                if pending and now - last_refresh >= 0.25:
                    pending = False
                    last_refresh = now
                    state.refresh()

                state.tick()
        except Exception:
            pass
        finally:
            try:
                sock.close()
            except OSError:
                pass
        time.sleep(0.5)


if __name__ == "__main__":
    main()
