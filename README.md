# Aerofruitos OS - Frutiger Aero Edition

![Aerofruitos](https://img.shields.io/badge/Aerofruitos-Frutiger%20Aero%20Edition-00B4D8?style=for-the-badge&logo=linux&logoColor=white)
![Target](https://img.shields.io/badge/Target-Q6600%20%7C%20GT9600%20%7C%202GB%20RAM-FFB700?style=for-the-badge)
![Desktop](https://img.shields.io/badge/DEs-XFCE%20%2B%20i3-48CAE4?style=for-the-badge)
![License](https://img.shields.io/badge/License-GPL%20v3-28A745?style=for-the-badge)

A daily-driver Linux distribution with full **Frutiger Aero** theming, optimized for legacy hardware (Core 2 Quad Q6600, NVIDIA GT9600, 2GB RAM).

## ✨ Features

- **🎨 Full Frutiger Aero Theme**: Boot (Plymouth) → GRUB → Login (SDDM) → Desktop (XFCE + i3) → Apps
- **🖥 Dual Desktop Environments**: XFCE (traditional) + i3 (tiling WM) - both Aero-themed
- **⚡ Optimized Kernel**: Custom config for Q6600, GT9600, 2GB RAM with zswap, transparent hugepages
- **📦 Hybrid Package System**: Arch base + custom PKGBUILDs (source builds, no binary repo needed)
- **🔧 Lightweight TUI Installer**: Custom Python installer (<100MB RAM) - no Calamares bloat
- **🎮 GPU Driver Choice**: Nouveau (open) or nvidia-340xx (proprietary) selectable at install
- **🌐 Modern Stack**: PipeWire, NetworkManager, systemd, GRUB2, Plymouth

## 📋 Target Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | Core 2 Quad Q6600 (2.4 GHz) | Any 64-bit dual/quad core |
| **RAM** | 2 GB | 4 GB+ |
| **GPU** | NVIDIA GT9600 / Intel GMA / AMD equivalent | Any with OpenGL 2.1+ |
| **Storage** | 8 GB USB / 20 GB disk | 50 GB+ SSD |
| **Firmware** | BIOS or UEFI | UEFI preferred |
| **Display** | 1024×768 | 1366×768+ |

## 🚀 Quick Start

### Download ISO (Windows/macOS/Linux)

Run the cross-platform downloader:

```bash
python3 aerofruitos-downloader.py
```

Or download directly from [GitHub Releases](https://github.com/aerofruitos/aerofruitos/releases) when available.

### Write to USB

**Windows**: Use [Rufus](https://rufus.ie/) or [Ventoy](https://www.ventoy.net/)

**Linux/macOS**:
```bash
# Find your USB device (e.g., /dev/sdX)
lsblk

# Write ISO (REPLACE /dev/sdX with your device!)
sudo dd if=aerofruitos-*.iso of=/dev/sdX bs=4M status=progress && sync
```

### Install

1. Boot from USB
2. Login as `liveuser` (no password)
3. Run installer: `aerofruitos-install` (or it may auto-start)
4. Follow TUI prompts:
   - Keyboard layout
   - Disk selection (auto-partition or manual)
   - Profile: **Minimal** (i3 only) / **Standard** (XFCE+i3+apps) / **Full** (dev tools)
   - GPU driver: Nouveau or nvidia-340xx
   - User setup
5. Reboot and enjoy!

## 🏗 Building from Source

### Prerequisites (Arch Linux or Arch-based)

```bash
# Install build dependencies
sudo pacman -S --needed base-devel archiso git python python-textual \
  xmlto kmod inetutils bc libelf cpio perl tar xz \
  gtk3 gtk4 sassc meson \
  imagemagick inkscape xorg-xcursorgen fontconfig unzip \
  qemu virt-manager ovmf dosfstools gptfdisk parted
```

### Build Process

```bash
# Clone repository
git clone https://github.com/aerofruitos/aerofruitos.git
cd aerofruitos

# Build all packages (in order)
cd packages/kernel/linux-aerofruitos && makepkg -si
cd ../../base/aerofruitos-keyring && makepkg -si
cd ../aerofruitos-mirrorlist && makepkg -si
cd ../base-system && makepkg -si

# Theme packages
cd ../../theme/aerofruitos-gtk-theme && makepkg -si
cd ../aerofruitos-icon-theme && makepkg -si
cd ../aerofruitos-cursor-theme && makepkg -si
cd ../aerofruitos-fonts && makepkg -si
cd ../aerofruitos-wallpapers && makepkg -si
cd ../plymouth-theme-aerofruitos && makepkg -si
cd ../grub-theme-aerofruitos && makepkg -si
cd ../sddm-theme-aerofruitos && makepkg -si
cd ../aerofruitos-theme-meta && makepkg -si

# DE configs
cd ../../de-xfce/xfce4-aerofruitos-config && makepkg -si
cd ../../de-i3/i3-aerofruitos-config && makepkg -si

# Installer
cd ../../installer/aerofruitos-installer && makepkg -si

# Apps
cd ../../apps/firefox-aerofruitos-theme && makepkg -si

# Build ISO (requires root)
cd ../../iso
sudo ./build.sh
```

### Build Output

ISO will be in `/out/aerofruitos-YYYY.MM.DD-x86_64.iso`

## 📁 Project Structure

```
aerofruitos/
├── packages/
│   ├── base/                    # Core system packages
│   │   ├── aerofruitos-keyring  # PGP keys
│   │   ├── aerofruitos-mirrorlist
│   │   └── base-system          # Meta-package
│   ├── kernel/
│   │   └── linux-aerofruitos    # Custom kernel (6.6 LTS)
│   ├── theme/                   # Frutiger Aero theme stack
│   │   ├── aerofruitos-gtk-theme    # GTK2/3/4 theme
│   │   ├── aerofruitos-icon-theme   # Icon theme
│   │   ├── aerofruitos-cursor-theme # Cursor theme
│   │   ├── aerofruitos-fonts        # Segoe UI, JetBrains Mono
│   │   ├── aerofruitos-wallpapers   # Wallpapers
│   │   ├── plymouth-theme-aerofruitos
│   │   ├── grub-theme-aerofruitos
│   │   ├── sddm-theme-aerofruitos
│   │   └── aerofruitos-theme-meta   # Meta-package
│   ├── de-xfce/
│   │   └── xfce4-aerofruitos-config
│   ├── de-i3/
│   │   └── i3-aerofruitos-config
│   ├── apps/
│   │   └── firefox-aerofruitos-theme
│   └── installer/
│       └── aerofruitos-installer    # Custom TUI installer
├── installer/                     # Installer source code
├── iso/                          # archiso profile
│   ├── profiledef.sh
│   ├── packages.x86_64
│   ├── pacman.conf
│   └── build.sh
├── config/                       # System configs
├── docs/                         # Documentation
├── aerofruitos-downloader.py     # Cross-platform downloader GUI
└── requirements.txt              # Build dependencies
```

## 🎨 Frutiger Aero Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Teal | `#00B4D8` | Primary accent, highlights |
| Teal Light | `#48CAE4` | Hover states, progress |
| Teal Dark | `#0096C7` | Active states, borders |
| Orange | `#FFB700` | Warning, secondary accent |
| White | `#FFFFFF` | Text on dark |
| Glass | `rgba(255,255,255,0.75)` | Panel/background translucency |
| Glass Dark | `rgba(255,255,255,0.55)` | Deeper glass |
| Dark BG | `#1A1A2E` | Window backgrounds |
| Text | `#E0E0E0` | Primary text |
| Text Muted | `#4A4A6A` | Secondary text |
| Border | `#80D8EF` | Borders, dividers |

## ⌨️ Default Keybindings

### XFCE
| Key | Action |
|-----|--------|
| `Super` | Whisker Menu |
| `Super + T` | Terminal |
| `Super + F` | File Manager |
| `Super + W` | Web Browser |
| `Super + L` | Lock Screen |
| `Print` | Screenshot (full) |
| `Shift + Print` | Screenshot (window) |
| `Alt + Print` | Screenshot (region) |

### i3
| Key | Action |
|-----|--------|
| `Super + Enter` | Terminal (Alacritty) |
| `Super + D` | App Launcher (Rofi) |
| `Super + Shift + D` | Run Command (Rofi) |
| `Super + H/J/K/L` | Focus Left/Down/Up/Right |
| `Super + Shift + H/J/K/L` | Move Window |
| `Super + F` | Fullscreen Toggle |
| `Super + S/W/E` | Stacking/Tabbed/Toggle Split |
| `Super + Shift + Space` | Toggle Floating |
| `Super + 1-0` | Switch Workspace |
| `Super + Shift + 1-0` | Move to Workspace |
| `Super + R` | Resize Mode |
| `Super + Shift + C` | Reload Config |
| `Super + Shift + R` | Restart i3 |
| `Super + Shift + Q` | Kill Window |
| `Super + Shift + L` | Lock Screen |
| `Super + Shift + P` | Power Menu |
| `Super + -/=` | Gaps Adjust |

## 🐛 Troubleshooting

### GT9600 Nouveau Issues
```bash
# If Nouveau fails, install nvidia-340xx
yay -S nvidia-340xx nvidia-340xx-dkms

# Or boot with kernel parameter:
# modprobe.blacklist=nouveau
```

### Low Memory (2GB RAM)
```bash
# Enable zswap (already in kernel config)
echo 1 > /sys/module/zswap/parameters/enabled

# Reduce swappiness
echo 10 > /proc/sys/vm/swappiness

# Use lighter apps: mpv instead of VLC, Mousepad instead of VS Code
```

### Theme Not Applying
```bash
# Regenerate font cache
fc-cache -f -v

# Reapply theme
aerofruitos-font-setup
# For GTK apps:
gsettings set org.gnome.desktop.interface gtk-theme 'Aerofruitos'
gsettings set org.gnome.desktop.interface icon-theme 'Aerofruitos'
```

### WiFi Not Working
```bash
# Check rfkill
rfkill list
rfkill unblock all

# Restart NetworkManager
sudo systemctl restart NetworkManager
```

## 📄 License

- **Code**: GPL v3
- **Theme Assets**: CC-BY-SA 4.0
- **Fonts**: See individual licenses (JetBrains Mono: OFL, Segoe UI: Microsoft proprietary)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 🙏 Acknowledgments

- **Arch Linux** - Base distribution
- **XFCE/i3** - Desktop environments
- **Frutiger Aero** - Design inspiration (Microsoft Windows Vista/7 era)
- **Chicago95/Orchis** - GTK theme references
- **JetBrains Mono** - Monospace font
- **Archiso** - ISO building tool

## 📞 Support

- **Wiki**: [GitHub Wiki](https://github.com/aerofruitos/aerofruitos/wiki)
- **Issues**: [GitHub Issues](https://github.com/aerofruitos/aerofruitos/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aerofruitos/aerofruitos/discussions)

---

**Made with 💚 for legacy hardware enthusiasts**

*Aerofruitos - Bringing Frutiger Aero beauty to 2006 hardware*