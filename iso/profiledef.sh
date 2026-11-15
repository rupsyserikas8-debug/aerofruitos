#!/bin/bash
# Aerofruitos archiso profile definition

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
    "linux-aerofruitos"
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
    
    # GPU Drivers (both for user choice)
    "mesa"
    "vulkan-radeon"
    "vulkan-intel"
    "nvidia-340xx"
    "nvidia-340xx-utils"
    "nvidia-340xx-dkms"
    
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

# Additional packages for specific architectures
packages_x86_64=()

# Remove these packages after install
remove_packages=(
    "archiso"
    "mkinitcpio-archiso"
    "arch-install-scripts"
    "gptfdisk"
)