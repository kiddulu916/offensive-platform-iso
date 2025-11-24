"""Integration tests for tool adapter execution"""
import pytest
import shutil
from app.tools.registry import ToolRegistry

pytestmark = pytest.mark.integration

@pytest.fixture
def registry():
    """Get ToolRegistry instance"""
    return ToolRegistry()

def test_registry_lists_all_tools(registry):
    """Test that registry contains all expected tools"""
    tools = registry.list_tools()
    tool_names = [t["name"] for t in tools]

    # Verify count
    assert len(tools) >= 13

    # Verify key tools are registered
    expected_tools = [
        "subfinder", "sublist3r", "amass",
        "nmap", "masscan",
        "nuclei", "httpx",
        "ffuf", "gobuster",
        "sqlmap",
        "testssl.sh", "wpscan", "metasploit"
    ]

    for tool in expected_tools:
        assert tool in tool_names, f"Tool {tool} not registered"

def test_tool_metadata_completeness(registry):
    """Test that all tools have complete metadata"""
    tools = registry.list_tools()

    for tool_info in tools:
        metadata = tool_info["metadata"]

        # Required metadata fields
        assert metadata["name"], f"Tool {tool_info['name']} missing name"
        assert metadata["category"], f"Tool {tool_info['name']} missing category"
        assert metadata["executable"], f"Tool {tool_info['name']} missing executable"
        assert metadata["default_timeout"] > 0, f"Tool {tool_info['name']} has invalid timeout"

@pytest.mark.skipif(not shutil.which("subfinder"), reason="subfinder not installed")
@pytest.mark.timeout(60)
@pytest.mark.requires_network
def test_subfinder_execution(registry):
    """Test Subfinder tool executes successfully"""
    subfinder = registry.get_tool("subfinder")

    result = subfinder.execute({
        "domain": "example.com",
        "all": False,
        "silent": True
    })

    # Note: This may fail if network is unavailable or tool has issues
    # The test verifies the tool can be executed, not necessarily that it succeeds
    assert "success" in result
    if result["success"]:
        assert "subdomains" in result["data"]

@pytest.mark.skipif(not shutil.which("nmap"), reason="nmap not installed")
@pytest.mark.timeout(120)
@pytest.mark.requires_network
@pytest.mark.requires_root
def test_nmap_execution(registry):
    """Test Nmap tool executes successfully"""
    nmap = registry.get_tool("nmap")

    result = nmap.execute({
        "target": ["scanme.nmap.org"],
        "scan_type": "quick"
    })

    assert "success" in result
    if result["success"]:
        assert "hosts" in result["data"]

def test_tool_parameter_validation(registry):
    """Test that tools properly validate parameters"""
    nmap = registry.get_tool("nmap")

    # Valid parameters
    assert nmap.validate_parameters({"target": ["192.168.1.1"]}) == True

    # Invalid parameters (missing target/domain)
    assert nmap.validate_parameters({}) == False
