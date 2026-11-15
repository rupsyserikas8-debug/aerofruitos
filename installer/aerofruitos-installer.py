#!/usr/bin/env python3
"""
Aerofruitos Custom TUI Installer
Lightweight text-based installer for Aerofruitos OS
Target: <100MB RAM usage
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Try to import textual for modern TUI, fallback to curses
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import Header, Footer, Static, Button, Input, Select, Checkbox, ProgressBar, Label
    from textual.screen import Screen
    from textual.binding import Binding
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    import curses
    from curses import wrapper

# Colors for Frutiger Aero theme (ANSI)
class AeroColors:
    TEAL = "\033[38;5;38m"      # #00B4D8
    TEAL_BRIGHT = "\033[38;5;39m"  # #48CAE4
    ORANGE = "\033[38;5;214m"   # #FFB700
    WHITE = "\033[38;5;15m"
    GRAY = "\033[38;5;245m"
    DARK = "\033[38;5;235m"
    RED = "\033[38;5;196m"
    GREEN = "\033[38;5;46m"
    YELLOW = "\033[38;5;226m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Backgrounds
    BG_TEAL = "\033[48;5;38m"
    BG_DARK = "\033[48;5;235m"
    BG_GLASS = "\033[48;5;255m"

# ASCII Art Logo
AERO_LOGO = f"""
{AeroColors.TEAL}    ╔══════════════════════════════════════╗
    ║  █████╗ ██╗   ██╗██████╗ ███████╗██████╗  ║
    ║ ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔══██╗ ║
    ║ ███████║██║   ██║██████╔╝█████╗  ██████╔╝ ║
    ║ ██╔══██║██║   ██║██╔══██╗██╔══╝  ██╔══██╗ ║
    ║ ██║  ██║╚██████╔╝██║  ██║███████╗██║  ██║ ║
    ║ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ║
    ║       Frutiger Aero Edition v1.0         ║
    ╚══════════════════════════════════════╝{AeroColors.RESET}
