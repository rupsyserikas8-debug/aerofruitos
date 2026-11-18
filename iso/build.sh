#!/bin/bash
# Aerofruitos ISO Profile - archiso configuration
# Build with: sudo mkarchiso -v -w /tmp/archiso-build -o /out iso/

# Profile definition
iso_name="aerofruitos"
iso_label="AEROFRUITOS_$(date +%Y%m)"
iso_publisher="Aerofruitos OS <https://github.com/aerofruitos>"
iso_application="Aerofruitos Frutiger Aero Edition"
iso_version="$(date +%Y.%m.%d)"
install_dir="aerofruitos"
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito' 'uefi-x64.systemd-boot.esp' 'uefi-x64.systemd-boot.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '15')

# Profile packages (installed into live system)
packages=(
    # Base
    "base"
    "linux"
    "linux-firmware"
    "systemd"
    "systemd-sysvcompat"
    
    # Boot
    "grub"
    "efibootmgr"
    "plymouth"
    "syslinux"
    
    # Network
    "networkmanager"
    "network-manager-applet"
    "wireless_tools"
    "wpa_supplicant"
    "dhcpcd"
    "inetutils"
    "iproute2"
    
    # Filesystem tools
    "e2fsprogs"
    "dosfstools"
    "ntfs-3g"
    "exfatprogs"
    "btrfs-progs"
    "f2fs-tools"
    
    # Basic utilities
    "sudo"
    "vim"
    "nano"
    "less"
    "man-db"
    "man-pages"
    "texinfo"
    "which"
    "psmisc"
    "procps-ng"
    "coreutils"
    "findutils"
    "grep"
    "sed"
    "gawk"
    "tar"
    "gzip"
    "bzip2"
    "xz"
    "zstd"
    "unzip"
    "p7zip"
    
    # Hardware support
    "intel-ucode"
    "amd-ucode"
    "usbutils"
    "pciutils"
    "lsb-release"
    "hwdetect"
    "dmidecode"
    "lshw"
    
    # Audio
    "pipewire"
    "pipewire-pulse"
    "wireplumber"
    "alsa-utils"
    "alsa-firmware"
    "pavucontrol"
    
    # Open-source GPU drivers
    "mesa"
    "vulkan-radeon"
    "vulkan-intel"
    
    # XFCE Desktop
    "xfce4"
    "xfce4-goodies"
    "xfwm4"
    "thunar"
    "xfce4-whiskermenu-plugin"
    "xfce4-pulseaudio-plugin"
    "xfce4-battery-plugin"
    "xfce4-datetime-plugin"
    "xfce4-notifyd"
    "xfce4-power-manager"
    "xfce4-screenshooter"
    "xfce4-taskmanager"
    "xfce4-terminal"
    "lightdm"
    "lightdm-gtk-greeter"
    
    # i3 Window Manager
    "i3-wm"
    "i3lock"
    "i3status"
    "polybar"
    "rofi"
    "picom"
    "dunst"
    "alacritty"
    "nitrogen"
    "lxappearance"
    
    # Applications
    "firefox"
    "thunar"
    "mousepad"
    "gparted"
    "timeshift"
    "reflector"
    "htop"
    "btop"
    "neofetch"
    
    # Theme packages
    "aerofruitos-gtk-theme"
    "aerofruitos-icon-theme"
    "aerofruitos-cursor-theme"
    "aerofruitos-fonts"
    "aerofruitos-wallpapers"
    "aerofruitos-theme-meta"
    
    # Installer
    "aerofruitos-installer"
    "python-textual"
    
    # Live environment
    "archiso"
    "mkinitcpio-archiso"
    "arch-install-scripts"
    "parted"
    "gptfdisk"
    "cryptsetup"
    "lvm2"
    "btrfs-progs"
    "f2fs-tools"
)

# Additional packages for specific architectures (none for x86_64)
packages_x86_64=()

# Remove these packages after install (not needed on installed system)
remove_packages=(
    "archiso"
    "mkinitcpio-archiso"
    "arch-install-scripts"
    "gptfdisk"
)

# Files to copy to airootfs (overlay)
# These are created in the airootfs/ directory structure

# Override pacman.conf
cp /etc/pacman.conf work/airootfs/etc/pacman.conf

# Enable services
systemctl -f enable NetworkManager.service --root=work/airootfs/
systemctl -f enable systemd-timesyncd.service --root=work/airootfs/
systemctl -f enable fstrim.timer --root=work/airootfs/
systemctl -f enable plymouth-start.service --root=work/airootfs/

# Enable display managers (both, user chooses at login)
systemctl -f enable lightdm.service --root=work/airootfs/
systemctl -f enable sddm.service --root=work/airootfs/

# Configure sudo
echo '%wheel ALL=(ALL:ALL) ALL' > work/airootfs/etc/sudoers.d/99-wheel
chmod 440 work/airootfs/etc/sudoers.d/99-wheel

