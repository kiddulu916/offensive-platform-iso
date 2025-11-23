# Required Security Tools

This document lists the security tools required by the Offensive Security Platform and how to install them.

## Quick Check

To check which tools are installed:

```bash
python check_tools.py
```

This will show you which tools are available and which are missing.

## Required Tools

The platform integrates with the following security testing tools:

### 1. Nmap (Network Scanner)
- **Purpose:** Port scanning, service detection, OS fingerprinting
- **Category:** Scanning
- **Installation:**
  - **Windows:** Download from https://nmap.org/download.html
  - **Linux:** `sudo apt install nmap`
  - **macOS:** `brew install nmap`

### 2. Subfinder (Subdomain Enumeration)
- **Purpose:** Passive subdomain discovery
- **Category:** Reconnaissance
- **Installation:**
  ```bash
  go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
  ```
- **Requirements:** Go 1.19+
- **Verify:** `subfinder -version`

### 3. Nuclei (Vulnerability Scanner)
- **Purpose:** Fast vulnerability scanning using templates
- **Category:** Scanning
- **Installation:**
  ```bash
  go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
  ```
- **Requirements:** Go 1.19+
- **Verify:** `nuclei -version`

### 4. httpx (HTTP Toolkit)
- **Purpose:** Fast HTTP probing, web server detection
- **Category:** Reconnaissance
- **Installation:**
  ```bash
  go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
  ```
- **Requirements:** Go 1.19+
- **Verify:** `httpx -version`

### 5. ffuf (Fuzzer)
- **Purpose:** Fast web fuzzer for directory/file discovery
- **Category:** Enumeration
- **Installation:**
  ```bash
  go install github.com/ffuf/ffuf/v2@latest
  ```
- **Requirements:** Go 1.19+
- **Verify:** `ffuf -V`

### 6. Gobuster (Directory Brute Forcer)
- **Purpose:** Directory/file brute forcing, DNS enumeration
- **Category:** Enumeration
- **Installation:**
  - **Linux:** `sudo apt install gobuster`
  - **From source:** https://github.com/OJ/gobuster/releases
- **Verify:** `gobuster version`

### 7. SQLMap (SQL Injection Tool)
- **Purpose:** Automated SQL injection testing
- **Category:** Exploitation
- **Installation:**
  - **Linux:** `sudo apt install sqlmap`
  - **From source:** `git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git`
- **Verify:** `sqlmap --version`

### 8. Amass (OWASP Network Mapping)
- **Purpose:** Advanced subdomain enumeration and network mapping
- **Category:** Reconnaissance
- **Installation:**
  - **Linux:** `sudo apt install amass`
  - **From releases:** https://github.com/owasp-amass/amass/releases
- **Verify:** `amass -version`

## Installation Prerequisites

### Go (Required for ProjectDiscovery tools)

Most tools require Go 1.19 or higher. Install Go:

**Windows:**
1. Download from https://go.dev/dl/
2. Run installer
3. Verify: `go version`

**Linux:**
```bash
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
source ~/.bashrc
go version
```

**macOS:**
```bash
brew install go
```

### Adding Tools to PATH

After installing tools, ensure they're in your system PATH:

**Windows:**
1. Go tools are automatically added to `%USERPROFILE%\go\bin`
2. Add this to your PATH via System Environment Variables
3. Or add manually: `C:\Users\YourName\go\bin`

**Linux/macOS:**
```bash
# Go tools are in ~/go/bin
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
source ~/.bashrc
```

## Quick Install Script (Linux/macOS)

```bash
#!/bin/bash

# Install Go tools
echo "Installing Go-based tools..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/ffuf/ffuf/v2@latest

# Install system tools (Debian/Ubuntu)
echo "Installing system tools..."
sudo apt update
sudo apt install -y nmap gobuster sqlmap

# Download Amass
echo "Installing Amass..."
wget https://github.com/owasp-amass/amass/releases/download/v4.2.0/amass_Linux_amd64.zip
unzip amass_Linux_amd64.zip
sudo mv amass_Linux_amd64/amass /usr/local/bin/
rm -rf amass_Linux_amd64*

echo "Done! Verify installation with: python check_tools.py"
```

## Verification

After installation, run the availability checker:

```bash
python check_tools.py
```

**Expected output:**
```
==================================================================
 SECURITY TOOLS AVAILABILITY CHECK
==================================================================

Checking 8 registered tools...

[+] OK   | nmap            | Executable: nmap
[+] OK   | subfinder       | Executable: subfinder
[+] OK   | nuclei          | Executable: nuclei
[+] OK   | httpx           | Executable: httpx
[+] OK   | ffuf            | Executable: ffuf
[+] OK   | gobuster        | Executable: gobuster
[+] OK   | sqlmap          | Executable: sqlmap
[+] OK   | amass           | Executable: amass

==================================================================
 SUMMARY
==================================================================

Available: 8/8
```

## Troubleshooting

### Tool not found after installation

**Problem:** Tool installed but shows as missing

**Solution:**
1. Verify tool is in PATH: `which toolname` (Linux/macOS) or `where toolname` (Windows)
2. Restart your terminal/command prompt
3. On Windows, restart the application
4. Check PATH environment variable includes the tool directory

### Go tools not found

**Problem:** Go tools installed but not in PATH

**Solution:**
```bash
# Linux/macOS
export PATH=$PATH:$HOME/go/bin

# Windows (PowerShell)
$env:Path += ";$env:USERPROFILE\go\bin"
```

Add permanently to your shell profile or environment variables.

### Permission denied

**Problem:** Cannot execute tool (Linux/macOS)

**Solution:**
```bash
chmod +x /path/to/tool
```

## Running Without All Tools

The platform will continue to work even if some tools are missing. Tasks using missing tools will fail with a clear error message:

```
Tool 'subfinder' not found. Please ensure subfinder is installed and available in PATH.
```

However, for full functionality, all 8 tools should be installed.

## Docker Alternative (Future)

*Note: Docker support is planned but not yet implemented.*

A future version may include a Docker container with all tools pre-installed:

```bash
docker run -it offensive-platform
```

## Tool Updates

Keep tools updated for latest features and vulnerability signatures:

```bash
# Update Go tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
# ... etc

# Update system tools
sudo apt update && sudo apt upgrade nmap gobuster sqlmap
```

## Minimum Tool Set

For basic functionality, at minimum install:
1. **nmap** - For port scanning
2. **subfinder** - For subdomain enumeration

These two tools will allow you to run basic reconnaissance workflows.

---

**Need Help?** Check the tool-specific documentation:
- Nmap: https://nmap.org/docs.html
- ProjectDiscovery tools: https://docs.projectdiscovery.io/
- Gobuster: https://github.com/OJ/gobuster
- SQLMap: https://github.com/sqlmapproject/sqlmap/wiki
- Amass: https://github.com/owasp-amass/amass/blob/master/doc/user_guide.md
