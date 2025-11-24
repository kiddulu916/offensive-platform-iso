#!/bin/bash

set -e

#####################################
# Kali-Config Directory Setup Script
# Creates all necessary files and directories for ISO building
#####################################

PROJECT_ROOT="$(pwd)"
CONFIG_DIR="$PROJECT_ROOT/kali-config"
APP_DIR="$PROJECT_ROOT/platform-app"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
check_directory() {
    if [ ! -d "$APP_DIR" ]; then
        log_error "platform-app directory not found. Please run this script from the project root."
        exit 1
    fi
    
    log_info "Project root: $PROJECT_ROOT"
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."
    
    mkdir -p "$CONFIG_DIR/variant-offensive/package-lists"
    mkdir -p "$CONFIG_DIR/variant-offensive/hooks/normal"
    mkdir -p "$CONFIG_DIR/variant-offensive/hooks/live"
    mkdir -p "$CONFIG_DIR/variant-offensive/includes.chroot/etc/lightdm/lightdm.conf.d"
    mkdir -p "$CONFIG_DIR/variant-offensive/includes.chroot/etc/systemd/system"
    mkdir -p "$CONFIG_DIR/variant-offensive/includes.chroot/home/platform/.config/openbox"
    mkdir -p "$CONFIG_DIR/variant-offensive/includes.chroot/usr/local/bin"
    mkdir -p "$CONFIG_DIR/variant-offensive/includes.chroot/opt/offensive-platform"
    
    log_info "Directory structure created"
}

# Create package list
create_package_list() {
    log_info "Creating package list..."
    
    cat > "$CONFIG_DIR/variant-offensive/package-lists/kali.list.chroot" << 'EOF'
# ============================================================================
# Offensive Security Platform - Package List
# ============================================================================

# Core Kali packages
kali-linux-core
kali-defaults
kali-menu

# Minimal desktop environment
xorg
xinit
openbox
lightdm
lightdm-gtk-greeter
lightdm-gtk-greeter-settings
xterm
feh
unclutter
lxappearance

# Network management
network-manager
network-manager-gnome

# System utilities
openssh-server
openssh-client
curl
wget
git
vim
nano
htop
tmux
screen
rsync
sudo

# Programming languages and build tools
python3
python3-pip
python3-venv
python3-dev
python3-setuptools
python3-wheel
python3-pyqt5
python3-pyqt5.qtwebengine
python3-pyqt5.qtsvg
golang-go
build-essential
make
gcc
g++

# Database and task queue
redis-server
sqlite3

# Python libraries (system)
python3-sqlalchemy
python3-pydantic
python3-bcrypt
python3-jwt

# Security Tools - Reconnaissance
nmap
masscan
amass
sublist3r
whatweb
whois
dnsutils
dnsrecon
dnsenum
fierce

# Security Tools - Web scanning
gobuster
ffuf
dirb
wfuzz
nikto
wpscan

# Security Tools - Vulnerability assessment
nuclei
burpsuite
zaproxy

# Security Tools - Exploitation
metasploit-framework
sqlmap
hashcat
john
hydra

# Security Tools - Network
netcat-openbsd
socat
mitmproxy
wireshark
tcpdump
ncat
proxychains4

# Security Tools - Web
chromium
firefox-esr

# Additional utilities
jq
yq
bat
ripgrep
fd-find
tree
ncdu

# Certificate management
ca-certificates
openssl

# Wordlists
wordlists
seclists
EOF

    log_info "Package list created"
}