# Configure live user
useradd -m -G wheel,audio,video,storage,network,power -s /bin/bash -p '' liveuser --root=work/airootfs/
echo 'liveuser ALL=(ALL) NOPASSWD: ALL' > work/airootfs/etc/sudoers.d/99-liveuser
chmod 440 work/airootfs/etc/sudoers.d/99-liveuser

# Auto-login for live user (LightDM)
mkdir -p work/airootfs/etc/lightdm/lightdm.conf.d/
cat > work/airootfs/etc/lightdm/lightdm.conf.d/50-autologin.conf << 'EOF'
[Seat:*]
autologin-user=liveuser
autologin-user-timeout=0
user-session=aerofruitos-xfce
EOF

# Auto-login for live user (SDDM)
mkdir -p work/airootfs/etc/sddm.conf.d/
cat > work/airootfs/etc/sddm.conf.d/autologin.conf << 'EOF'
[Autologin]
User=liveuser
Session=aerofruitos-xfce
Relogin=false
EOF

# Plymouth theme
mkdir -p work/airootfs/usr/share/plymouth/themes/aerofruitos/
# (theme files copied from aerofruitos-plymouth-theme package)

# GRUB theme
mkdir -p work/airootfs/usr/share/grub/themes/aerofruitos/
# (theme files copied from aerofruitos-grub-theme package)

# Default wallpaper
mkdir -p work/airootfs/usr/share/backgrounds/aerofruitos/
# (wallpapers copied from aerofruitos-wallpapers package)

# GTK settings for live user
mkdir -p work/airootfs/home/liveuser/.config/gtk-3.0/
cat > work/airootfs/home/liveuser/.config/gtk-3.0/settings.ini << 'EOF'
[Settings]
gtk-theme-name=Aerofruitos
gtk-icon-theme-name=Aerofruitos
gtk-font-name=Segoe UI 10
gtk-cursor-theme-name=Aerofruitos
gtk-cursor-theme-size=24
gtk-toolbar-style=GTK_TOOLBAR_ICONS
gtk-toolbar-icon-size=GTK_ICON_SIZE_LARGE_TOOLBAR
gtk-button-images=1
gtk-menu-images=1
gtk-enable-event-sounds=1
gtk-enable-input-feedback-sounds=1
gtk-xft-antialias=1
gtk-xft-hinting=1
gtk-xft-hintstyle=hintslight
gtk-xft-rgba=rgb
gtk-application-prefer-dark-theme=false
gtk-decoration-layout=menu:minimize,maximize,close
EOF

mkdir -p work/airootfs/home/liveuser/.config/gtk-4.0/
cat > work/airootfs/home/liveuser/.config/gtk-4.0/settings.ini << 'EOF'
[Settings]
gtk-theme-name=Aerofruitos
gtk-icon-theme-name=Aerofruitos
gtk-font-name=Segoe UI 10
gtk-cursor-theme-name=Aerofruitos
gtk-cursor-theme-size=24
gtk-decoration-layout=menu:minimize,maximize,close
EOF

# XFCE panel config for live user
mkdir -p work/airootfs/home/liveuser/.config/xfce4/xfconf/xfce-perchannel-xml/
# (configs from xfce4-aerofruitos-config package)

# i3 config for live user
mkdir -p work/airootfs/home/liveuser/.config/i3/
# (config from i3-aerofruitos-config package)

# Polybar config
mkdir -p work/airootfs/home/liveuser/.config/polybar/
# (config from i3-aerofruitos-config package)

# Rofi config
mkdir -p work/airootfs/home/liveuser/.config/rofi/
# (config from i3-aerofruitos-config package)

# Picom config
mkdir -p work/airootfs/home/liveuser/.config/picom/
# (config from i3-aerofruitos-config package)

# Dunst config
mkdir -p work/airootfs/home/liveuser/.config/dunst/
# (config from i3-aerofruitos-config package)

# Alacritty config
mkdir -p work/airootfs/home/liveuser/.config/alacritty/
# (config from i3-aerofruitos-config package)

# Nitrogen config
mkdir -p work/airootfs/home/liveuser/.config/nitrogen/
# (config from i3-aerofruitos-config package)

# Set ownership
chown -R 1000:1000 work/airootfs/home/liveuser/

# Mkinitcpio hooks (add plymouth for boot splash)
sed -i 's/HOOKS=(base udev autodetect modconf block filesystems keyboard fsck)/HOOKS=(base udev autodetect modconf block filesystems keyboard fsck plymouth)/' work/airootfs/etc/mkinitcpio.conf

# Generate initramfs
mkinitcpio -p linux --root=work/airootfs/

# Build ISO
mkarchiso -v -w /tmp/archiso-build -o /out .