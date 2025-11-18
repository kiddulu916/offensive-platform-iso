"""Tests for TestSSL adapter"""
import pytest
from app.tools.adapters.testssl_adapter import TestsslAdapter
from app.tools.base import ToolCategory


def test_testssl_metadata():
    """Test TestSSL adapter metadata"""
    adapter = TestsslAdapter()
    metadata = adapter.get_metadata()

    assert metadata.name == "testssl"
    assert metadata.category == ToolCategory.SCANNING
    assert metadata.executable == "testssl.sh"
    assert metadata.requires_root == False
    assert metadata.default_timeout == 300


def test_testssl_validate_parameters():
    """Test TestSSL parameter validation"""
    adapter = TestsslAdapter()

    # Valid: host parameter present
    assert adapter.validate_parameters({"host": "example.com"}) == True

    # Valid: url parameter present
    assert adapter.validate_parameters({"url": "https://example.com"}) == True

    # Invalid: no host or url
    assert adapter.validate_parameters({}) == False
    assert adapter.validate_parameters({"port": "443"}) == False


def test_testssl_build_command_basic():
    """Test TestSSL command building with basic parameters"""
    adapter = TestsslAdapter()

    # Test with host
    cmd = adapter.build_command({"host": "example.com"})
    assert cmd == ["testssl.sh", "--jsonfile-pretty", "-", "example.com"]

    # Test with URL
    cmd = adapter.build_command({"url": "https://example.com:8443"})
    assert cmd == ["testssl.sh", "--jsonfile-pretty", "-", "https://example.com:8443"]


def test_testssl_build_command_with_options():
    """Test TestSSL command building with additional options"""
    adapter = TestsslAdapter()

    # Test with severity filter
    cmd = adapter.build_command({
        "host": "example.com",
        "severity": ["HIGH", "CRITICAL"]
    })
    assert "testssl.sh" in cmd
    assert "--severity" in cmd
    assert "HIGH,CRITICAL" in cmd

    # Test with specific checks
    cmd = adapter.build_command({
        "host": "example.com",
        "protocols": True,
        "ciphers": True,
        "vulnerabilities": True
    })
    assert "--protocols" in cmd or "-p" in cmd
    assert "--ciphers" in cmd or "-e" in cmd
    assert "--vulnerable" in cmd or "-U" in cmd


def test_testssl_parse_output():
    """Test TestSSL output parsing"""
    adapter = TestsslAdapter()

    # Sample testssl JSON output (simplified)
    sample_output = '''[
        {
            "id": "TLS1_2",
            "finding": "TLS 1.2 offered (OK)",
            "severity": "OK"
        },
        {
            "id": "BEAST",
            "finding": "BEAST vulnerability",
            "severity": "MEDIUM"
        },
        {
            "id": "POODLE_SSL",
            "finding": "POODLE (SSL)",
            "severity": "HIGH"
        }
    ]'''

    result = adapter.parse_output(sample_output, "", 0)

    assert "findings" in result
    assert len(result["findings"]) == 3
    assert result["total_findings"] == 3

    # Check severity counts
    assert "severity_counts" in result
    assert result["severity_counts"]["HIGH"] == 1
    assert result["severity_counts"]["MEDIUM"] == 1
    assert result["severity_counts"]["OK"] == 1

    # Check vulnerabilities list
    assert "vulnerabilities" in result
    assert len(result["vulnerabilities"]) == 2  # BEAST and POODLE


def test_testssl_parse_output_empty():
    """Test TestSSL parsing with empty output"""
    adapter = TestsslAdapter()

    result = adapter.parse_output("", "", 0)

    assert result["findings"] == []
    assert result["total_findings"] == 0
