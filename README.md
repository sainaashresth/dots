# pixie rice — full backup (2026-11-14)

A complete, shareable snapshot of my Arch Linux + Hyprland desktop rice.
Machine: Toshiba laptop, Intel Haswell HD 4400 + dead GT 720M, 1366x768, Arch.

## What's in here

| Path | What |
|---|---|
| `config/hypr/` | Hyprland lua config (binds, env, autostart) + all scripts (wallpaper restore, clipboard picker + daemon, screenshots, reference popup, auto-hide, power menu) |
| `config/waybar/` | waybar config + style (music hover drawer, workspaces) + scripts |
| `config/fuzzel/` | fuzzel.ini (cyan glow theme) |
| `config/foot/` | foot terminal config |
| `config/gtklock/` | lock screen styled like the login |
| `config/waypaper/` + `config/wallppr/` | wallpaper settings + wallpapers |
| `config/zed/`, `dolphinrc`, `kdeglobals`, `color-schemes/` | editor + dolphin + dark scheme |
| `local-share/fonts/` | FlexRounded fonts ("Google Sans Flex Freeze") |
| `pixie-sddm-src/` | the original pixie SDDM theme source repo |
| `y2k-splash/` + `y2k-assets.py` | my custom Plymouth theme source + its asset generator |
| `root/` | root-owned copies: SDDM theme (patched Main.qml + assets), plymouth pixie-y2k theme, `/etc/mkinitcpio.conf`, `/etc/default/grub`, `/etc/plymouth/plymouthd.conf`, `/etc/sddm.conf.d/theme.conf` |
| `pkglist-explicit.txt` | all explicitly installed pacman packages |
| `pkglist-aur.txt` | AUR packages |
| `pkglist-flatpak.txt` | flatpak apps |
| `restore.sh` | the installer — run it on a fresh machine |

## Restore on a new device (short version)

```bash
sudo pacman -S --needed - < pkglist-explicit.txt
yay -S - < pkglist-aur.txt
./restore.sh          # will offer to run the root section with sudo
sudo mkinitcpio -P && sudo grub-mkconfig -o /boot/grub/grub.cfg
fc-cache -f
# reboot
```

## Keybinds cheat sheet

| Bind | Action |
|---|---|
| SUPER+SPACE | fuzzel app launcher |
| SUPER+Q / C | run app in terminal / close window |
| SUPER+I | reference image popup (fuzzel picker, float+pin) |
| SUPER+SHIFT+V | clipboard history picker (copies selection) |
| SUPER+SHIFT+X | clipboard history picker (deletes selection) |
| PRINT / SHIFT+PRINT | screenshot area / full screen (→ ~/Pictures/Screenshots + clipboard) |
| SUPER+ESCAPE | power menu (fuzzel: lock/logout/restart/poweroff) |
| SUPER+M | session exit |
| SUPER+V | float toggle |
| SUPER+E | dolphin |
| SUPER+W | *(removed — wallpaper now auto-restores at login)* |

## Known hardware gotchas (already handled in config)

- Haswell has no Vulkan 1.3 → `ZED_ALLOW_UNSUPPORTED_GPU=1` (Zed runs on llvmpipe)
- GT 720M has no working driver → expect nvidia probe errors at boot (harmless)
- Zed "won't open" fix: `pkill -f zed-editor` (single-instance zombie)

## Plymouth theme switch

```bash
sudo plymouth-set-default-theme pixie-y2k   # cyan Y2K custom (recommended)
# or
sudo plymouth-set-default-theme deus_ex     # terminal/hacker style (AUR)
sudo mkinitcpio -P
```

## Sharing note

Contains personal wallpapers/avatar images (`wallppr/`, SDDM `assets/`) and
FlexRounded font files — fine to share privately; check the font license if
publishing publicly.