"""

@dataclass
class InstallConfig:
    """Installation configuration"""
    hostname: str = "aerofruitos"
    username: str = "user"
    password: str = ""
    root_password: str = ""
    timezone: str = "UTC"
    locale: str = "en_US.UTF-8"
    keymap: str = "us"
    target_disk: str = ""
    partition_scheme: str = "auto"  # auto, manual
    filesystem: str = "ext4"
    bootloader: str = "grub"
    gpu_driver: str = "nouveau"  # nouveau, nvidia-340xx
    desktop_env: str = "both"  # xfce, i3, both
    profile: str = "standard"  # minimal, standard, full
    enable_sudo: bool = True
    enable_networkmanager: bool = True
    enable_ssh: bool = False

class InstallStep(Enum):
    WELCOME = 0
    KEYBOARD = 1
    NETWORK = 2
    DISK = 3
    PARTITION = 4
    FILESYSTEM = 5
    PACKAGES = 6
    USERS = 7
    BOOTLOADER = 8
    CONFIG = 9
    THEME = 10
    SUMMARY = 11
    INSTALL = 12
    COMPLETE = 13

STEP_NAMES = {
    InstallStep.WELCOME: "Welcome",
    InstallStep.KEYBOARD: "Keyboard Layout",
    InstallStep.NETWORK: "Network Setup",
    InstallStep.DISK: "Select Disk",
    InstallStep.PARTITION: "Partition Disk",
    InstallStep.FILESYSTEM: "Format Partitions",
    InstallStep.PACKAGES: "Select Packages",
    InstallStep.USERS: "User Setup",
    InstallStep.BOOTLOADER: "Bootloader",
    InstallStep.CONFIG: "System Config",
    InstallStep.THEME: "Theme Setup",
    InstallStep.SUMMARY: "Summary",
    InstallStep.INSTALL: "Installing",
    InstallStep.COMPLETE: "Complete",
}

class AerofruitosInstaller:
    def __init__(self):
        self.config = InstallConfig()
        self.current_step = InstallStep.WELCOME
        self.disks = []
        self.partitions = []
        self.install_log = []
        self.mount_point = "/mnt"
        
    def log(self, msg: str):
        self.install_log.append(msg)
        print(f"{AeroColors.GRAY}[LOG]{AeroColors.RESET} {msg}")
    
    def run_cmd(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run command and log output"""
        self.log(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            if result.stdout:
                self.log(f"STDOUT: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"ERROR: {e.stderr.strip()}")
            if check:
                raise
            return e
    
    def detect_disks(self) -> List[Dict]:
        """Detect available disks"""
        try:
            result = self.run_cmd(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MODEL,TRAN"], check=False)
            import json
            data = json.loads(result.stdout)
            disks = []
            for dev in data.get("blockdevices", []):
                if dev.get("type") == "disk":
                    disks.append({
                        "name": f"/dev/{dev['name']}",
                        "size": dev["size"],
                        "model": dev.get("model", "Unknown"),
                        "transport": dev.get("tran", "unknown")
                    })
            self.disks = disks
            return disks
        except Exception as e:
            self.log(f"Disk detection failed: {e}")
            return []
    
    def partition_disk_auto(self, disk: str) -> List[Dict]:
        """Auto partition disk with BIOS/UEFI support"""
        partitions = []
        
        # Check if UEFI
        is_uefi = os.path.exists("/sys/firmware/efi/efivars")
        
        # Wipe disk
        self.run_cmd(["wipefs", "-a", disk])
        
        if is_uefi:
            # GPT for UEFI
            self.run_cmd(["parted", "-s", disk, "mklabel", "gpt"])
            # EFI partition (512MB)
            self.run_cmd(["parted", "-s", disk, "mkpart", "ESP", "fat32", "1MiB", "513MiB"])
            self.run_cmd(["parted", "-s", disk, "set", "1", "esp", "on"])
            # Swap partition (4GB)
            self.run_cmd(["parted", "-s", disk, "mkpart", "swap", "linux-swap", "513MiB", "4.5GiB"])
            # Root partition (rest)
            self.run_cmd(["parted", "-s", disk, "mkpart", "root", "ext4", "4.5GiB", "100%"])
            
            partitions = [
                {"device": f"{disk}1", "mount": "/boot/efi", "fs": "fat32", "size": "512M", "type": "efi"},
                {"device": f"{disk}2", "mount": "swap", "fs": "swap", "size": "4G", "type": "swap"},
                {"device": f"{disk}3", "mount": "/", "fs": "ext4", "size": "rest", "type": "root"},
            ]
        else:
            # MBR for BIOS
            self.run_cmd(["parted", "-s", disk, "mklabel", "msdos"])
            # Boot partition (512MB)
            self.run_cmd(["parted", "-s", disk, "mkpart", "primary", "ext4", "1MiB", "513MiB"])
            self.run_cmd(["parted", "-s", disk, "set", "1", "boot", "on"])
            # Swap partition (4GB)
            self.run_cmd(["parted", "-s", disk, "mkpart", "primary", "linux-swap", "513MiB", "4.5GiB"])
            # Root partition (rest)
            self.run_cmd(["parted", "-s", disk, "mkpart", "primary", "ext4", "4.5GiB", "100%"])
            
            partitions = [
                {"device": f"{disk}1", "mount": "/boot", "fs": "ext4", "size": "512M", "type": "boot"},
                {"device": f"{disk}2", "mount": "swap", "fs": "swap", "size": "4G", "type": "swap"},
                {"device": f"{disk}3", "mount": "/", "fs": "ext4", "size": "rest", "type": "root"},
            ]
        
        self.partitions = partitions
        return partitions
    
    def format_partitions(self):
        """Format partitions according to scheme"""
        for part in self.partitions:
            dev = part["device"]
            fs = part["fs"]
            
            if fs == "ext4":
                self.run_cmd(["mkfs.ext4", "-F", "-L", part.get("label", "AEROFRUITOS"), dev])
            elif fs == "fat32":
                self.run_cmd(["mkfs.fat", "-F32", "-n", "ESP", dev])
            elif fs == "swap":
                self.run_cmd(["mkswap", "-L", "SWAP", dev])
    
    def mount_partitions(self):
        """Mount partitions for installation"""
        # Mount root first
        root_part = next((p for p in self.partitions if p["type"] == "root"), None)
        if root_part:
            self.run_cmd(["mount", root_part["device"], self.mount_point])
        
        # Mount others
        for part in self.partitions:
            if part["type"] == "root":
                continue
            mount_path = f"{self.mount_point}{part['mount']}"
            if part["mount"] != "swap":
                os.makedirs(mount_path, exist_ok=True)
                self.run_cmd(["mount", part["device"], mount_path])
            else:
                self.run_cmd(["swapon", part["device"]])
    
    def install_base_system(self):
        """Install base system with pacstrap"""
        profile_packages = self.get_profile_packages()
        
        # Pacstrap
        cmd = ["pacstrap", "-K", self.mount_point] + profile_packages
        self.run_cmd(cmd)
        
        # Generate fstab
        self.run_cmd(["genfstab", "-U", self.mount_point], check=False)
        with open(f"{self.mount_point}/etc/fstab", "w") as f:
            result = self.run_cmd(["genfstab", "-U", self.mount_point])
            f.write(result.stdout)
    
    def get_profile_packages(self) -> List[str]:
        """Get package list for selected profile"""
        base = [
            "base", "linux-aerofruitos", "linux-firmware", "base-devel",
            "systemd", "systemd-sysvcompat", "grub", "efibootmgr",
            "networkmanager", "network-manager-applet",
            "pipewire", "pipewire-pulse", "wireplumber", "alsa-utils",
            "sudo", "vim", "nano", "man-db", "man-pages",
            "intel-ucode", "amd-ucode",
        ]
        
        if self.config.gpu_driver == "nvidia-340xx":
            base.extend(["nvidia-340xx", "nvidia-340xx-utils", "nvidia-340xx-dkms"])
        else:
            base.append("mesa")
        
        if self.config.desktop_env in ["xfce", "both"]:
            base.extend([
                "xfce4", "xfce4-goodies", "xfwm4", "thunar",
                "xfce4-whiskermenu-plugin", "xfce4-pulseaudio-plugin",
                "xfce4-battery-plugin", "xfce4-datetime-plugin",
                "xfce4-notifyd", "xfce4-power-manager", "xfce4-screenshooter",
                "xfce4-taskmanager", "xfce4-terminal", "lightdm", "lightdm-gtk-greeter"
            ])
        
        if self.config.desktop_env in ["i3", "both"]:
            base.extend([
                "i3-wm", "i3lock", "i3status", "polybar", "rofi", "picom",
                "dunst", "alacritty", "nitrogen", "lxappearance"
            ])
        
        if self.config.profile in ["standard", "full"]:
            base.extend([
                "firefox", "thunar", "mousepad", "gparted", "timeshift",
                "pavucontrol", "blueman", "cups", "system-config-printer",
                "ntfs-3g", "exfatprogs", "dosfstools", "btrfs-progs", "f2fs-tools",
                "reflector", "htop", "btop", "neofetch", "unzip", "p7zip"
            ])
        
        if self.config.profile == "full":
            base.extend([
                "libreoffice-fresh", "gimp", "mpv", "vlc", "code",
                "python", "python-pip", "nodejs", "npm", "docker",
                "virtualbox", "virtualbox-host-dkms"
            ])
        
        # Theme packages
        base.extend([
            "aerofruitos-gtk-theme", "aerofruitos-icon-theme",
            "aerofruitos-cursor-theme", "aerofruitos-fonts",
            "aerofruitos-wallpapers", "aerofruitos-theme-meta",
            "aerofruitos-installer"
        ])
        
        return base
    
    def configure_system(self):
        """Configure the installed system"""
        # Chroot commands
        chroot_cmds = [
            # Timezone
            f"ln -sf /usr/share/zoneinfo/{self.config.timezone} /etc/localtime",
            "hwclock --systohc",
            
            # Locale
            f"sed -i 's/^#{self.config.locale}/{self.config.locale}/' /etc/locale.gen",
            "locale-gen",
            f"echo 'LANG={self.config.locale}' > /etc/locale.conf",
            f"echo 'KEYMAP={self.config.keymap}' > /etc/vconsole.conf",
            
            # Hostname
            f"echo '{self.config.hostname}' > /etc/hostname",
            f"echo '127.0.0.1\tlocalhost' >> /etc/hosts",
            f"echo '::1\t\tlocalhost' >> /etc/hosts",
            f"echo '127.0.1.1\t{self.config.hostname}.localdomain\t{self.config.hostname}' >> /etc/hosts",
            
            # Root password
            f"echo 'root:{self.config.root_password}' | chpasswd",
            
            # User
            f"useradd -m -G wheel,audio,video,storage,network,power -s /bin/bash {self.config.username}",
            f"echo '{self.config.username}:{self.config.password}' | chpasswd",
        ]
        
        if self.config.enable_sudo:
            chroot_cmds.append("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
        
        # Enable services
        services = [
            "NetworkManager", "systemd-timesyncd", "fstrim.timer",
            "plymouth-start", "systemd-resolved"
        ]
        if self.config.desktop_env in ["xfce", "both"]:
            services.append("lightdm")
        elif self.config.desktop_env == "i3":
            services.append("sddm")
        
        for svc in services:
            chroot_cmds.append(f"systemctl enable {svc}")
        
        # GPU driver config
        if self.config.gpu_driver == "nvidia-340xx":
            chroot_cmds.extend([
                "sed -i 's/MODULES=()/MODULES=(nvidia nvidia_modeset nvidia_uvm nvidia_drm)/' /etc/mkinitcpio.conf",
                "mkinitcpio -P linux-aerofruitos"
            ])
        
        # Plymouth theme
        chroot_cmds.append("plymouth-set-default-theme aerofruitos -R")
        
        # GRUB
        is_uefi = os.path.exists("/sys/firmware/efi/efivars")
        if is_uefi:
            chroot_cmds.extend([
                "grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=Aerofruitos",
                "grub-mkconfig -o /boot/grub/grub.cfg"
            ])
        else:
            chroot_cmds.extend([
                f"grub-install --target=i386-pc {self.config.target_disk}",
                "grub-mkconfig -o /boot/grub/grub.cfg"
            ])
        
        # Apply theme defaults
        chroot_cmds.extend([
            "mkdir -p /etc/skel/.config/gtk-3.0",
            "echo '[Settings]' > /etc/skel/.config/gtk-3.0/settings.ini",
            "echo 'gtk-theme-name=Aerofruitos' >> /etc/skel/.config/gtk-3.0/settings.ini",
            "echo 'gtk-icon-theme-name=Aerofruitos' >> /etc/skel/.config/gtk-3.0/settings.ini",
            "echo 'gtk-font-name=Segoe UI 10' >> /etc/skel/.config/gtk-3.0/settings.ini",
            "echo 'gtk-cursor-theme-name=Aerofruitos' >> /etc/skel/.config/gtk-3.0/settings.ini",
            "echo 'gtk-cursor-theme-size=24' >> /etc/skel/.config/gtk-3.0/settings.ini",
            
            "mkdir -p /etc/skel/.config/gtk-4.0",
            "echo '[Settings]' > /etc/skel/.config/gtk-4.0/settings.ini",
            "echo 'gtk-theme-name=Aerofruitos' >> /etc/skel/.config/gtk-4.0/settings.ini",
            "echo 'gtk-icon-theme-name=Aerofruitos' >> /etc/skel/.config/gtk-4.0/settings.ini",
            "echo 'gtk-font-name=Segoe UI 10' >> /etc/skel/.config/gtk-4.0/settings.ini",
            "echo 'gtk-cursor-theme-name=Aerofruitos' >> /etc/skel/.config/gtk-4.0/settings.ini",
            "echo 'gtk-cursor-theme-size=24' >> /etc/skel/.config/gtk-4.0/settings.ini",
        ])
        
        # Execute all chroot commands
        for cmd in chroot_cmds:
            self.run_cmd(["arch-chroot", self.mount_point, "bash", "-c", cmd])
    
    def install_grub(self):
        """Install GRUB bootloader"""
        is_uefi = os.path.exists("/sys/firmware/efi/efivars")
        
        if is_uefi:
            self.run_cmd([
                "arch-chroot", self.mount_point,
                "grub-install", "--target=x86_64-efi",
                "--efi-directory=/boot/efi",
                "--bootloader-id=Aerofruitos"
            ])
        else:
            self.run_cmd([
                "arch-chroot", self.mount_point,
                "grub-install", "--target=i386-pc",
                self.config.target_disk
            ])
        
        self.run_cmd([
            "arch-chroot", self.mount_point,
            "grub-mkconfig", "-o", "/boot/grub/grub.cfg"
        ])
    
    def cleanup(self):
        """Unmount and cleanup"""
        # Unmount in reverse order
        for part in reversed(self.partitions):
            if part["mount"] != "swap":
                mount_path = f"{self.mount_point}{part['mount']}"
                self.run_cmd(["umount", "-R", mount_path], check=False)
            else:
                self.run_cmd(["swapoff", part["device"]], check=False)
        
        self.run_cmd(["umount", "-R", self.mount_point], check=False)

# Textual TUI App (modern)
if TEXTUAL_AVAILABLE:
    class AeroInstallerApp(App):
        CSS = """
        Screen {
            background: #1A1A2E;
        }
        .title {
            text-align: center;
            color: #00B4D8;
            text-style: bold;
            padding: 1;
        }
        .step-title {
            color: #48CAE4;
            text-style: bold;
            padding: 1;
        }
        .panel {
            border: solid #80D8EF;
            padding: 1;
            margin: 1;
        }
        .button {
            background: #00B4D8;
            color: #FFFFFF;
            border: none;
            padding: 1 2;
        }
        .button:hover {
            background: #48CAE4;
        }
        .button:focus {
            background: #0096C7;
        }
        Input, Select {
            border: solid #80D8EF;
            background: #C0FFFFFF;
            color: #1A1A2E;
        }
        Input:focus, Select:focus {
            border: solid #00B4D8;
        }
        ProgressBar {
            color: #00B4D8;
        }
        """
        
        BINDINGS = [
            Binding("ctrl+c", "quit", "Quit"),
            Binding("ctrl+n", "next", "Next"),
            Binding("ctrl+p", "previous", "Previous"),
        ]
        
        def __init__(self):
            super().__init__()
            self.installer = AerofruitosInstaller()
            self.current_step = InstallStep.WELCOME
        
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Container(
                Static(AERO_LOGO, classes="title"),
                id="main"
            )
            yield Footer()
        
        def action_next(self):
            self.advance_step()
        
        def action_previous(self):
            self.previous_step()
        
        def advance_step(self):
            pass  # Implement step logic
        
        def previous_step(self):
            pass  # Implement step logic

# Curses-based TUI (fallback)
def curses_main(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    
    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)    # Teal
    curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Orange
    curses.init_pair(3, curses.COLOR_WHITE, -1)   # White
    curses.init_pair(4, curses.COLOR_GREEN, -1)   # Success
    curses.init_pair(5, curses.COLOR_RED, -1)     # Error
    curses.init_pair(6, curses.COLOR_BLUE, -1)    # Info
    
    installer = AerofruitosInstaller()
    current_step = InstallStep.WELCOME
    
    def draw_header():
        h, w = stdscr.getmaxyx()
        stdscr.addstr(0, 0, "═" * w, curses.color_pair(1))
        stdscr.addstr(1, (w - len("Aerofruitos Installer")) // 2, "Aerofruitos Installer", 
                      curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(2, 0, "═" * w, curses.color_pair(1))
        
        # Step indicator
        step_text = f"Step {current_step.value + 1}/14: {STEP_NAMES[current_step]}"
        stdscr.addstr(3, 2, step_text, curses.color_pair(2))
        stdscr.addstr(4, 0, "─" * w, curses.color_pair(6))
    
    def draw_footer():
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h - 2, 0, "─" * w, curses.color_pair(6))
        stdscr.addstr(h - 1, 2, "[Enter] Next  [Backspace] Back  [Ctrl+C] Quit", curses.color_pair(6))
    
    def run_step():
        nonlocal current_step
        h, w = stdscr.getmaxyx()
        
        stdscr.clear()
        draw_header()
        
        if current_step == InstallStep.WELCOME:
            stdscr.addstr(6, 4, AERO_LOGO, curses.color_pair(1))
            stdscr.addstr(18, 4, "Welcome to Aerofruitos OS Installer", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(19, 4, "Frutiger Aero Edition - Daily Driver for Legacy Hardware", curses.color_pair(6))
            stdscr.addstr(21, 4, "Target: Q6600 + GT9600 + 2GB RAM", curses.color_pair(6))
            stdscr.addstr(22, 4, "Desktops: XFCE + i3 (both Frutiger Aero themed)", curses.color_pair(6))
            stdscr.addstr(24, 4, "Press Enter to continue...", curses.color_pair(2) | curses.A_BOLD)
        
        elif current_step == InstallStep.KEYBOARD:
            stdscr.addstr(6, 4, "Select Keyboard Layout:", curses.color_pair(3))
            layouts = ["us", "de", "fr", "uk", "es", "it", "pt", "ru", "jp", "cn"]
            for i, layout in enumerate(layouts):
                attr = curses.color_pair(1) | curses.A_BOLD if layout == installer.config.keymap else curses.color_pair(3)
                stdscr.addstr(8 + i, 6, f"  {layout}", attr)
            stdscr.addstr(h - 4, 4, "Use arrow keys to select, Enter to confirm", curses.color_pair(6))
        
        elif current_step == InstallStep.DISK:
            stdscr.addstr(6, 4, "Detecting disks...", curses.color_pair(2))
            stdscr.refresh()
            disks = installer.detect_disks()
            stdscr.addstr(8, 4, "Available Disks:", curses.color_pair(3))
            for i, disk in enumerate(disks):
                attr = curses.color_pair(1) | curses.A_BOLD if disk["name"] == installer.config.target_disk else curses.color_pair(3)
                stdscr.addstr(10 + i, 6, f"  {disk['name']} - {disk['size']} - {disk['model']}", attr)
            if not disks:
                stdscr.addstr(10, 6, "  No disks found!", curses.color_pair(5))
        
        elif current_step == InstallStep.PARTITION:
            stdscr.addstr(6, 4, f"Partitioning {installer.config.target_disk}...", curses.color_pair(2))
            stdscr.addstr(8, 4, "Scheme: Auto (BIOS/UEFI detected)", curses.color_pair(3))
            stdscr.addstr(9, 4, "  1. EFI/Boot - 512MB", curses.color_pair(3))
            stdscr.addstr(10, 4, "  2. Swap - 4GB", curses.color_pair(3))
            stdscr.addstr(11, 4, "  3. Root (ext4) - Rest", curses.color_pair(3))
            stdscr.addstr(13, 4, "Press Enter to confirm partitioning (DESTROYS DATA)", curses.color_pair(5) | curses.A_BOLD)
        
        elif current_step == InstallStep.FILESYSTEM:
            stdscr.addstr(6, 4, "Formatting partitions...", curses.color_pair(2))
            stdscr.refresh()
            try:
                installer.format_partitions()
                stdscr.addstr(8, 4, "✓ Partitions formatted successfully", curses.color_pair(4))
            except Exception as e:
                stdscr.addstr(8, 4, f"✗ Format failed: {e}", curses.color_pair(5))
        
        elif current_step == InstallStep.PACKAGES:
            stdscr.addstr(6, 4, "Select Install Profile:", curses.color_pair(3))
            profiles = [
                ("minimal", "Base + i3 only (~1.5GB)"),
                ("standard", "Base + XFCE + i3 + Apps (~3GB) [RECOMMENDED]"),
                ("full", "Everything + Dev tools + VM (~6GB)")
            ]
            for i, (name, desc) in enumerate(profiles):
                attr = curses.color_pair(1) | curses.A_BOLD if name == installer.config.profile else curses.color_pair(3)
                stdscr.addstr(8 + i*2, 6, f"  {name}", attr)
                stdscr.addstr(9 + i*2, 8, f"  {desc}", curses.color_pair(6))
            stdscr.addstr(h - 4, 4, "GPU Driver: " + installer.config.gpu_driver + " (press 'g' to toggle)", curses.color_pair(6))
            stdscr.addstr(h - 5, 4, "Desktop: " + installer.config.desktop_env + " (press 'd' to toggle)", curses.color_pair(6))
        
        elif current_step == InstallStep.USERS:
            stdscr.addstr(6, 4, "User Configuration:", curses.color_pair(3))
            fields = [
                ("Hostname", installer.config.hostname),
                ("Username", installer.config.username),
                ("Password", "*" * len(installer.config.password) if installer.config.password else "(empty)"),
                ("Root Password", "*" * len(installer.config.root_password) if installer.config.root_password else "(empty)"),
                ("Timezone", installer.config.timezone),
                ("Locale", installer.config.locale),
            ]
            for i, (label, value) in enumerate(fields):
                stdscr.addstr(8 + i, 6, f"  {label}: ", curses.color_pair(6))
                stdscr.addstr(8 + i, 22, value, curses.color_pair(3))
        
        elif current_step == InstallStep.INSTALL:
            stdscr.addstr(6, 4, "Installing Aerofruitos...", curses.color_pair(2))
            stdscr.addstr(8, 4, "This may take 10-30 minutes depending on profile", curses.color_pair(6))
            stdscr.addstr(10, 4, "Steps:", curses.color_pair(3))
            steps = [
                "Mount partitions",
                "Install base system (pacstrap)",
                "Configure system (locale, users, services)",
                "Install bootloader (GRUB)",
                "Apply Frutiger Aero theme",
                "Generate initramfs",
            ]
            for i, step in enumerate(steps):
                stdscr.addstr(12 + i, 6, f"  {i+1}. {step}", curses.color_pair(6))
            stdscr.addstr(20, 4, "Press Enter to start installation...", curses.color_pair(2) | curses.A_BOLD)
        
        elif current_step == InstallStep.COMPLETE:
            stdscr.addstr(6, 4, AERO_LOGO, curses.color_pair(1))
            stdscr.addstr(18, 4, "Installation Complete!", curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(20, 4, "Aerofruitos OS has been installed successfully.", curses.color_pair(3))
            stdscr.addstr(22, 4, "Remove installation media and reboot.", curses.color_pair(6))
            stdscr.addstr(24, 4, "Default login:", curses.color_pair(6))
            stdscr.addstr(25, 6, f"  User: {installer.config.username}", curses.color_pair(3))
            stdscr.addstr(26, 6, f"  Pass: [your password]", curses.color_pair(3))
            stdscr.addstr(28, 4, "Select desktop at login: XFCE or i3", curses.color_pair(6))
            stdscr.addstr(30, 4, "Press Enter to reboot...", curses.color_pair(2) | curses.A_BOLD)
        
        draw_footer()
        stdscr.refresh()
    
    # Main loop
    while True:
        run_step()
        key = stdscr.getch()
        
        if key == 3:  # Ctrl+C
            break
        elif key in (10, 13):  # Enter
            if current_step == InstallStep.WELCOME:
                current_step = InstallStep.KEYBOARD
            elif current_step == InstallStep.KEYBOARD:
                current_step = InstallStep.DISK
            elif current_step == InstallStep.DISK:
                if installer.disks:
                    installer.config.target_disk = installer.disks[0]["name"]
                    current_step = InstallStep.PARTITION
            elif current_step == InstallStep.PARTITION:
                try:
                    installer.partition_disk_auto(installer.config.target_disk)
                    current_step = InstallStep.FILESYSTEM
                except Exception as e:
                    stdscr.addstr(15, 4, f"Error: {e}", curses.color_pair(5))
                    stdscr.getch()
            elif current_step == InstallStep.FILESYSTEM:
                current_step = InstallStep.PACKAGES
            elif current_step == InstallStep.PACKAGES:
                current_step = InstallStep.USERS
            elif current_step == InstallStep.USERS:
                current_step = InstallStep.INSTALL
            elif current_step == InstallStep.INSTALL:
                # Run actual installation
                stdscr.addstr(22, 4, "Running installation...", curses.color_pair(2))
                stdscr.refresh()
                try:
                    installer.mount_partitions()
                    installer.install_base_system()
                    installer.configure_system()
                    installer.install_grub()
                    installer.cleanup()
                    current_step = InstallStep.COMPLETE
                except Exception as e:
                    stdscr.addstr(22, 4, f"Installation failed: {e}", curses.color_pair(5))
                    stdscr.getch()
            elif current_step == InstallStep.COMPLETE:
                installer.run_cmd(["reboot"])
                break
        elif key == 263:  # Backspace
            # Go back
            step_order = list(InstallStep)
            idx = step_order.index(current_step)
            if idx > 0:
                current_step = step_order[idx - 1]
        elif key == ord('g'):  # Toggle GPU driver
            if current_step == InstallStep.PACKAGES:
                installer.config.gpu_driver = "nvidia-340xx" if installer.config.gpu_driver == "nouveau" else "nouveau"
        elif key == ord('d'):  # Toggle desktop
            if current_step == InstallStep.PACKAGES:
                options = ["xfce", "i3", "both"]
                idx = options.index(installer.config.desktop_env)
                installer.config.desktop_env = options[(idx + 1) % len(options)]
        elif key == curses.KEY_UP or key == curses.KEY_DOWN:
            # Handle selection in steps with options
            pass

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--textual" and TEXTUAL_AVAILABLE:
        app = AeroInstallerApp()
        app.run()
    else:
        wrapper(curses_main)

if __name__ == "__main__":
    main()