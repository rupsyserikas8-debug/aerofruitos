#!/bin/bash
# Aerofruitos Build Script
# Run on Arch Linux (or Arch-based) as regular user with sudo access
# Builds all packages and creates ISO

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
PKG_DEST="$BUILD_DIR/packages"
ISO_OUT="$BUILD_DIR/iso_out"

log() { echo -e "${CYAN}[BUILD]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Check prerequisites
check_prereqs() {
    log "Checking prerequisites..."
    
    if ! command -v makepkg &>/dev/null; then
        error "makepkg not found. Install base-devel"
    fi
    
    if ! command -v mkarchiso &>/dev/null; then
        error "mkarchiso not found. Install archiso"
    fi
    
    if [[ $EUID -eq 0 ]]; then
        error "Don't run as root! Run as regular user with sudo access"
    fi
    
    # Check sudo access
    if ! sudo -n true 2>/dev/null; then
        log "Sudo access needed for ISO build. Please enter password when prompted."
        sudo -v || error "Sudo required"
    fi
    
    success "Prerequisites OK"
}

# Setup build directories
setup_dirs() {
    log "Setting up build directories..."
    mkdir -p "$BUILD_DIR" "$PKG_DEST" "$ISO_OUT"
    
    # Configure makepkg to use our package cache
    export PKGDEST="$PKG_DEST"
    export SRCDEST="$BUILD_DIR/src"
    export LOGDEST="$BUILD_DIR/logs"
    export BUILDDIR="$BUILD_DIR/build"
    
    mkdir -p "$SRCDEST" "$LOGDEST" "$BUILDDIR"
    success "Build directories ready"
}

# Build a package
build_package() {
    local pkg_dir="$1"
    local pkg_name=$(basename "$pkg_dir")
    
    log "Building $pkg_name..."
    
    cd "$pkg_dir"
    
    # Clean previous builds
    rm -f *.pkg.tar.zst *.pkg.tar.xz *.log
    
    # Build package
    if makepkg -sf --noconfirm --skippgpcheck 2>&1 | tee "$LOGDEST/$pkg_name.log"; then
        # Move built packages to cache
        mv *.pkg.tar.zst "$PKG_DEST"/ 2>/dev/null || true
        success "$pkg_name built successfully"
    else
        error "Failed to build $pkg_name. Check $LOGDEST/$pkg_name.log"
    fi
}

# Build all packages in order
build_all_packages() {
    log "Building all packages..."
    
    # Define build order (dependencies first)
    local packages=(
        "packages/base/aerofruitos-keyring"
        "packages/base/aerofruitos-mirrorlist"
        "packages/kernel/linux-aerofruitos"
        "packages/base/base-system"
        
        "packages/theme/aerofruitos-gtk-theme"
        "packages/theme/aerofruitos-icon-theme"
        "packages/theme/aerofruitos-cursor-theme"
        "packages/theme/aerofruitos-fonts"
        "packages/theme/aerofruitos-wallpapers"
        "packages/theme/plymouth-theme-aerofruitos"
        "packages/theme/grub-theme-aerofruitos"
        "packages/theme/sddm-theme-aerofruitos"
        "packages/theme/aerofruitos-theme-meta"
        
        "packages/de-xfce/xfce4-aerofruitos-config"
        "packages/de-i3/i3-aerofruitos-config"
        
        "packages/installer/aerofruitos-installer"
        
        "packages/apps/firefox-aerofruitos-theme"
    )
    
    for pkg in "${packages[@]}"; do
        if [[ -d "$PROJECT_ROOT/$pkg" ]]; then
            build_package "$PROJECT_ROOT/$pkg"
        else
            warn "Package directory not found: $pkg"
        fi
    done
    
    # Create local repository database
    log "Creating local package repository..."
    cd "$PKG_DEST"
    repo-add aerofruitos.db.tar.gz *.pkg.tar.zst 2>/dev/null || true
    success "Local repository created"
}

# Build ISO
build_iso() {
    log "Building ISO with archiso..."
    
    cd "$PROJECT_ROOT/iso"
    
    # Copy built packages to ISO profile for inclusion
    mkdir -p work/airootfs/var/cache/pacman/aerofruitos
    cp "$PKG_DEST"/*.pkg.tar.zst work/airootfs/var/cache/pacman/aerofruitos/ 2>/dev/null || true
    
    # Build ISO
    sudo mkarchiso -v -w "$BUILD_DIR/archiso-work" -o "$ISO_OUT" . 2>&1 | tee "$LOGDEST/iso-build.log"
    
    # Find the built ISO
    local iso_file=$(find "$ISO_OUT" -name "aerofruitos-*.iso" -type f | head -1)
    
    if [[ -f "$iso_file" ]]; then
        success "ISO built successfully!"
        log "ISO location: $iso_file"
        
        # Generate checksums
        cd "$(dirname "$iso_file")"
        sha256sum "$(basename "$iso_file")" > "$(basename "$iso_file").sha256"
        log "SHA256: $(cat "$(basename "$iso_file").sha256")"
    else
        error "ISO not found in output directory"
    fi
}

# Test ISO in QEMU
test_iso() {
    local iso_file=$(find "$ISO_OUT" -name "aerofruitos-*.iso" -type f | head -1)
    
    if [[ ! -f "$iso_file" ]]; then
        error "No ISO found to test"
    fi
    
    log "Testing ISO in QEMU (2GB RAM, 2 CPUs)..."
    log "Press Ctrl+Alt+G to release mouse, Ctrl+Alt+Delete to force quit"
    
    qemu-system-x86_64 \
        -enable-kvm \
        -m 2G \
        -smp 2 \
        -cpu host \
        -drive file="$iso_file",media=cdrom,readonly=on \
        -boot d \
        -display gtk,gl=on \
        -vga qxl \
        -device virtio-net-pci \
        -netdev user,id=net0 \
        -soundhw hda \
        -usb \
        -device usb-tablet
}

# Clean build artifacts
clean_build() {
    log "Cleaning build artifacts..."
    rm -rf "$BUILD_DIR"
    find "$PROJECT_ROOT/packages" -name "*.pkg.tar.zst" -delete
    find "$PROJECT_ROOT/packages" -name "*.pkg.tar.xz" -delete
    find "$PROJECT_ROOT/packages" -name "*.log" -delete
    find "$PROJECT_ROOT/packages" -name "pkg" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT/packages" -name "src" -type d -exec rm -rf {} + 2>/dev/null || true
    success "Clean complete"
}

# Show help
show_help() {
    cat << EOF
Aerofruitos Build Script

Usage: $0 [command]

Commands:
  build       Build all packages and ISO (default)
  packages    Build packages only
  iso         Build ISO only (requires packages)
  test        Test ISO in QEMU
  clean       Clean build artifacts
  help        Show this help

Environment Variables:
  SKIP_PACKAGES=1   Skip package building (use existing)
  SKIP_ISO=1        Skip ISO building
  SKIP_TEST=1       Skip QEMU test

Examples:
  $0                    # Full build
  $0 packages           # Build packages only
  $0 iso                # Build ISO from existing packages
  $0 test               # Test latest ISO
  $0 clean              # Clean everything
EOF
}

# Main
main() {
    local cmd="${1:-build}"
    
    case "$cmd" in
        build)
            check_prereqs
            setup_dirs
            build_all_packages
            build_iso
            ;;
        packages)
            check_prereqs
            setup_dirs
            build_all_packages
            ;;
        iso)
            check_prereqs
            setup_dirs
            build_iso
            ;;
        test)
            test_iso
            ;;
        clean)
            clean_build
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown command: $cmd. Use '$0 help' for usage."
            ;;
    esac
}

main "$@"