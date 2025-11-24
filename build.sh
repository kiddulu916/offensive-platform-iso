#!/bin/bash

set -e

#####################################
# Offensive Platform ISO Builder
# Using Kali Live-Build Official Method
#####################################

PROJECT_NAME="offensive-platform"
VERSION="1.0.0"
BUILD_DIR="$(pwd)/live-build-config"
CONFIG_DIR="$(pwd)/kali-config"
APP_DIR="$(pwd)/platform-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        log_info "Please run: sudo $0"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if running on Debian/Kali
    if [ ! -f /etc/debian_version ]; then
        log_error "This script must run on Debian-based system (preferably Kali)"
        exit 1
    fi
    
    # Check available disk space (need at least 20GB)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 20 ]; then
        log_error "Insufficient disk space. Need at least 20GB free."
        exit 1
    fi
    
    log_info "System requirements met"
}

# Install build dependencies
install_dependencies() {
    log_info "Installing build dependencies..."
    
    apt update
    apt install -y \
        git \
        live-build \
        cdebootstrap \
        curl \
        wget \
        ca-certificates \
        gnupg
    
    log_info "Dependencies installed"
}

# Setup build environment
setup_build_environment() {
    log_info "Setting up build environment..."
    
    # Clean previous build
    if [ -d "$BUILD_DIR" ]; then
        log_warn "Removing previous build directory..."
        rm -rf "$BUILD_DIR"
    fi
    
    # Create build directory
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Copy Kali configuration if we're on Kali
    if [ -d /usr/share/kali-defaults/live-build-config ]; then
        log_info "Copying Kali live-build configuration..."
        cp -r /usr/share/kali-defaults/live-build-config/* .
    else
        log_info "Initializing live-build configuration..."
        lb config
    fi
    
    log_info "Build environment ready"
}

# Configure live-build
configure_live_build() {
    log_info "Configuring live-build..."
    
    cd "$BUILD_DIR"
    
    # Run lb config with our custom settings
    lb config noauto \
        --distribution kali-rolling \
        --debian-installer live \
        --debian-installer-gui false \
        --archive-areas "main contrib non-free non-free-firmware" \
        --updates true \
        --security true \
        --backports true \
        --source false \
        --binary-images iso-hybrid \
        --bootappend-live "boot=live components quiet splash" \
        --bootappend-install "auto=true priority=critical" \
        --bootloaders "syslinux,grub-efi" \
        --memtest none \
        --iso-application "$PROJECT_NAME" \
        --iso-preparer "$PROJECT_NAME-builder" \
        --iso-publisher "$PROJECT_NAME" \
        --iso-volume "$PROJECT_NAME-$VERSION" \
        --image-name "$PROJECT_NAME-$VERSION" \
        --linux-flavours amd64 \
        --mode debian \
        --system normal \
        "${@}"
    
    log_info "Live-build configured"
}

# Create package list
create_package_list() {
    log_info "Creating package list..."
    
    mkdir -p "$BUILD_DIR/config/package-lists"
    
    cat > "$BUILD_DIR/config/package-lists/offensive-platform.list.chroot" << 'EOF'
# Core Kali packages
kali-linux-core
kali-desktop-live
kali-tools-top10

# Minimal desktop environment
xorg
openbox
lightdm
lightdm-gtk-greeter
xterm
feh
unclutter

# Network tools
network-manager
network-manager-gnome

# Programming languages and build tools
python3
python3-pip
python3-venv
python3-dev
python3-pyqt5
python3-pyqt5.qtwebengine
python3-pyqt5.qtsvg
golang-go
build-essential

# System utilities
openssh-server
openssh-client
curl
wget
git
vim
nano
htop
redis-server
sqlite3

# Security tools - Reconnaissance
nmap
masscan
amass
sublist3r
whatweb
whois
dnsutils

# Security tools - Web scanning
gobuster
ffuf
dirb
wfuzz
nikto

# Security tools - Vulnerability assessment
nuclei
burpsuite
zaproxy

# Security tools - Exploitation
metasploit-framework
sqlmap
hashcat

# Security tools - Network
netcat-openbsd
socat
mitmproxy
wireshark
tcpdump

# Additional utilities
jq
tmux
screen
rsync
EOF

    log_info "Package list created"
}

# Create installation hooks
create_hooks() {
    log_info "Creating installation hooks..."
    
    mkdir -p "$BUILD_DIR/config/hooks/normal"
    
    # Hook 1: Install Go-based tools
    cat > "$BUILD_DIR/config/hooks/normal/0100-install-go-tools.hook.chroot" << 'HOOK1'
#!/bin/bash
set -e

echo "===== Installing Go-based security tools ====="

# Set up Go environment
export GOPATH=/opt/go
export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin
mkdir -p $GOPATH

# Install subfinder
echo "Installing subfinder..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Install httpx
echo "Installing httpx..."
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Install katana
echo "Installing katana..."
go install -v github.com/projectdiscovery/katana/cmd/katana@latest

# Install naabu
echo "Installing naabu..."
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Install dnsx
echo "Installing dnsx..."
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest

# Install assetfinder
echo "Installing assetfinder..."
go install -v github.com/tomnomnom/assetfinder@latest

# Install waybackurls
echo "Installing waybackurls..."
go install -v github.com/tomnomnom/waybackurls@latest

# Install gau (Get All URLs)
echo "Installing gau..."
go install -v github.com/lc/gau/v2/cmd/gau@latest

# Copy binaries to system path
cp $GOPATH/bin/* /usr/local/bin/

echo "Go tools installation complete"
HOOK1

    # Hook 2: Install Python-based tools
    cat > "$BUILD_DIR/config/hooks/normal/0200-install-python-tools.hook.chroot" << 'HOOK2'
#!/bin/bash
set -e

echo "===== Installing Python-based security tools ====="

# Install XSStrike
echo "Installing XSStrike..."
cd /opt
git clone --depth 1 https://github.com/s0md3v/XSStrike.git
cd XSStrike
pip3 install --break-system-packages -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt

# Install CMSeek
echo "Installing CMSeek..."
cd /opt
git clone --depth 1 https://github.com/Tuhinshubhra/CMSeeK.git
cd CMSeeK
pip3 install --break-system-packages -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt

# Install censys CLI
echo "Installing censys..."
pip3 install --break-system-packages censys 2>/dev/null || pip3 install censys

# Create wrapper scripts
cat > /usr/local/bin/xsstrike << 'XSSTRIKE'
#!/bin/bash
cd /opt/XSStrike
python3 xsstrike.py "$@"
XSSTRIKE
chmod +x /usr/local/bin/xsstrike

cat > /usr/local/bin/cmseek << 'CMSEEK'
#!/bin/bash
cd /opt/CMSeeK
python3 cmseek.py "$@"
CMSEEK
chmod +x /usr/local/bin/cmseek

echo "Python tools installation complete"
HOOK2

    # Hook 3: Install massDNS
    cat > "$BUILD_DIR/config/hooks/normal/0250-install-massdns.hook.chroot" << 'HOOK3'
#!/bin/bash
set -e

echo "===== Installing massDNS ====="

cd /opt
git clone --depth 1 https://github.com/blechschmidt/massdns.git
cd massdns
make
cp bin/massdns /usr/local/bin/

echo "massDNS installation complete"
HOOK3

    # Hook 4: Install the platform application
    cat > "$BUILD_DIR/config/hooks/normal/0300-install-application.hook.chroot" << 'HOOK4'
#!/bin/bash
set -e

echo "===== Installing Offensive Platform Application ====="

cd /opt/offensive-platform

# Create virtual environment
python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Create start script
cat > /opt/offensive-platform/start.sh << 'STARTSCRIPT'
#!/bin/bash

cd /opt/offensive-platform
source venv/bin/activate

export QT_QPA_PLATFORM=xcb
export DISPLAY=:0

python3 main.py --fullscreen

# Restart on crash
while true; do
    echo "Application crashed. Restarting in 5 seconds..."
    sleep 5
    python3 main.py --fullscreen
done
STARTSCRIPT

chmod +x /opt/offensive-platform/start.sh

# Set permissions
chown -R root:root /opt/offensive-platform
chmod -R 755 /opt/offensive-platform

echo "Application installation complete"
HOOK4

    # Hook 5: System configuration
    cat > "$BUILD_DIR/config/hooks/normal/0400-configure-system.hook.chroot" << 'HOOK5'
#!/bin/bash
set -e

echo "===== Configuring system ====="

# Create platform user
useradd -m -s /bin/bash -G sudo platform
echo "platform:platform" | chpasswd

# Configure LightDM for auto-login
mkdir -p /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/10-offensive-platform.conf << 'LIGHTDM'
[Seat:*]
autologin-user=platform
autologin-user-timeout=0
user-session=openbox
greeter-session=lightdm-gtk-greeter
LIGHTDM

# Configure Openbox
mkdir -p /home/platform/.config/openbox
cat > /home/platform/.config/openbox/autostart << 'OPENBOX'
# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor after short inactivity
unclutter -idle 0.1 -root &

# Set background
feh --bg-scale /opt/offensive-platform/resources/background.png 2>/dev/null || xsetroot -solid "#1a1a1a"

# Launch platform application
/opt/offensive-platform/start.sh &
OPENBOX

cat > /home/platform/.config/openbox/rc.xml << 'OPENBOXRC'
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <applications>
    <application class="*">
      <decor>no</decor>
      <maximized>yes</maximized>
      <fullscreen>yes</fullscreen>
    </application>
  </applications>
  <keyboard>
    <!-- Disable Alt+F4 -->
    <keybind key="A-F4">
      <action name="Execute">
        <execute>true</execute>
      </action>
    </keybind>
  </keyboard>
</openbox_config>
OPENBOXRC

chown -R platform:platform /home/platform/.config

# Create systemd service for the platform
cat > /etc/systemd/system/offensive-platform.service << 'SERVICE'
[Unit]
Description=Offensive Security Platform
After=graphical.target lightdm.service

[Service]
Type=simple
User=platform
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/platform/.Xauthority"
ExecStart=/opt/offensive-platform/start.sh
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
SERVICE

# Enable the service
systemctl enable offensive-platform.service

# Configure SSH
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl enable ssh

# Configure Redis
systemctl enable redis-server

# Create update script
cat > /usr/local/bin/platform-update.sh << 'UPDATE'
#!/bin/bash

LOG_FILE="/var/log/platform-update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "===== Starting platform update ====="

# Update system packages
log "Updating system packages..."
apt update >> "$LOG_FILE" 2>&1
apt upgrade -y >> "$LOG_FILE" 2>&1

# Update Go tools
log "Updating Go-based tools..."
export GOPATH=/opt/go
export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin

go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest >> "$LOG_FILE" 2>&1
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest >> "$LOG_FILE" 2>&1
go install -v github.com/projectdiscovery/katana/cmd/katana@latest >> "$LOG_FILE" 2>&1
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest >> "$LOG_FILE" 2>&1
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest >> "$LOG_FILE" 2>&1

cp $GOPATH/bin/* /usr/local/bin/

# Update Metasploit
log "Updating Metasploit Framework..."
msfupdate >> "$LOG_FILE" 2>&1

# Update Nuclei templates
log "Updating Nuclei templates..."
nuclei -update-templates >> "$LOG_FILE" 2>&1

# Update application if git repo exists
if [ -d /opt/offensive-platform/.git ]; then
    log "Updating platform application..."
    cd /opt/offensive-platform
    git pull >> "$LOG_FILE" 2>&1
    source venv/bin/activate
    pip install --upgrade -r requirements.txt >> "$LOG_FILE" 2>&1
    deactivate
fi

log "===== Update completed ====="
UPDATE

chmod +x /usr/local/bin/platform-update.sh

# Create systemd timer for updates
cat > /etc/systemd/system/platform-update.timer << 'TIMER'
[Unit]
Description=Platform Auto-Update Timer
Requires=platform-update.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=24h
Persistent=true

[Install]
WantedBy=timers.target
TIMER

cat > /etc/systemd/system/platform-update.service << 'UPDATESERVICE'
[Unit]
Description=Platform Auto-Update Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/platform-update.sh

[Install]
WantedBy=multi-user.target
UPDATESERVICE

# Enable update timer
systemctl enable platform-update.timer

# Clean up
apt clean
rm -rf /var/lib/apt/lists/*

echo "System configuration complete"
HOOK5

    # Make hooks executable
    chmod +x "$BUILD_DIR/config/hooks/normal/"*.hook.chroot
    
    log_info "Hooks created"
}

# Copy application files
copy_application() {
    log_info "Copying application files..."
    
    if [ ! -d "$APP_DIR" ]; then
        log_error "Application directory not found: $APP_DIR"
        exit 1
    fi
    
    mkdir -p "$BUILD_DIR/config/includes.chroot/opt/offensive-platform"
    cp -r "$APP_DIR"/* "$BUILD_DIR/config/includes.chroot/opt/offensive-platform/"
    
    # Create placeholder background if doesn't exist
    mkdir -p "$BUILD_DIR/config/includes.chroot/opt/offensive-platform/resources"
    if [ ! -f "$BUILD_DIR/config/includes.chroot/opt/offensive-platform/resources/background.png" ]; then
        # Create a simple dark background
        convert -size 1920x1080 xc:#1a1a1a "$BUILD_DIR/config/includes.chroot/opt/offensive-platform/resources/background.png" 2>/dev/null || true
    fi
    
    log_info "Application files copied"
}

# Build the ISO
build_iso() {
    log_info "Building ISO image..."
    log_warn "This will take 30-60 minutes depending on your system..."
    
    cd "$BUILD_DIR"
    
    # Clean any previous build
    lb clean --purge
    
    # Build
    lb build 2>&1 | tee build.log
    
    if [ -f "live-image-amd64.hybrid.iso" ]; then
        OUTPUT_ISO="../${PROJECT_NAME}-${VERSION}.iso"
        mv live-image-amd64.hybrid.iso "$OUTPUT_ISO"
        
        # Calculate checksums
        cd ..
        sha256sum "${PROJECT_NAME}-${VERSION}.iso" > "${PROJECT_NAME}-${VERSION}.iso.sha256"
        
        log_info "Build complete!"
        echo ""
        echo "=================================================="
        echo "  ISO file: ${PROJECT_NAME}-${VERSION}.iso"
        echo "  Size: $(du -h ${PROJECT_NAME}-${VERSION}.iso | cut -f1)"
        echo "  SHA256: $(cat ${PROJECT_NAME}-${VERSION}.iso.sha256)"
        echo "=================================================="
        echo ""
        echo "To create a bootable USB:"
        echo "  sudo dd if=${PROJECT_NAME}-${VERSION}.iso of=/dev/sdX bs=4M status=progress && sync"
        echo "  (Replace /dev/sdX with your USB device)"
        echo ""
        
    else
        log_error "Build failed! Check build.log for details"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    cd "$BUILD_DIR"
    lb clean --purge 2>/dev/null || true
}

# Main execution
main() {
    echo ""
    echo "=================================================="
    echo "  Offensive Platform ISO Builder"
    echo "  Version: $VERSION"
    echo "  Using Kali Live-Build Methodology"
    echo "=================================================="
    echo ""
    
    check_root
    check_requirements
    install_dependencies
    setup_build_environment
    configure_live_build
    create_package_list
    create_hooks
    copy_application
    build_iso
    
    log_info "All done!"
}

# Handle errors
trap 'log_error "Build failed at line $LINENO"' ERR

# Run main
main "$@"