# Create hook: Install Go tools
create_hook_go_tools() {
    log_info "Creating Go tools installation hook..."
    
    cat > "$CONFIG_DIR/variant-offensive/hooks/normal/0100-install-go-tools.hook.chroot" << 'EOF'
#!/bin/bash
set -e

echo "============================================"
echo "  Installing Go-based Security Tools"
echo "============================================"

# Set up Go environment
export GOPATH=/opt/go
export GOBIN=/opt/go/bin
export PATH=$PATH:/usr/local/go/bin:$GOBIN
mkdir -p $GOPATH $GOBIN

# Verify Go installation
if ! command -v go &> /dev/null; then
    echo "ERROR: Go is not installed"
    exit 1
fi

echo "Go version: $(go version)"

# Install subfinder
echo "[1/8] Installing subfinder..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>&1 | grep -v "go: downloading" || true

# Install httpx
echo "[2/8] Installing httpx..."
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest 2>&1 | grep -v "go: downloading" || true

# Install katana
echo "[3/8] Installing katana..."
go install -v github.com/projectdiscovery/katana/cmd/katana@latest 2>&1 | grep -v "go: downloading" || true

# Install naabu
echo "[4/8] Installing naabu..."
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest 2>&1 | grep -v "go: downloading" || true

# Install dnsx
echo "[5/8] Installing dnsx..."
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest 2>&1 | grep -v "go: downloading" || true

# Install assetfinder
echo "[6/8] Installing assetfinder..."
go install -v github.com/tomnomnom/assetfinder@latest 2>&1 | grep -v "go: downloading" || true

# Install waybackurls
echo "[7/8] Installing waybackurls..."
go install -v github.com/tomnomnom/waybackurls@latest 2>&1 | grep -v "go: downloading" || true

# Install gau (Get All URLs)
echo "[8/8] Installing gau..."
go install -v github.com/lc/gau/v2/cmd/gau@latest 2>&1 | grep -v "go: downloading" || true

# Copy binaries to system path
echo "Copying Go binaries to /usr/local/bin..."
if [ -d "$GOBIN" ]; then
    cp -v $GOBIN/* /usr/local/bin/ || true
fi

# Verify installations
echo ""
echo "Verifying Go tool installations..."
for tool in subfinder httpx katana naabu dnsx assetfinder waybackurls gau; do
    if command -v $tool &> /dev/null; then
        echo "  ✓ $tool installed"
    else
        echo "  ✗ $tool NOT found"
    fi
done

echo ""
echo "Go tools installation complete"
EOF

    chmod +x "$CONFIG_DIR/variant-offensive/hooks/normal/0100-install-go-tools.hook.chroot"
    log_info "Go tools hook created"
}

# Create hook: Install Python tools
create_hook_python_tools() {
    log_info "Creating Python tools installation hook..."
    
    cat > "$CONFIG_DIR/variant-offensive/hooks/normal/0200-install-python-tools.hook.chroot" << 'EOF'
#!/bin/bash
set -e

echo "============================================"
echo "  Installing Python-based Security Tools"
echo "============================================"

# Install XSStrike
echo "[1/3] Installing XSStrike..."
cd /opt
if [ -d "XSStrike" ]; then
    rm -rf XSStrike
fi
git clone --depth 1 https://github.com/s0md3v/XSStrike.git
cd XSStrike
pip3 install --break-system-packages -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt
echo "#!/bin/bash" > /usr/local/bin/xsstrike
echo "cd /opt/XSStrike && python3 xsstrike.py \"\$@\"" >> /usr/local/bin/xsstrike
chmod +x /usr/local/bin/xsstrike

# Install CMSeek
echo "[2/3] Installing CMSeek..."
cd /opt
if [ -d "CMSeeK" ]; then
    rm -rf CMSeeK
fi
git clone --depth 1 https://github.com/Tuhinshubhra/CMSeeK.git
cd CMSeeK
pip3 install --break-system-packages -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt
echo "#!/bin/bash" > /usr/local/bin/cmseek
echo "cd /opt/CMSeeK && python3 cmseek.py \"\$@\"" >> /usr/local/bin/cmseek
chmod +x /usr/local/bin/cmseek

# Install censys CLI
echo "[3/3] Installing censys..."
pip3 install --break-system-packages censys 2>/dev/null || pip3 install censys

# Verify installations
echo ""
echo "Verifying Python tool installations..."
if [ -f /usr/local/bin/xsstrike ]; then
    echo "  ✓ XSStrike installed"
fi
if [ -f /usr/local/bin/cmseek ]; then
    echo "  ✓ CMSeek installed"
fi
if command -v censys &> /dev/null; then
    echo "  ✓ censys installed"
fi

echo ""
echo "Python tools installation complete"
EOF

    chmod +x "$CONFIG_DIR/variant-offensive/hooks/normal/0200-install-python-tools.hook.chroot"
    log_info "Python tools hook created"
}

# Create hook: Install massDNS
create_hook_massdns() {
    log_info "Creating massDNS installation hook..."
    
    cat > "$CONFIG_DIR/variant-offensive/hooks/normal/0250-install-massdns.hook.chroot" << 'EOF'
#!/bin/bash
set -e

echo "============================================"
echo "  Installing massDNS"
echo "============================================"

cd /opt
if [ -d "massdns" ]; then
    rm -rf massdns
fi

git clone --depth 1 https://github.com/blechschmidt/massdns.git
cd massdns
make
cp bin/massdns /usr/local/bin/

if command -v massdns &> /dev/null; then
    echo "✓ massDNS installed successfully"
else
    echo "✗ massDNS installation failed"
fi
EOF

    chmod +x "$CONFIG_DIR/variant-offensive/hooks/normal/0250-install-massdns.hook.chroot"
    log_info "massDNS hook created"
}

# Create hook: Install application
create_hook_install_app() {
    log_info "Creating application installation hook..."
    
    cat > "$CONFIG_DIR/variant-offensive/hooks/normal/0300-install-application.hook.chroot" << 'EOF'
#!/bin/bash
set -e

echo "============================================"
echo "  Installing Offensive Platform Application"
echo "============================================"

cd /opt/offensive-platform

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found"
    exit 1
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
deactivate

# Create start script
echo "Creating start script..."
cat > /opt/offensive-platform/start.sh << 'STARTSCRIPT'
#!/bin/bash

# Navigate to app directory
cd /opt/offensive-platform

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export QT_QPA_PLATFORM=xcb
export DISPLAY=:0
export XAUTHORITY=/home/platform/.Xauthority

# Launch application in fullscreen
python3 main.py --fullscreen

# Restart on crash
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Application exited with code $exit_code. Restarting in 5 seconds..."
    sleep 5
    exec /opt/offensive-platform/start.sh
fi
STARTSCRIPT

chmod +x /opt/offensive-platform/start.sh

# Set permissions
chown -R root:root /opt/offensive-platform
chmod -R 755 /opt/offensive-platform

# Make main.py executable
if [ -f "/opt/offensive-platform/main.py" ]; then
    chmod +x /opt/offensive-platform/main.py
fi

echo "✓ Application installation complete"
EOF

    chmod +x "$CONFIG_DIR/variant-offensive/hooks/normal/0300-install-application.hook.chroot"
    log_info "Application installation hook created"
}

# Create hook: System configuration
create_hook_system_config() {
    log_info "Creating system configuration hook..."
    
    cat > "$CONFIG_DIR/variant-offensive/hooks/normal/0400-configure-system.hook.chroot" << 'EOF'
#!/bin/bash
set -e

echo "============================================"
echo "  Configuring System"
echo "============================================"

# Create platform user
echo "[1/6] Creating platform user..."
if ! id -u platform > /dev/null 2>&1; then
    useradd -m -s /bin/bash -G sudo,netdev,audio,video platform
    echo "platform:platform" | chpasswd
    echo "✓ User 'platform' created"
else
    echo "✓ User 'platform' already exists"
fi

# Configure sudo (allow platform user to run commands without password for security tools)
echo "[2/6] Configuring sudo..."
echo "platform ALL=(ALL) NOPASSWD: /usr/bin/nmap, /usr/bin/masscan, /usr/local/bin/naabu" > /etc/sudoers.d/platform-tools
chmod 0440 /etc/sudoers.d/platform-tools

# Set proper ownership for home directory
chown -R platform:platform /home/platform

# Configure SSH (disable root login)
echo "[3/6] Configuring SSH..."
if [ -f /etc/ssh/sshd_config ]; then
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    systemctl enable ssh || true
fi

# Enable Redis
echo "[4/6] Enabling Redis..."
systemctl enable redis-server || true

# Configure NetworkManager
echo "[5/6] Configuring NetworkManager..."
systemctl enable NetworkManager || true

# Clean up
echo "[6/6] Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/*
rm -rf /var/tmp/*

echo ""
echo "✓ System configuration complete"
EOF

    chmod +x "$CONFIG_DIR/variant-offensive/hooks/normal/0400-configure-system.hook.chroot"
    log_info "System configuration hook created"
}

# Create hook: Auto-update configuration
create_hook_autoupdate() {
    log_info "Creating auto-update configuration hook..."
    
    cat > "$CONFIG_DIR/variant-offensive/hooks/normal/0500-configure-autoupdate.hook.chroot" << 'EOF'
#!/bin/bash
set -e

echo "============================================"
echo "  Configuring Auto-Update System"
echo "============================================"

# Create update script
cat > /usr/local/bin/platform-update.sh << 'UPDATESCRIPT'
#!/bin/bash

LOG_FILE="/var/log/platform-update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "===== Starting Platform Update ====="

# Update system packages
log "Updating system packages..."
apt update >> "$LOG_FILE" 2>&1
apt upgrade -y >> "$LOG_FILE" 2>&1

# Update Go-based tools
log "Updating Go-based tools..."
export GOPATH=/opt/go
export GOBIN=/opt/go/bin
export PATH=$PATH:/usr/local/go/bin:$GOBIN

go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest >> "$LOG_FILE" 2>&1 || true
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest >> "$LOG_FILE" 2>&1 || true
go install -v github.com/projectdiscovery/katana/cmd/katana@latest >> "$LOG_FILE" 2>&1 || true
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest >> "$LOG_FILE" 2>&1 || true
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest >> "$LOG_FILE" 2>&1 || true

if [ -d "$GOBIN" ]; then
    cp $GOBIN/* /usr/local/bin/ 2>/dev/null || true
fi

# Update Metasploit Framework
log "Updating Metasploit Framework..."
msfupdate >> "$LOG_FILE" 2>&1 || log "Metasploit update skipped"

# Update Nuclei templates
log "Updating Nuclei templates..."
nuclei -update-templates >> "$LOG_FILE" 2>&1 || log "Nuclei update skipped"

# Update application if it's a git repository
if [ -d /opt/offensive-platform/.git ]; then
    log "Updating platform application..."
    cd /opt/offensive-platform
    git pull >> "$LOG_FILE" 2>&1 || true
    source venv/bin/activate
    pip install --upgrade -r requirements.txt >> "$LOG_FILE" 2>&1 || true
    deactivate
fi

log "===== Platform Update Complete ====="
UPDATESCRIPT

chmod +x /usr/local/bin/platform-update.sh

# Create systemd timer
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

# Create systemd service
cat > /etc/systemd/system/platform-update.service << 'SERVICE'
[Unit]
Description=Platform Auto-Update Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/platform-update.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Enable the timer
systemctl enable platform-update.timer

echo "✓ Auto-update system configured"
EOF

    chmod +x "$CONFIG_DIR/variant-offensive/hooks/normal/0500-configure-autoupdate.hook.chroot"
    log_info "Auto-update configuration hook created"
}

# Create LightDM configuration
create_lightdm_config() {
    log_info "Creating LightDM configuration..."
    
    cat > "$CONFIG_DIR/variant-offensive/includes.chroot/etc/lightdm/lightdm.conf.d/10-offensive-platform.conf" << 'EOF'
# Offensive Platform LightDM Configuration
# Auto-login to platform user with Openbox session

[Seat:*]
autologin-user=platform
autologin-user-timeout=0
user-session=openbox
greeter-session=lightdm-gtk-greeter
EOF

    log_info "LightDM configuration created"
}

# Create Openbox configuration
create_openbox_config() {
    log_info "Creating Openbox configuration..."
    
    # Autostart
    cat > "$CONFIG_DIR/variant-offensive/includes.chroot/home/platform/.config/openbox/autostart" << 'EOF'
#!/bin/bash

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor after short inactivity
unclutter -idle 0.1 -root &

# Set background to dark
xsetroot -solid "#1a1a1a"

# Load background image if exists
if [ -f /opt/offensive-platform/resources/background.png ]; then
    feh --bg-scale /opt/offensive-platform/resources/background.png &
fi

# Launch platform application
/opt/offensive-platform/start.sh &
EOF

    # RC.xml
    cat > "$CONFIG_DIR/variant-offensive/includes.chroot/home/platform/.config/openbox/rc.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <resistance>
    <strength>10</strength>
    <screen_edge_strength>20</screen_edge_strength>
  </resistance>
  
  <focus>
    <focusNew>yes</focusNew>
    <followMouse>no</followMouse>
  </focus>
  
  <placement>
    <policy>Smart</policy>
  </placement>
  
  <theme>
    <name>Clearlooks</name>
    <titleLayout>NLIMC</titleLayout>
  </theme>
  
  <desktops>
    <number>1</number>
  </desktops>
  
  <applications>
    <application class="*">
      <decor>no</decor>
      <maximized>yes</maximized>
      <fullscreen>yes</fullscreen>
    </application>
  </applications>
  
  <keyboard>
    <!-- Disable Alt+F4 to prevent accidental closure -->
    <keybind key="A-F4">
      <action name="Execute">
        <execute>true</execute>
      </action>
    </keybind>
    
    <!-- Emergency exit still available via Ctrl+Alt+Q (handled by app) -->
  </keyboard>
  
  <mouse>
    <dragThreshold>8</dragThreshold>
    <doubleClickTime>200</doubleClickTime>
  </mouse>
</openbox_config>
EOF

    log_info "Openbox configuration created"
}

# Create systemd service for platform
create_systemd_service() {
    log_info "Creating systemd service..."
    
    cat > "$CONFIG_DIR/variant-offensive/includes.chroot/etc/systemd/system/offensive-platform.service" << 'EOF'
[Unit]
Description=Offensive Security Platform
Documentation=https://github.com/yourusername/offensive-platform
After=graphical.target lightdm.service redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=platform
Group=platform
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/platform/.Xauthority"
Environment="QT_QPA_PLATFORM=xcb"
WorkingDirectory=/opt/offensive-platform
ExecStart=/opt/offensive-platform/start.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=graphical.target
EOF

    log_info "Systemd service created"
}

# Copy application files
copy_application_files() {
    log_info "Copying application files..."
    
    if [ ! -d "$APP_DIR" ]; then
        log_error "Application directory not found: $APP_DIR"
        return 1
    fi
    
    # Remove old files
    rm -rf "$CONFIG_DIR/variant-offensive/includes.chroot/opt/offensive-platform"/*
    
    # Copy application
    cp -r "$APP_DIR"/* "$CONFIG_DIR/variant-offensive/includes.chroot/opt/offensive-platform/"
    
    # Create placeholder background if it doesn't exist
    mkdir -p "$CONFIG_DIR/variant-offensive/includes.chroot/opt/offensive-platform/resources"
    if [ ! -f "$CONFIG_DIR/variant-offensive/includes.chroot/opt/offensive-platform/resources/background.png" ]; then
        # Create a simple 1x1 black pixel PNG
        echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "$CONFIG_DIR/variant-offensive/includes.chroot/opt/offensive-platform/resources/background.png"
    fi
    
    log_info "Application files copied"
}

# Create README
create_readme() {
    log_info "Creating README..."
    
    cat > "$CONFIG_DIR/README.md" << 'EOF'
# Kali-Config Directory

This directory contains all configuration files for building the Offensive Security Platform custom Kali Linux ISO.

## Structure
```
kali-config/
└── variant-offensive/
    ├── package-lists/          # List of packages to install
    ├── hooks/
    │   └── normal/            # Post-installation hooks
    ├── includes.chroot/       # Files to include in the live system
    │   ├── etc/              # System configuration files
    │   ├── home/             # Home directory files
    │   ├── opt/              # Application files
    │   └── usr/              # Additional binaries and scripts
    └── README.md             # This file
```

## Hooks

Hooks are executed during the build process in alphabetical order:

1. **0100-install-go-tools.hook.chroot** - Installs Go-based security tools
2. **0200-install-python-tools.hook.chroot** - Installs Python-based security tools
3. **0250-install-massdns.hook.chroot** - Installs massDNS
4. **0300-install-application.hook.chroot** - Installs the platform application
5. **0400-configure-system.hook.chroot** - Configures the system
6. **0500-configure-autoupdate.hook.chroot** - Sets up auto-update

## Building

After running `setup-kali-config.sh`, you can build the ISO with:
```bash
sudo ./build.sh
```

## Customization

To customize the build:

1. Edit `package-lists/kali.list.chroot` to add/remove packages
2. Modify hooks to change installation behavior
3. Add files to `includes.chroot/` to include them in the ISO
4. Update application files in `platform-app/` and re-run setup script

## Default Credentials

- Username: `platform`
- Password: `platform`

**Change these on first boot!**
EOF

    log_info "README created"
}

# Create verification script
create_verify_script() {
    log_info "Creating verification script..."
    
    cat > "$CONFIG_DIR/verify-config.sh" << 'EOF'
#!/bin/bash

echo "Verifying Kali-Config structure..."
echo ""

errors=0

# Check directories
dirs=(
    "variant-offensive"
    "variant-offensive/package-lists"
    "variant-offensive/hooks/normal"
    "variant-offensive/includes.chroot/etc"
    "variant-offensive/includes.chroot/opt/offensive-platform"
)

for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir"
    else
        echo "✗ $dir (missing)"
        ((errors++))
    fi
done

echo ""

# Check files
files=(
    "variant-offensive/package-lists/kali.list.chroot"
    "variant-offensive/hooks/normal/0100-install-go-tools.hook.chroot"
    "variant-offensive/hooks/normal/0200-install-python-tools.hook.chroot"
    "variant-offensive/hooks/normal/0300-install-application.hook.chroot"
    "variant-offensive/hooks/normal/0400-configure-system.hook.chroot"
    "variant-offensive/includes.chroot/etc/lightdm/lightdm.conf.d/10-offensive-platform.conf"
    "variant-offensive/includes.chroot/home/platform/.config/openbox/autostart"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (missing)"
        ((errors++))
    fi
done

echo ""

# Check application files
if [ -d "variant-offensive/includes.chroot/opt/offensive-platform/app" ]; then
    echo "✓ Application files present"
else
    echo "✗ Application files missing"
    ((errors++))
fi

echo ""

if [ $errors -eq 0 ]; then
    echo "All checks passed! ✓"
    exit 0
else
    echo "Found $errors error(s) ✗"
    exit 1
fi
EOF

    chmod +x "$CONFIG_DIR/verify-config.sh"
    log_info "Verification script created"
}

# Main execution
main() {
    echo ""
    echo "============================================"
    echo "  Kali-Config Setup Script"
    echo "  Offensive Security Platform"
    echo "============================================"
    echo ""
    
    check_directory
    create_directories
    create_package_list
    create_hook_go_tools
    create_hook_python_tools
    create_hook_massdns
    create_hook_install_app
    create_hook_system_config
    create_hook_autoupdate
    create_lightdm_config
    create_openbox_config
    create_systemd_service
    copy_application_files
    create_readme
    create_verify_script
    
    echo ""
    echo "============================================"
    echo "  Setup Complete!"
    echo "============================================"
    echo ""
    echo "Configuration directory: $CONFIG_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Review the configuration files in kali-config/"
    echo "  2. Verify the setup: cd kali-config && ./verify-config.sh"
    echo "  3. Build the ISO: sudo ./build.sh"
    echo ""
    echo "For more information, see kali-config/README.md"
    echo ""
}

# Run main
main