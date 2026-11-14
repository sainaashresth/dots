#!/bin/bash
# ============================================================================
#  pixie rice — restore script
#  Generated: 2026-11-14  from a fully working Arch + Hyprland (Wayland) setup
#
#  What this machine had:
#    - Hyprland 0.57 (lua config) + waybar (drawers, auto-hide) + fuzzel
#    - foot terminal, dolphin + dark color scheme (DarkMatch)
#    - SDDM "pixie" login theme (patched Main.qml date, user avatar/background)
#    - gtklock lock screen styled like the login (Google Sans Flex Freeze)
#    - Plymouth boot splash: pixie-y2k (custom) or deus_ex (AUR)
#    - swayimg + reference.sh = SUPER+I image reference popup (float+pin)
#    - clipboard history: cliphist + fuzzel picker (SUPER+SHIFT+V copy,
#      SUPER+SHIFT+X delete), daemon autostarts via hyprland.start
#    - screenshots: grim+slurp (PRINT = area, SHIFT+PRINT = full) saved to
#      ~/Pictures/Screenshots, copied to clipboard
#    - wallpaper auto-restore via start-wallpaper.sh at hyprland.start
#
#  HOW TO RESTORE (on a fresh Arch install):
#    1. Install packages:        sudo pacman -S --needed - < pkglist-explicit.txt
#       AUR packages:            yay -S - < pkglist-aur.txt      (run as user)
#       Flatpak apps:            xargs -a pkglist-flatpak.txt -n1 flatpak install -y
#    2. Run this script:         ./restore.sh
#       - user configs copied with cp (no deletions)
#       - root files section runs with sudo (prompts once)
#    3. sudo mkinitcpio -P && sudo grub-mkconfig -o /boot/grub/grub.cfg
#    4. fc-cache -f  (refresh fonts)
#    5. Reboot once. Check: sddm shows pixie; boot shows the splash;
#       after login wallpaper restores by itself (see /tmp/start-wallpaper.log).
#
#  Notes:
#    - Everything here is reversible; the script never deletes anything.
#    - Hardware caveats baked into config: ZED_ALLOW_UNSUPPORTED_GPU=1 and
#      Vulkan notes in hyprland.lua are for Intel Haswell (HD 4400) —
#      on a newer GPU you can remove them.
# ============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "==> Restoring user configs to ~/.config and ~/.local/share ..."
mkdir -p "$HOME/.config" "$HOME/.local/share"
cp -a "$HERE/config/." "$HOME/.config/"
if [ -d "$HERE/local-share/fonts" ]; then
    mkdir -p "$HOME/.local/share/fonts"
    cp -a "$HERE/local-share/fonts/." "$HOME/.local/share/fonts/"
fi
chmod +x "$HOME/.config/hypr/scripts/"*.sh 2>/dev/null || true
chmod +x "$HOME/.config/waybar/scripts/"* 2>/dev/null || true

echo "==> SDDM: pixie-sddm source restored to ~/pixie-sddm (copy to /usr/share via root section)"
if [ -d "$HERE/pixie-sddm-src" ] && [ ! -d "$HOME/pixie-sddm" ]; then
    cp -a "$HERE/pixie-sddm-src" "$HOME/pixie-sddm"
fi

if [ "$(id -u)" -eq 0 ]; then
    ROOT_SECTION="yes"
else
    echo
    echo "==> Root files (SDDM theme, Plymouth theme, boot configs) need sudo."
    read -r -p "    Run the root section now with sudo? [y/N] " ans
    case "$ans" in [yY]*) ROOT_SECTION="yes" ;; *) ROOT_SECTION="no" ;;
    esac
fi

if [ "$ROOT_SECTION" = "yes" ]; then
    echo "==> Root section: installing themes + boot configs (all backed up first) ..."
    ts=$(date +%Y%m%d-%H%M%S)

    # SDDM theme
    if [ -d "$HERE/root/sddm/themes/pixie" ]; then
        sudo mkdir -p /usr/share/sddm/themes
        [ -d /usr/share/sddm/themes/pixie ] && \
            sudo cp -a /usr/share/sddm/themes/pixie "/usr/share/sddm/themes/pixie.bak-$ts"
        sudo cp -a "$HERE/root/sddm/themes/pixie" /usr/share/sddm/themes/pixie
        sudo mkdir -p /etc/sddm.conf.d
        sudo cp -a "$HERE/root/etc/sddm.conf.d/theme.conf" /etc/sddm.conf.d/theme.conf
        echo "    sddm: pixie installed, Current=pixie"
    fi

    # Plymouth pixie-y2k
    if [ -d "$HERE/root/plymouth/themes/pixie-y2k" ]; then
        sudo mkdir -p /usr/share/plymouth/themes
        sudo cp -a "$HERE/root/plymouth/themes/pixie-y2k" /usr/share/plymouth/themes/pixie-y2k
        sudo plymouth-set-default-theme pixie-y2k || \
            echo "    (plymouth not installed? install it, then re-run this block)"
        echo "    plymouth: pixie-y2k installed + set default"
    fi

    # boot configs (restore only if the system files exist to begin with)
    [ -f /etc/mkinitcpio.conf ] && \
        sudo cp -a "$HERE/root/etc/mkinitcpio.conf" /etc/mkinitcpio.conf
    [ -f /etc/default/grub ] && \
        sudo cp -a "$HERE/root/etc/default/grub" /etc/default/grub
    [ -f /etc/plymouth/plymouthd.conf ] && \
        sudo cp -a "$HERE/root/etc/plymouth/plymouthd.conf" /etc/plymouth/plymouthd.conf
    echo "    mkinitcpio.conf / grub defaults / plymouthd.conf restored"
    echo
    echo "==> IMPORTANT: finish with:"
    echo "      sudo mkinitcpio -P"
    echo "      sudo grub-mkconfig -o /boot/grub/grub.cfg"
    echo "      fc-cache -f"
    echo "      # then reboot once"
fi

echo "==> Done. Log in, then press SUPER+I to test the reference popup,"
echo "    SUPER+SHIFT+V for clipboard history, PRINT for screenshots."
