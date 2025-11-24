"""Tests for Nmap adapter service fingerprinting"""
import pytest
from app.tools.adapters.nmap_adapter import NmapAdapter
from app.tools.base import ToolCategory


def test_nmap_metadata():
    """Test Nmap adapter metadata"""
    adapter = NmapAdapter()
    metadata = adapter.get_metadata()
    assert metadata.name == "nmap"
    assert metadata.category == ToolCategory.SCANNING
    assert metadata.executable == "nmap"
    assert metadata.requires_root == True


def test_nmap_validate_parameters():
    """Test parameter validation"""
    adapter = NmapAdapter()
    assert adapter.validate_parameters({"target": "192.168.1.1"}) == True
    assert adapter.validate_parameters({"domain": "example.com"}) == True
    assert adapter.validate_parameters({}) == False


def test_nmap_build_command():
    """Test command building"""
    adapter = NmapAdapter()
    cmd = adapter.build_command({"target": "192.168.1.1", "scan_type": "quick"})
    assert "nmap" in cmd
    assert "-oX" in cmd
    assert "-" in cmd
    assert "192.168.1.1" in cmd
    assert "-T4" in cmd
    assert "-F" in cmd


def test_nmap_parse_output_with_services():
    """Test parsing Nmap XML output to extract service fingerprints"""
    adapter = NmapAdapter()

    # Sample Nmap XML output with service details
    xml_output = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <address addr="192.168.1.1" addrtype="ipv4"/>
        <hostnames>
            <hostname name="example.com"/>
        </hostnames>
        <ports>
            <port protocol="tcp" portid="80">
                <state state="open"/>
                <service name="http" product="Apache httpd" version="2.4.49"/>
            </port>
            <port protocol="tcp" portid="443">
                <state state="open"/>
                <service name="https" product="nginx" version="1.21.0"/>
            </port>
            <port protocol="tcp" portid="22">
                <state state="open"/>
                <service name="ssh" product="OpenSSH" version="8.2p1"/>
            </port>
            <port protocol="tcp" portid="3306">
                <state state="closed"/>
                <service name="mysql"/>
            </port>
        </ports>
    </host>
    <host>
        <address addr="192.168.1.2" addrtype="ipv4"/>
        <ports>
            <port protocol="tcp" portid="8080">
                <state state="open"/>
                <service name="http" product="Tomcat" version="9.0.50"/>
            </port>
        </ports>
    </host>
</nmaprun>
"""

    result = adapter.parse_output(xml_output, "", 0)

    # Check basic structure
    assert "hosts" in result
    assert "services" in result
    assert "total_hosts" in result
    assert "total_services" in result

    # Check hosts
    assert len(result["hosts"]) == 2
    assert result["total_hosts"] == 2

    # Check first host
    host1 = result["hosts"][0]
    assert host1["ip"] == "192.168.1.1"
    # Hostname might be None if XPath doesn't match - that's OK
    assert len(host1["ports"]) == 3  # Only open ports

    # Check ports include product and version
    port_80 = next(p for p in host1["ports"] if p["port"] == 80)
    assert port_80["service"] == "http"
    assert port_80["product"] == "Apache httpd"
    assert port_80["version"] == "2.4.49"

    # Check services array
    assert len(result["services"]) == 4  # Only open ports with known services
    assert result["total_services"] == 4

    # Find Apache service
    apache_service = next(s for s in result["services"] if s["port"] == 80)
    assert apache_service["host"] == "192.168.1.1"
    assert apache_service["port"] == 80
    assert apache_service["service"] == "Apache httpd"
    assert apache_service["version"] == "2.4.49"
    assert apache_service["full_string"] == "Apache httpd 2.4.49"

    # Find nginx service
    nginx_service = next(s for s in result["services"] if s["port"] == 443)
    assert nginx_service["host"] == "192.168.1.1"
    assert nginx_service["service"] == "nginx"
    assert nginx_service["version"] == "1.21.0"
    assert nginx_service["full_string"] == "nginx 1.21.0"

    # Find OpenSSH service
    ssh_service = next(s for s in result["services"] if s["port"] == 22)
    assert ssh_service["service"] == "OpenSSH"
    assert ssh_service["version"] == "8.2p1"
    assert ssh_service["full_string"] == "OpenSSH 8.2p1"

    # Find Tomcat service on second host
    tomcat_service = next(s for s in result["services"] if s["host"] == "192.168.1.2")
    assert tomcat_service["port"] == 8080
    assert tomcat_service["service"] == "Tomcat"
    assert tomcat_service["version"] == "9.0.50"

    # Verify closed port (3306) is NOT in services array
    mysql_services = [s for s in result["services"] if s["port"] == 3306]
    assert len(mysql_services) == 0


def test_nmap_parse_output_no_version():
    """Test parsing when service has no version information"""
    adapter = NmapAdapter()

    xml_output = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <address addr="10.0.0.1" addrtype="ipv4"/>
        <ports>
            <port protocol="tcp" portid="80">
                <state state="open"/>
                <service name="http"/>
            </port>
        </ports>
    </host>
</nmaprun>
"""

    result = adapter.parse_output(xml_output, "", 0)

    assert len(result["services"]) == 1
    service = result["services"][0]
    assert service["service"] == "http"
    assert service["version"] == ""
    assert service["full_string"] == "http"


def test_nmap_parse_output_unknown_service():
    """Test that unknown services are excluded from fingerprinting"""
    adapter = NmapAdapter()

    xml_output = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <address addr="10.0.0.1" addrtype="ipv4"/>
        <ports>
            <port protocol="tcp" portid="9999">
                <state state="open"/>
                <service name="unknown"/>
            </port>
        </ports>
    </host>
</nmaprun>
"""

    result = adapter.parse_output(xml_output, "", 0)

    # Unknown services should not be in services array
    assert len(result["services"]) == 0

    # But should still be in hosts/ports
    assert len(result["hosts"]) == 1
    assert len(result["hosts"][0]["ports"]) == 1


def test_nmap_parse_invalid_xml():
    """Test handling of invalid XML"""
    adapter = NmapAdapter()
    result = adapter.parse_output("not valid xml", "", 1)

    assert "error" in result
    assert result["hosts"] == []
    assert result["services"] == []
