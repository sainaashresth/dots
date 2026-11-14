#!/usr/bin/env python3
"""Airplay-style media popup for waybar's music chip (g4music / MPRIS).

- Anchors under the waybar chip (top, right) via gtk-layer-shell.
- Album art (if MPRIS provides artUrl), song title/artist, progress bar.
- Prev / play-pause / next buttons.
- Closes on ESC, the close button, or after the mouse leaves it.

Rules honored: this script never runs any power-related command.
"""
import os
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, GdkPixbuf

PLAYER = "com.github.neithern.g4music"


def run(*args):
    """Run a playerctl command, return stdout or None."""
    try:
        out = GLib.spawn_command_line_sync(
            f"playerctl -p {PLAYER} {args[0]}"
        )
        return out[1].decode().strip() if out[3] == 0 else None
    except GLib.Error:
        return None


class Popup(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_default_size(300, 140)
        self.set_decorated(False)
        self.set_resizable(False)
        self.art_path = None
        self.art_needed = False
        self.last_art = None
        self._leave_pending = False

        self.build_ui()
        self.apply_layer_shell()
        self.connect("key-press-event", self.on_key)
        self.show_all()

        self.tick()          # first fill immediately
        GLib.timeout_add(250, self.tick)   # progress + metadata refresh
        # Auto-close shortly after opening if the mouse never moves onto
        # the card (e.g. opened by click and immediately forgotten).
        GLib.timeout_add_seconds(8, self._close_if_still_out)

    # ---------- UI ----------
    def build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.set_margin_top(4)
        outer.set_margin_bottom(4)
        outer.set_margin_start(8)
        outer.set_margin_end(8)
        self.add(outer)

        # header row: app dot + close button
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        app = Gtk.Label(label="󰝚 Music")
        app.set_halign(Gtk.Align.START)
        close = Gtk.Button(label="✕")
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.get_style_context().add_class("close")
        close.set_halign(Gtk.Align.END)
        close.connect("clicked", lambda *_: Gtk.main_quit())
        head.pack_start(app, True, True, 0)
        head.pack_start(close, False, False, 0)
        outer.pack_start(head, False, False, 0)

        # main row: art | info
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.art = Gtk.Image()
        self.art.set_size_request(48, 48)
        row.pack_start(self.art, False, False, 0)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.title = Gtk.Label(label="No track")
        self.title.set_halign(Gtk.Align.START)
        self.title.get_style_context().add_class("title")
        self.artist = Gtk.Label(label="")
        self.artist.set_halign(Gtk.Align.START)
        self.artist.get_style_context().add_class("artist")
        info.pack_start(self.title, False, False, 0)
        info.pack_start(self.artist, False, False, 0)
        row.pack_start(info, True, True, 0)
        outer.pack_start(row, False, False, 0)

        # progress
        self.bar = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.bar.set_draw_value(False)
        self.bar.get_style_context().add_class("progress")
        self.bar.set_sensitive(False)
        outer.pack_start(self.bar, False, False, 0)

        # time labels
        self.times = Gtk.Label(label="--:-- / --:--")
        self.times.set_halign(Gtk.Align.CENTER)
        self.times.get_style_context().add_class("times")
        outer.pack_start(self.times, False, False, 0)

        # transport buttons
        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btns.set_halign(Gtk.Align.CENTER)
        self.prev = self.icon_button("󰒮", self.do_prev)
        self.play = self.icon_button("󰐊", self.do_toggle)
        self.next = self.icon_button("󰒭", self.do_next)
        btns.pack_start(self.prev, False, False, 0)
        btns.pack_start(self.play, False, False, 0)
        btns.pack_start(self.next, False, False, 0)
        outer.pack_start(btns, False, False, 0)

        # mouse leave -> auto close
        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)

        css = Gtk.CssProvider()
        css.load_from_data(b"""
        window { background: rgba(20, 20, 23, 0.96); border-radius: 14px;
                 border: 1px solid rgba(51, 204, 255, 0.45); }
        label.title { font-weight: 700; font-size: 13px; color: #cdd6f4; }
        label.artist { font-size: 11px; color: #9aa5b1; }
        label.times { font-size: 10px; color: #7f8a96; font-family: monospace; }
        button.close { color: #9aa5b1; font-size: 12px; padding: 0 4px; }
        button.media { color: #cdd6f4; }
        button.media:hover { color: #33ccff; }
        scale.progress trough { min-height: 3px; background: rgba(120,130,140,0.35); }
        scale.progress highlight { min-height: 3px; background: #33ccff; }
        scale.progress slider { opacity: 0; }
        """)
        self.get_style_context().add_provider(
            css, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def icon_button(self, glyph, cb):
        b = Gtk.Button()
        lbl = Gtk.Label(label=glyph)
        lbl.get_style_context().add_class("media")
        b.add(lbl)
        b.set_relief(Gtk.ReliefStyle.NONE)
        b.get_style_context().add_class("media")
        b.connect("clicked", cb)
        return b

    # ---------- layer shell ----------
    def apply_layer_shell(self):
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 36)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 8)
        GtkLayerShell.set_keyboard_mode(
            self, GtkLayerShell.KeyboardMode.ON_DEMAND)

    # ---------- actions ----------
    def _set_play_glyph(self, playing):
        """Show pause (󰐊) while playing, play (󰒯) when paused."""
        cur = self.play.get_child().get_text()
        want = "󰐊" if playing else "󰒯"
        if cur != want:
            self.play.get_child().set_text(want)

    def do_toggle(self, *_):
        run("toggle")
        self.tick()
        self.reset_auto_close()

    def do_next(self, *_):
        run("next")
        self.tick()
        self.reset_auto_close()

    def do_prev(self, *_):
        run("previous")
        self.tick()
        self.reset_auto_close()

    def on_key(self, _w, ev):
        if ev.keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            Gtk.main_quit()
        return False

    def on_enter(self, *_):
        self._leave_pending = False
        return False

    def on_leave(self, *_):
        self._leave_pending = True
        GLib.timeout_add_seconds(3, self._close_if_still_out)
        return False

    def _close_if_still_out(self):
        if self._leave_pending:
            Gtk.main_quit()
        return False

    def reset_auto_close(self):
        # restart the idle close timer after user interaction
        self._leave_pending = False
        self.on_leave(None)

    # ---------- refresh ----------
    def tick(self):
        status = run("status")
        title = run("metadata --format '{{title}}'")
        artist = run("metadata --format '{{artist}}'")
        art = run("metadata --format '{{mpris:artUrl}}'")
        length = run("metadata --format '{{mpris:length}}'")
        pos = run("position")
        rate = run("metadata --format '{{mpris:rate}}'") or "1"

        playing = status == "Playing"
        self._set_play_glyph(playing)

        if title:
            self.title.set_text(title)
        elif self.art_needed:
            pass
        else:
            self.title.set_text("No track")
            self.artist.set_text("g4music not running")

        if artist:
            self.artist.set_text(artist)

        if playing:
            if self.play.get_label() != "󰏤":
                self.play.get_child().set_text("󰐊")
        elif self.play.get_label() == "󰏤":
            self.play.get_child().set_text("󰒯")
        # (glyph handled by _set_play_glyph below)

        try:
            rate_f = float(rate) or 1.0
        except ValueError:
            rate_f = 1.0

        if pos and length:
            try:
                pos_us = float(pos)
                len_us = float(length)
                if len_us > 0:
                    adj = self.bar.get_adjustment()
                    if playing:
                        pos_us += rate_f * 250_000  # predict 250ms with rate
                    adj.set_upper(100)
                    self.bar.set_value(min(100.0, 100.0 * pos_us / len_us))
                    self.times.set_text(
                        f"{fmt(pos_us)} / {fmt(len_us)}")
            except ValueError:
                pass
        else:
            self.bar.set_value(0)
            self.times.set_text("--:-- / --:--")

        # album art
        if art and art.startswith("file://"):
            from urllib.parse import unquote, urlparse
            path = unquote(urlparse(art).path)
            if path != self.last_art:
                try:
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_size(path, 48, 48)
                    self.art.set_from_pixbuf(pb)
                    self.last_art = path
                except GLib.Error:
                    pass
        if not art:
            self.art.clear()
            self.last_art = None

        return True  # keep the timer


def fmt(us):
    s = int(us / 1_000_000)
    return f"{s // 60}:{s % 60:02d}"


if __name__ == "__main__":
    # only one popup at a time: if another real python popup is running,
    # exit quietly and leave it open. Match processes whose cmdline is
    # python3 .../music-popup.py exactly (never shell wrappers).
    me = os.getpid()
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me:
            continue
        try:
            args = open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
        except (OSError, PermissionError):
            continue
        is_python = args and args[0].endswith(b"python3")
        is_this = any(a.endswith(b"music-popup.py") for a in args[1:])
        if is_python and is_this:
            sys.exit(0)  # an instance is already open

    Popup()
    Gtk.main()
