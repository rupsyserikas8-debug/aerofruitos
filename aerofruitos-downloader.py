#!/usr/bin/env python3
"""
Aerofruitos ISO Downloader & Launcher
Cross-platform tool to download, verify, and test Aerofruitos ISOs
"""

import os
import sys
import json
import hashlib
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from pathlib import Path
import platform
import webbrowser

# Aerofruitos branding
AERO_COLORS = {
    'bg': '#0A1620',
    'card': '#1A1A2E',
    'glass': '#C0FFFFFF',
    'teal': '#00B4D8',
    'teal_light': '#48CAE4',
    'teal_dark': '#0096C7',
    'orange': '#FFB700',
    'white': '#FFFFFF',
    'text': '#E0E0E0',
    'text_muted': '#4A4A6A',
    'border': '#80D8EF',
    'success': '#28A745',
    'error': '#DC3545',
    'warning': '#FFC107',
}

# Default release info (update when real releases exist)
RELEASE_INFO = {
    'latest': {
        'version': '2026.11.15',
        'date': '2026-11-15',
        'iso_url': 'https://github.com/aerofruitos/aerofruitos/releases/download/v2026.11.15/aerofruitos-2026.11.15-x86_64.iso',
        'sha256_url': 'https://github.com/aerofruitos/aerofruitos/releases/download/v2026.11.15/aerofruitos-2026.11.15-x86_64.iso.sha256',
        'size_mb': 2800,
        'notes': 'Initial release with XFCE + i3, Frutiger Aero theme, Linux 6.6 LTS kernel'
    },
    'mirrors': [
        'https://mirrors.aerofruitos.org/releases/',
        'https://mirror.aerofruitos.org/releases/',
    ]
}

class AerofruitosDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Aerofruitos ISO Downloader & Launcher")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        self.download_thread = None
        self.download_path = Path.home() / "Downloads" / "aerofruitos"
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.iso_path = None
        
        self.setup_style()
        self.create_ui()
        self.load_release_info()
    
    def setup_style(self):
        """Configure custom styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('.', 
            background=AERO_COLORS['bg'],
            foreground=AERO_COLORS['text'],
            font=('Segoe UI', 10)
        )
        
        style.configure('TFrame', background=AERO_COLORS['bg'])
        style.configure('TLabel', background=AERO_COLORS['bg'], foreground=AERO_COLORS['text'])
        style.configure('TLabelFrame', background=AERO_COLORS['bg'], foreground=AERO_COLORS['teal'])
        style.configure('TLabelFrame.Label', background=AERO_COLORS['bg'], foreground=AERO_COLORS['teal'], font=('Segoe UI', 11, 'bold'))
        
        style.configure('Card.TFrame', background=AERO_COLORS['card'])
        style.configure('Card.TLabel', background=AERO_COLORS['card'], foreground=AERO_COLORS['text'])
        
        style.configure('Aero.TButton',
            background=AERO_COLORS['teal'],
            foreground=AERO_COLORS['white'],
            borderwidth=0,
            focuscolor=AERO_COLORS['teal_light'],
            font=('Segoe UI', 10, 'bold'),
            padding=(20, 10)
        )
        style.map('Aero.TButton',
            background=[('active', AERO_COLORS['teal_light']), ('pressed', AERO_COLORS['teal_dark']), ('disabled', AERO_COLORS['border'])]
        )
        
        style.configure('Aero.Secondary.TButton',
            background=AERO_COLORS['card'],
            foreground=AERO_COLORS['teal'],
            borderwidth=2,
            bordercolor=AERO_COLORS['border'],
            font=('Segoe UI', 10),
            padding=(15, 8)
        )
        style.map('Aero.Secondary.TButton',
            background=[('active', AERO_COLORS['glass']), ('pressed', AERO_COLORS['teal'])]
        )
        
        style.configure('Aero.Danger.TButton',
            background=AERO_COLORS['error'],
            foreground=AERO_COLORS['white'],
            borderwidth=0,
            font=('Segoe UI', 10, 'bold'),
            padding=(15, 8)
        )
        
        style.configure('Aero.Horizontal.TProgressbar',
            background=AERO_COLORS['teal'],
            troughcolor=AERO_COLORS['card'],
            borderwidth=0,
            lightcolor=AERO_COLORS['teal_light'],
            darkcolor=AERO_COLORS['teal']
        )
        
        style.configure('Aero.TEntry',
            fieldbackground=AERO_COLORS['card'],
            foreground=AERO_COLORS['text'],
            bordercolor=AERO_COLORS['border'],
            lightcolor=AERO_COLORS['teal'],
            darkcolor=AERO_COLORS['teal']
        )
        
        style.configure('Aero.TCombobox',
            fieldbackground=AERO_COLORS['card'],
            foreground=AERO_COLORS['text'],
            background=AERO_COLORS['card'],
            bordercolor=AERO_COLORS['border']
        )
        
        # Configure root
        self.root.configure(bg=AERO_COLORS['bg'])
    
    def create_ui(self):
        """Create the main UI"""
        # Main container
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Header with logo
        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 20))
        
        logo_text = tk.Label(header, 
            text="AEROFRUITOS",
            font=('Segoe UI', 28, 'bold'),
            fg=AERO_COLORS['teal'],
            bg=AERO_COLORS['bg']
        )
        logo_text.pack(side=tk.LEFT)
        
        subtitle = tk.Label(header,
            text="Frutiger Aero Edition  •  ISO Downloader & Launcher",
            font=('Segoe UI', 11),
            fg=AERO_COLORS['text_muted'],
            bg=AERO_COLORS['bg']
        )
        subtitle.pack(side=tk.LEFT, padx=(15, 0), pady=(10, 0))
        
        # Version badge
        self.version_badge = tk.Label(header,
            text="v2026.11.15",
            font=('Segoe UI', 10, 'bold'),
            fg=AERO_COLORS['white'],
            bg=AERO_COLORS['teal'],
            padx=10, pady=4
        )
        self.version_badge.pack(side=tk.RIGHT, pady=(10, 0))
        
        # Main content area - 3 columns
        content = ttk.Frame(main)
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.columnconfigure(2, weight=1)
        content.rowconfigure(0, weight=1)
        
        # Column 1: Download
        self.create_download_panel(content)
        
        # Column 2: Verify & Info
        self.create_verify_panel(content)
        
        # Column 3: Launch & Test
        self.create_launch_panel(content)
        
        # Progress bar at bottom
        self.progress_frame = ttk.Frame(main)
        self.progress_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            style='Aero.Horizontal.TProgressbar',
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Ready", style='TLabel')
        self.progress_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Log area
        log_frame = ttk.LabelFrame(main, text="Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            bg=AERO_COLORS['card'],
            fg=AERO_COLORS['text'],
            font=('JetBrains Mono', 9) if self.font_exists('JetBrains Mono') else ('Consolas', 9),
            insertbackground=AERO_COLORS['teal'],
            selectbackground=AERO_COLORS['teal'],
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=AERO_COLORS['border'],
            highlightbackground=AERO_COLORS['border']
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
    
    def font_exists(self, font_name):
        """Check if font is available"""
        import tkinter.font as tkfont
        return font_name in tkfont.families()
    
    def create_download_panel(self, parent):
        """Create download panel"""
        frame = ttk.LabelFrame(parent, text="📥 Download ISO", padding=15)
        frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        frame.rowconfigure(4, weight=1)
        
        # Version info
        info_frame = ttk.Frame(frame, style='Card.TFrame', padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(info_frame, text="Latest Release", style='Card.TLabel', font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        self.release_version = ttk.Label(info_frame, text="v2026.11.15", style='Card.TLabel', foreground=AERO_COLORS['teal'])
        self.release_version.pack(anchor=tk.W)
        self.release_date = ttk.Label(info_frame, text="Released: 2026-11-15", style='Card.TLabel', foreground=AERO_COLORS['text_muted'])
        self.release_date.pack(anchor=tk.W)
        self.release_size = ttk.Label(info_frame, text="Size: ~2.8 GB", style='Card.TLabel', foreground=AERO_COLORS['text_muted'])
        self.release_size.pack(anchor=tk.W)
        
        # Download location
        loc_frame = ttk.Frame(frame)
        loc_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(loc_frame, text="Save to:").pack(anchor=tk.W)
        
        loc_input_frame = ttk.Frame(loc_frame)
        loc_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.path_var = tk.StringVar(value=str(self.download_path))
        path_entry = ttk.Entry(loc_input_frame, textvariable=self.path_var, style='Aero.TEntry')
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(loc_input_frame, text="Browse", style='Aero.Secondary.TButton', command=self.browse_path).pack(side=tk.RIGHT)
        
        # Mirror selection
        mirror_frame = ttk.Frame(frame)
        mirror_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(mirror_frame, text="Mirror:").pack(anchor=tk.W)
        self.mirror_var = tk.StringVar()
        self.mirror_combo = ttk.Combobox(mirror_frame, textvariable=self.mirror_var, style='Aero.TCombobox', state='readonly')
        self.mirror_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Download button
        self.download_btn = ttk.Button(
            frame,
            text="⬇  Download ISO",
            style='Aero.TButton',
            command=self.start_download
        )
        self.download_btn.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        # Cancel button
        self.cancel_btn = ttk.Button(
            frame,
            text="✕ Cancel Download",
            style='Aero.Danger.TButton',
            command=self.cancel_download,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(fill=tk.X)
        
        # Release notes
        notes_frame = ttk.LabelFrame(frame, text="Release Notes", padding=10)
        notes_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notes_text = tk.Text(
            notes_frame,
            height=8,
            bg=AERO_COLORS['card'],
            fg=AERO_COLORS['text_muted'],
            font=('Segoe UI', 9),
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=AERO_COLORS['border'],
            highlightbackground=AERO_COLORS['border']
        )
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        self.notes_text.config(state=tk.DISABLED)
    
    def create_verify_panel(self, parent):
        """Create verification panel"""
        frame = ttk.LabelFrame(parent, text="🔐 Verify & Info", padding=15)
        frame.grid(row=0, column=1, sticky=tk.NSEW, padx=5)
        frame.rowconfigure(2, weight=1)
        
        # File selection
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(file_frame, text="ISO File:").pack(anchor=tk.W)
        
        file_input = ttk.Frame(file_frame)
        file_input.pack(fill=tk.X, pady=(5, 0))
        
        self.iso_file_var = tk.StringVar()
        iso_entry = ttk.Entry(file_input, textvariable=self.iso_file_var, style='Aero.TEntry')
        iso_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(file_input, text="Browse", style='Aero.Secondary.TButton', command=self.browse_iso).pack(side=tk.RIGHT)
        
        # Auto-detect downloaded ISO
        ttk.Button(frame, text="🔍 Auto-detect Downloaded ISO", style='Aero.Secondary.TButton', command=self.auto_detect_iso).pack(fill=tk.X, pady=(0, 15))
        
        # Verification buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(btn_frame, text="✓ Verify SHA256", style='Aero.TButton', command=self.verify_sha256).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="📋 Show File Info", style='Aero.Secondary.TButton', command=self.show_file_info).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="🔑 Verify GPG Signature", style='Aero.Secondary.TButton', command=self.verify_gpg).pack(fill=tk.X, pady=2)
        
        # Results area
        results_frame = ttk.LabelFrame(frame, text="Verification Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.verify_text = scrolledtext.ScrolledText(
            results_frame,
            bg=AERO_COLORS['card'],
            fg=AERO_COLORS['text'],
            font=('JetBrains Mono', 9) if self.font_exists('JetBrains Mono') else ('Consolas', 9),
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=AERO_COLORS['border'],
            highlightbackground=AERO_COLORS['border']
        )
        self.verify_text.pack(fill=tk.BOTH, expand=True)
        self.verify_text.config(state=tk.DISABLED)
    
    def create_launch_panel(self, parent):
        """Create launch/test panel"""
        frame = ttk.LabelFrame(parent, text="🚀 Launch & Test", padding=15)
        frame.grid(row=0, column=2, sticky=tk.NSEW, padx=(10, 0))
        frame.rowconfigure(3, weight=1)
        
        # Quick launch buttons
        ttk.Label(frame, text="Quick Launch:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # VM launch buttons
        vm_frame = ttk.Frame(frame)
        vm_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(vm_frame, text="🖥  QEMU/KVM (Linux)", style='Aero.TButton', command=lambda: self.launch_vm('qemu')).pack(fill=tk.X, pady=3)
        ttk.Button(vm_frame, text="📦 VirtualBox", style='Aero.Secondary.TButton', command=lambda: self.launch_vm('virtualbox')).pack(fill=tk.X, pady=3)
        ttk.Button(vm_frame, text="☁  VMware Player/Workstation", style='Aero.Secondary.TButton', command=lambda: self.launch_vm('vmware')).pack(fill=tk.X, pady=3)
        
        # USB writing
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        ttk.Label(frame, text="Write to USB:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        usb_frame = ttk.Frame(frame)
        usb_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(usb_frame, text="💾 Rufus (Windows)", style='Aero.TButton', command=lambda: self.open_tool('rufus')).pack(fill=tk.X, pady=3)
        ttk.Button(usb_frame, text="🔧 Ventoy (Multi-boot)", style='Aero.Secondary.TButton', command=lambda: self.open_tool('ventoy')).pack(fill=tk.X, pady=3)
        ttk.Button(usb_frame, text="🐧 balenaEtcher (Cross-platform)", style='Aero.Secondary.TButton', command=lambda: self.open_tool('etcher')).pack(fill=tk.X, pady=3)
        ttk.Button(usb_frame, text="📝 dd (Linux/macOS)", style='Aero.Secondary.TButton', command=self.show_dd_command).pack(fill=tk.X, pady=3)
        
        # System requirements
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        ttk.Label(frame, text="Target Hardware:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        req_frame = ttk.Frame(frame, style='Card.TFrame', padding=10)
        req_frame.pack(fill=tk.BOTH, expand=True)
        
        requirements = [
            ("CPU", "Core 2 Quad Q6600 or better"),
            ("RAM", "2 GB minimum (4 GB recommended)"),
            ("GPU", "NVIDIA GT9600 / Intel GMA / AMD equivalent"),
            ("Storage", "8 GB USB / 20 GB disk"),
            ("Firmware", "BIOS or UEFI (no Secure Boot)"),
            ("Display", "1024×768 minimum"),
        ]
        
        for label, value in requirements:
            row = ttk.Frame(req_frame, style='Card.TFrame')
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{label}:", style='Card.TLabel', foreground=AERO_COLORS['text_muted'], width=10).pack(side=tk.LEFT)
            ttk.Label(row, text=value, style='Card.TLabel').pack(side=tk.LEFT)
        
        # Links
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        links = [
            ("📖 Documentation", "https://github.com/aerofruitos/aerofruitos/wiki"),
            ("🐛 Report Issue", "https://github.com/aerofruitos/aerofruitos/issues"),
            ("💬 Discussions", "https://github.com/aerofruitos/aerofruitos/discussions"),
            ("⭐ Star on GitHub", "https://github.com/aerofruitos/aerofruitos"),
        ]
        
        for text, url in links:
            btn = ttk.Button(frame, text=text, style='Aero.Secondary.TButton', command=lambda u=url: webbrowser.open(u))
            btn.pack(fill=tk.X, pady=2)
    
    def load_release_info(self):
        """Load release information"""
        # In production, this would fetch from GitHub API
        info = RELEASE_INFO['latest']
        
        self.release_version.config(text=f"Version {info['version']}")
        self.release_date.config(text=f"Released: {info['date']}")
        self.release_size.config(text=f"Size: ~{info['size_mb']} MB")
        
        # Mirrors
        mirrors = ['Auto (GitHub)'] + RELEASE_INFO['mirrors']
        self.mirror_combo['values'] = mirrors
        self.mirror_combo.current(0)
        
        # Notes
        self.notes_text.config(state=tk.NORMAL)
        self.notes_text.delete(1.0, tk.END)
        self.notes_text.insert(tk.END, info['notes'])
        self.notes_text.config(state=tk.DISABLED)
    
    def browse_path(self):
        """Browse for download directory"""
        path = filedialog.askdirectory(initialdir=self.download_path, title="Select Download Folder")
        if path:
            self.download_path = Path(path)
            self.path_var.set(str(self.download_path))
    
    def browse_iso(self):
        """Browse for ISO file"""
        path = filedialog.askopenfilename(
            initialdir=self.download_path,
            title="Select Aerofruitos ISO",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )
        if path:
            self.iso_file_var.set(path)
            self.iso_path = Path(path)
            self.log(f"Selected ISO: {path}")
    
    def auto_detect_iso(self):
        """Auto-detect downloaded ISO"""
        iso_files = list(self.download_path.glob("aerofruitos-*.iso"))
        if iso_files:
            latest = max(iso_files, key=lambda f: f.stat().st_mtime)
            self.iso_file_var.set(str(latest))
            self.iso_path = latest
            self.log(f"Auto-detected: {latest.name}")
        else:
            messagebox.showinfo("Not Found", "No Aerofruitos ISO found in download folder")
    
    def start_download(self):
        """Start downloading ISO"""
        if self.download_thread and self.download_thread.is_alive():
            return
        
        mirror = self.mirror_var.get()
        if mirror == 'Auto (GitHub)':
            url = RELEASE_INFO['latest']['iso_url']
        else:
            url = mirror.rstrip('/') + '/' + Path(RELEASE_INFO['latest']['iso_url']).name
        
        filename = Path(url).name
        dest = self.download_path / filename
        
        if dest.exists():
            if not messagebox.askyesno("File Exists", f"{filename} already exists. Overwrite?"):
                return
        
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_label.config(text="Starting download...")
        
        self.download_thread = threading.Thread(target=self.download_file, args=(url, dest), daemon=True)
        self.download_thread.start()
    
    def download_file(self, url, dest):
        """Download file with progress"""
        try:
            self.log(f"Downloading from {url}")
            
            req = Request(url, headers={'User-Agent': 'Aerofruitos-Downloader/1.0'})
            with urlopen(req, timeout=30) as response:
                total = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(dest, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total > 0:
                            progress = (downloaded / total) * 100
                            self.root.after(0, lambda p=progress: self.update_progress(p, downloaded, total))
                
                self.root.after(0, lambda: self.download_complete(dest))
                
        except Exception as e:
            self.root.after(0, lambda: self.download_error(str(e)))
    
    def update_progress(self, progress, downloaded, total):
        """Update progress bar"""
        self.progress_var.set(progress)
        self.progress_label.config(text=f"Downloading... {self.format_size(downloaded)} / {self.format_size(total)} ({progress:.1f}%)")
    
    def download_complete(self, dest):
        """Download completed"""
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_var.set(100)
        self.progress_label.config(text="Download complete!")
        self.iso_file_var.set(str(dest))
        self.iso_path = dest
        self.log(f"Download complete: {dest}")
        messagebox.showinfo("Success", f"ISO downloaded to:\n{dest}")
        
        # Auto-verify
        self.verify_sha256()
    
    def download_error(self, error):
        """Download error"""
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="Download failed")
        self.log(f"Download error: {error}")
        messagebox.showerror("Download Failed", f"Error: {error}")
    
    def cancel_download(self):
        """Cancel download"""
        # Note: This is a simple implementation; real cancellation would need more work
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="Cancelled")
        self.log("Download cancelled by user")
    
    def verify_sha256(self):
        """Verify SHA256 checksum"""
        if not self.iso_path or not self.iso_path.exists():
            messagebox.showwarning("No File", "Please select an ISO file first")
            return
        
        self.log(f"Verifying SHA256 for {self.iso_path.name}...")
        self.verify_text.config(state=tk.NORMAL)
        self.verify_text.delete(1.0, tk.END)
        self.verify_text.insert(tk.END, f"Calculating SHA256 for {self.iso_path.name}...\n")
        self.verify_text.config(state=tk.DISABLED)
        
        def verify():
            try:
                sha256 = hashlib.sha256()
                with open(self.iso_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        sha256.update(chunk)
                calculated = sha256.hexdigest()
                
                # Try to fetch expected hash
                expected = self.fetch_expected_hash()
                
                self.root.after(0, lambda: self.show_verify_result(calculated, expected))
            except Exception as e:
                self.root.after(0, lambda: self.show_verify_error(str(e)))
        
        threading.Thread(target=verify, daemon=True).start()
    
    def fetch_expected_hash(self):
        """Fetch expected hash from release"""
        try:
            sha256_url = RELEASE_INFO['latest']['sha256_url']
            req = Request(sha256_url, headers={'User-Agent': 'Aerofruitos-Downloader/1.0'})
            with urlopen(req, timeout=10) as response:
                content = response.read().decode().strip()
                # Format: "hash  filename"
                return content.split()[0]
        except:
            return None
    
    def show_verify_result(self, calculated, expected):
        """Show verification result"""
        self.verify_text.config(state=tk.NORMAL)
        self.verify_text.delete(1.0, tk.END)
        
        self.verify_text.insert(tk.END, f"Calculated SHA256:\n{calculated}\n\n")
        
        if expected:
            self.verify_text.insert(tk.END, f"Expected SHA256:\n{expected}\n\n")
            if calculated.lower() == expected.lower():
                self.verify_text.insert(tk.END, "✅ VERIFICATION PASSED - Hashes match!\n", 'success')
                self.verify_text.tag_config('success', foreground=AERO_COLORS['success'])
                self.log("✅ SHA256 verification PASSED")
            else:
                self.verify_text.insert(tk.END, "❌ VERIFICATION FAILED - Hashes do NOT match!\n", 'error')
                self.verify_text.tag_config('error', foreground=AERO_COLORS['error'])
                self.log("❌ SHA256 verification FAILED")
        else:
            self.verify_text.insert(tk.END, "⚠ Could not fetch expected hash from release.\n")
            self.verify_text.insert(tk.END, "Please verify manually against release page.\n")
            self.log("⚠ Could not fetch expected hash")
        
        self.verify_text.config(state=tk.DISABLED)
    
    def show_verify_error(self, error):
        """Show verification error"""
        self.verify_text.config(state=tk.NORMAL)
        self.verify_text.delete(1.0, tk.END)
        self.verify_text.insert(tk.END, f"Verification error: {error}\n")
        self.verify_text.config(state=tk.DISABLED)
        self.log(f"Verification error: {error}")
    
    def show_file_info(self):
        """Show file information"""
        if not self.iso_path or not self.iso_path.exists():
            messagebox.showwarning("No File", "Please select an ISO file first")
            return
        
        stat = self.iso_path.stat()
        info = f"""File: {self.iso_path.name}
