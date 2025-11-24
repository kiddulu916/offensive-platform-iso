#!/usr/bin/env python3
"""
Tool Availability Checker
Checks which security tools are installed and available
"""

import sys
import os
import subprocess
import shutil

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.registry import ToolRegistry


def check_tool_available(executable: str) -> bool:
    """Check if a tool is available in PATH"""
    # Try using shutil.which first (more reliable)
    if shutil.which(executable):
        return True

    # Fallback: try running with --version or --help
    try:
        subprocess.run(
            [executable, "--version"],
            capture_output=True,
            timeout=5,
            check=False
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            subprocess.run(
                [executable, "--help"],
                capture_output=True,
                timeout=5,
                check=False
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def main():
    """Check all registered tools"""
    print("=" * 70)
    print(" SECURITY TOOLS AVAILABILITY CHECK")
    print("=" * 70)
    print()

    registry = ToolRegistry()
    tools = registry.list_tools()

    print(f"Checking {len(tools)} registered tools...\n")

    available = []
    missing = []

    for tool_info in tools:
        tool = registry.get_tool(tool_info['name'])
        metadata = tool.get_metadata()

        executable = metadata.executable
        is_available = check_tool_available(executable)

        status = "OK  " if is_available else "MISS"
        symbol = "[+]" if is_available else "[-]"

        print(f"{symbol} {status} | {metadata.name:15} | Executable: {executable}")

        if is_available:
            available.append(metadata.name)
        else:
            missing.append({
                'name': metadata.name,
                'executable': executable,
                'category': metadata.category.value
            })

    print()
    print("=" * 70)
    print(" SUMMARY")
    print("=" * 70)

    print(f"\nAvailable: {len(available)}/{len(tools)}")
    if available:
        for name in available:
            print(f"  + {name}")

    print(f"\nMissing: {len(missing)}/{len(tools)}")
    if missing:
        for tool in missing:
            print(f"  - {tool['name']} ({tool['executable']}) - {tool['category']}")

    if missing:
        print("\n" + "=" * 70)
        print(" INSTALLATION INSTRUCTIONS")
        print("=" * 70)
        print("\nTo install missing tools:\n")

        # Group by installation method
        go_tools = []
        apt_tools = []
        other_tools = []

        for tool in missing:
            exe = tool['executable']
            if exe in ['subfinder', 'nuclei', 'httpx', 'ffuf']:
                go_tools.append(exe)
            elif exe in ['nmap', 'gobuster', 'sqlmap', 'amass']:
                apt_tools.append(exe)
            else:
                other_tools.append(exe)

        if go_tools:
            print("Go-based tools (install with go):")
            for tool in go_tools:
                if tool == 'subfinder':
                    print(f"  go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
                elif tool == 'nuclei':
                    print(f"  go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest")
                elif tool == 'httpx':
                    print(f"  go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest")
                elif tool == 'ffuf':
                    print(f"  go install github.com/ffuf/ffuf/v2@latest")
            print()

        if apt_tools:
            print("APT-based tools (Linux):")
            for tool in apt_tools:
                print(f"  sudo apt install {tool}")
            print()

            print("Or download from:")
            for tool in apt_tools:
                if tool == 'nmap':
                    print(f"  nmap: https://nmap.org/download.html")
                elif tool == 'gobuster':
                    print(f"  gobuster: https://github.com/OJ/gobuster/releases")
                elif tool == 'sqlmap':
                    print(f"  sqlmap: https://github.com/sqlmapproject/sqlmap")
                elif tool == 'amass':
                    print(f"  amass: https://github.com/owasp-amass/amass/releases")
            print()

        print("After installation, ensure tools are in your system PATH.")
        print("You can verify by running: python check_tools.py")

    print()

    # Exit code: 0 if all tools available, 1 if any missing
    return 0 if len(missing) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
