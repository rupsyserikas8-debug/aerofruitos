#!/bin/bash
# Aerofruitos Build Script
# Works in Docker (as root) and locally (as user with sudo)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BUILD_DIR="$PROJECT_ROOT/build"
PKG_DEST="$BUILD_DIR/packages"
ISO_OUT="$BUILD_DIR/iso_out"

# Detect if running as root (Docker) or user (local)
IS_ROOT=false
if [[ $EUID -eq 0 ]]; then
    IS_ROOT=true
fi

SUDO=""
if [[ "$IS_ROOT" == "false" ]]; then
    SUDO="sudo"
fi

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
    
    if [[ "$IS_ROOT" == "false" ]]; then
        if ! $SUDO -n true 2>/dev/null; then
            log "Sudo access needed for ISO build."
            $SUDO -v || error "Sudo required"
        fi
    fi
    
    success "Prerequisites OK"
}

# Setup build directories
setup_dirs() {
    log "Setting up build directories..."
    mkdir -p "$BUILD_DIR" "$PKG_DEST" "$ISO_OUT"
    
    export PKGDEST="$PKG_DEST"
    export SRCDEST="$BUILD_DIR/src"
    export LOGDEST="$BUILD_DIR/logs"
    export BUILDDIR="$BUILD_DIR/build"
    
    mkdir -p "$SRCDEST" "$LOGDEST" "$BUILDDIR"
    
    # Ensure builder user can write to project and build dirs
    if [[ "$IS_ROOT" == "true" ]]; then
        if ! id builder &>/dev/null; then
            useradd -m -G wheel builder
            echo 'builder ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
        fi
        chown -R builder:builder "$PROJECT_ROOT"
        chmod -R a+rwX "$PROJECT_ROOT"
    fi
    
    success "Build directories ready"
}

# Build a package
build_package() {
    local pkg_dir="$1"
    local pkg_name=$(basename "$pkg_dir")
    
    log "Building $pkg_name..."
    
    # Copy to writable build location to avoid permission issues on bind mounts
    local work_dir="$BUILDDIR/$pkg_name"
    rm -rf "$work_dir"
    cp -r "$pkg_dir" "$work_dir"
    
    if [[ "$IS_ROOT" == "true" ]]; then
        chown -R builder:builder "$work_dir"
    fi
    
    cd "$work_dir"
    rm -f *.pkg.tar.zst *.pkg.tar.xz *.log
    
    # Run makepkg as builder user if root, otherwise current user
    local makepkg_cmd="PKGDEST='$PKG_DEST' SRCDEST='$SRCDEST' LOGDEST='$LOGDEST' makepkg -sf --noconfirm --skippgpcheck"
    if [[ "$IS_ROOT" == "true" ]]; then
        if sudo -u builder bash -c "$makepkg_cmd" 2>&1 | tee "$LOGDEST/$pkg_name.log"; then
            success "$pkg_name built successfully"
        else
            error "Failed to build $pkg_name. Check $LOGDEST/$pkg_name.log"
        fi
    else
        if eval "$makepkg_cmd" 2>&1 | tee "$LOGDEST/$pkg_name.log"; then
            success "$pkg_name built successfully"
        else
            error "Failed to build $pkg_name. Check $LOGDEST/$pkg_name.log"
        fi
    fi
}

# Build all packages in order
build_all_packages() {
    log "Building all packages..."
    
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
    
    log "Creating local package repository..."
    cd "$PKG_DEST"
    repo-add aerofruitos.db.tar.gz *.pkg.tar.zst 2>/dev/null || true
    success "Local repository created"
}

# Build ISO
build_iso() {
    log "Building ISO with archiso..."
    
    cd "$PROJECT_ROOT/iso"
    
    mkdir -p work/airootfs/var/cache/pacman/aerofruitos
    cp "$PKG_DEST"/*.pkg.tar.zst work/airootfs/var/cache/pacman/aerofruitos/ 2>/dev/null || true
    
    # mkarchiso needs to run as root (we are root in Docker, or use sudo locally)
    $SUDO mkarchiso -v -w "$BUILD_DIR/archiso-work" -o "$ISO_OUT" . 2>&1 | tee "$LOGDEST/iso-build.log"
    
    local iso_file=$(find "$ISO_OUT" -name "aerofruitos-*.iso" -type f | head -1)
    
    if [[ -f "$iso_file" ]]; then
        success "ISO built successfully!"
        log "ISO location: $iso_file"
        
        cd "$(dirname "$iso_file")"
        sha256sum "$(basename "$iso_file")" > "$(basename "$iso_file").sha256"
        log "SHA256: $(cat "$(basename "$iso_file").sha256")"
    else
        error "ISO not found in output directory"
    fi
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
        clean)
            log "Cleaning build artifacts..."
            rm -rf "$BUILD_DIR"
            find "$PROJECT_ROOT/packages" -name "*.pkg.tar.zst" -delete
            find "$PROJECT_ROOT/packages" -name "*.pkg.tar.xz" -delete
            find "$PROJECT_ROOT/packages" -name "*.log" -delete
            find "$PROJECT_ROOT/packages" -name "pkg" -type d -exec rm -rf {} + 2>/dev/null || true
            find "$PROJECT_ROOT/packages" -name "src" -type d -exec rm -rf {} + 2>/dev/null || true
            success "Clean complete"
            ;;
        help|--help|-h)
            cat << EOF
Aerofruitos Build Script

Usage: $0 [command]

Commands:
  build       Build all packages and ISO (default)
  packages    Build packages only
  iso         Build ISO only (requires packages)
  clean       Clean build artifacts
  help        Show this help
EOF
            ;;
        *)
            error "Unknown command: $cmd. Use '$0 help' for usage."
            ;;
    esac
}

main "$@"