Path: {self.iso_path}
Size: {self.format_size(stat.st_size)} ({stat.st_size:,} bytes)
Modified: {stat.st_mtime}
"""
        
        self.verify_text.config(state=tk.NORMAL)
        self.verify_text.delete(1.0, tk.END)
        self.verify_text.insert(tk.END, info)
        self.verify_text.config(state=tk.DISABLED)
    
    def verify_gpg(self):
        """Verify GPG signature"""
        messagebox.showinfo("GPG Verification", "GPG signature verification requires:\n1. Aerofruitos signing key imported\n2. .sig file downloaded\n\nRun manually:\n  gpg --verify aerofruitos-*.iso.sig aerofruitos-*.iso")
    
    def launch_vm(self, vm_type):
        """Launch VM for testing"""
        if not self.iso_path or not self.iso_path.exists():
            messagebox.showwarning("No ISO", "Please download or select an ISO first")
            return
        
        commands = {
            'qemu': [
                'qemu-system-x86_64',
                '-enable-kvm',
                '-m', '2G',
                '-cpu', 'host',
                '-smp', '4',
                '-drive', f'file={self.iso_path},media=cdrom,readonly=on',
                '-boot', 'd',
                '-display', 'gtk',
                '-vga', 'qxl',
                '-device', 'virtio-net-pci',
                '-netdev', 'user,id=net0'
            ],
            'virtualbox': [
                'VBoxManage', 'createvm', '--name', 'Aerofruitos-Test', '--register',
                'VBoxManage', 'modifyvm', 'Aerofruitos-Test', '--memory', '2048', '--cpus', '2',
                'VBoxManage', 'storagectl', 'Aerofruitos-Test', '--name', 'IDE', '--add', 'ide',
                'VBoxManage', 'storageattach', 'Aerofruitos-Test', '--storagectl', 'IDE', '--port', '0', '--device', '0', '--type', 'dvddrive', '--medium', str(self.iso_path),
                'VBoxManage', 'startvm', 'Aerofruitos-Test'
            ],
            'vmware': [
                'vmplayer', str(self.iso_path)
            ]
        }
        
        if vm_type not in commands:
            return
        
        cmd = commands[vm_type]
        
        try:
            if vm_type == 'virtualbox':
                # Run each VBoxManage command separately
                for c in cmd:
                    subprocess.Popen(c, shell=True)
            else:
                subprocess.Popen(cmd)
            self.log(f"Launched {vm_type} with ISO: {self.iso_path.name}")
            messagebox.showinfo("VM Launched", f"{vm_type} started with Aerofruitos ISO")
        except FileNotFoundError:
            messagebox.showerror("Not Found", f"{vm_type} not installed or not in PATH")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {vm_type}: {e}")
    
    def open_tool(self, tool):
        """Open USB writing tool website"""
        urls = {
            'rufus': 'https://rufus.ie/',
            'ventoy': 'https://www.ventoy.net/',
            'etcher': 'https://www.balena.io/etcher/'
        }
        if tool in urls:
            webbrowser.open(urls[tool])
            self.log(f"Opened {tool} website")
    
    def show_dd_command(self):
        """Show dd command for Linux/macOS"""
        if not self.iso_path or not self.iso_path.exists():
            messagebox.showwarning("No ISO", "Please select an ISO file first")
            return
        
        cmd = f"sudo dd if={self.iso_path} of=/dev/sdX bs=4M status=progress && sync"
        
        dialog = tk.Toplevel(self.root)
        dialog.title("dd Command")
        dialog.geometry("600x200")
        dialog.configure(bg=AERO_COLORS['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Linux/macOS dd command:", font=('Segoe UI', 10, 'bold')).pack(pady=10)
        
        text = tk.Text(dialog, height=4, bg=AERO_COLORS['card'], fg=AERO_COLORS['teal'], font=('JetBrains Mono', 10), wrap=tk.WORD)
        text.pack(fill=tk.X, padx=20, pady=10)
        text.insert(tk.END, cmd)
        text.config(state=tk.DISABLED)
        
        ttk.Label(dialog, text="⚠ Replace /dev/sdX with your USB device (use lsblk to find it)", foreground=AERO_COLORS['warning']).pack()
        
        ttk.Button(dialog, text="Copy to Clipboard", style='Aero.TButton', command=lambda: self.copy_to_clipboard(cmd)).pack(pady=10)
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Command copied to clipboard!")
    
    def format_size(self, bytes_val):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
    
    def log(self, message):
        """Add message to log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

def main():
    # Check for required modules
    try:
        import tkinter
        import tkinter.ttk
    except ImportError:
        print("tkinter not available. Install python3-tk (Linux) or use Windows/macOS Python.")
        sys.exit(1)
    
    root = tk.Tk()
    
    # Set window icon if available
    try:
        # root.iconbitmap('aerofruitos.ico')  # Would need actual icon file
        pass
    except:
        pass
    
    app = AerofruitosDownloader(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()