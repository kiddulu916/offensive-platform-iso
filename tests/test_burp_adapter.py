"""Tests for Burp Suite adapter"""
import pytest
from app.tools.adapters.burp_adapter import BurpAdapter
from app.tools.base import ToolCategory


def test_burp_metadata():
    """Test Burp Suite adapter metadata"""
    adapter = BurpAdapter()
    metadata = adapter.get_metadata()

    assert metadata.name == "burp"
    assert metadata.category == ToolCategory.SCANNING
    assert metadata.executable == "burp"
    assert metadata.requires_root == False
    assert metadata.default_timeout == 1800


def test_burp_validate_parameters():
    """Test Burp parameter validation"""
    adapter = BurpAdapter()

    # Valid: url or urls present
    assert adapter.validate_parameters({"url": "https://example.com"}) == True
    assert adapter.validate_parameters({"urls": ["https://example.com"]}) == True

    # Invalid: no url
    assert adapter.validate_parameters({}) == False
    assert adapter.validate_parameters({"scan_type": "crawl"}) == False


def test_burp_build_command_basic(tmp_path):
    """Test Burp command building"""
    adapter = BurpAdapter()
    adapter._temp_dir = tmp_path

    params = {
        "url": "https://example.com"
    }

    cmd = adapter.build_command(params)

    assert "burp" in cmd
    assert "--project-file" in cmd or "--unpacked-project" in cmd
    assert "--scan" in cmd or any("--scan" in str(c) for c in cmd)


def test_burp_build_command_with_config(tmp_path):
    """Test Burp with scan configuration"""
    adapter = BurpAdapter()
    adapter._temp_dir = tmp_path

    params = {
        "urls": ["https://example.com", "https://test.com"],
        "scan_type": "audit",
        "report_format": "xml"
    }

    cmd = adapter.build_command(params)

    # Should specify output format
    assert any("xml" in str(c).lower() or "report" in str(c).lower() for c in cmd)


def test_burp_parse_output():
    """Test Burp XML report parsing"""
    adapter = BurpAdapter()

    # Sample Burp XML report (simplified)
    sample_output = '''<?xml version="1.0"?>
<issues burpVersion="2023.1">
    <issue>
        <serialNumber>1</serialNumber>
        <type>2097920</type>
        <name>Cross-site scripting (reflected)</name>
        <host>https://example.com</host>
        <path>/search?q=test</path>
        <severity>High</severity>
        <confidence>Certain</confidence>
    </issue>
    <issue>
        <serialNumber>2</serialNumber>
        <type>5244416</type>
        <name>SQL injection</name>
        <host>https://example.com</host>
        <path>/product?id=1</path>
        <severity>High</severity>
        <confidence>Firm</confidence>
    </issue>
</issues>
'''

    result = adapter.parse_output(sample_output, "", 0)

    assert "issues" in result
    assert len(result["issues"]) == 2
    assert result["total_issues"] == 2

    # Check severity counts
    assert "severity_counts" in result
    assert result["severity_counts"]["High"] == 2

    # Check first issue
    assert result["issues"][0]["name"] == "Cross-site scripting (reflected)"
    assert result["issues"][0]["severity"] == "High"


def test_burp_parse_output_empty():
    """Test Burp parsing with no issues"""
    adapter = BurpAdapter()

    sample_output = '''<?xml version="1.0"?>
<issues burpVersion="2023.1">
</issues>
'''

    result = adapter.parse_output(sample_output, "", 0)

    assert result["issues"] == []
    assert result["total_issues"] == 0
