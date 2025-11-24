"""Tests for WPScan adapter"""
import pytest
from app.tools.adapters.wpscan_adapter import WpscanAdapter
from app.tools.base import ToolCategory


def test_wpscan_metadata():
    """Test WPScan adapter metadata"""
    adapter = WpscanAdapter()
    metadata = adapter.get_metadata()

    assert metadata.name == "wpscan"
    assert metadata.category == ToolCategory.SCANNING
    assert metadata.executable == "wpscan"
    assert metadata.requires_root == False
    assert metadata.default_timeout == 600


def test_wpscan_validate_parameters():
    """Test WPScan parameter validation"""
    adapter = WpscanAdapter()

    # Valid: url parameter present
    assert adapter.validate_parameters({"url": "https://wordpress.example.com"}) == True

    # Invalid: no url
    assert adapter.validate_parameters({}) == False
    assert adapter.validate_parameters({"api_token": "xxx"}) == False


def test_wpscan_build_command_basic():
    """Test WPScan command building"""
    adapter = WpscanAdapter()

    cmd = adapter.build_command({"url": "https://wordpress.example.com"})

    assert "wpscan" in cmd
    assert "--url" in cmd
    assert "https://wordpress.example.com" in cmd
    assert "--format" in cmd
    assert "json" in cmd


def test_wpscan_build_command_with_options():
    """Test WPScan with enumeration options"""
    adapter = WpscanAdapter()

    # Test with plugin enumeration
    cmd = adapter.build_command({
        "url": "https://example.com",
        "enumerate": ["vp", "vt", "u"]
    })

    assert "--enumerate" in cmd
    assert "vp,vt,u" in cmd

    # Test with API token
    cmd = adapter.build_command({
        "url": "https://example.com",
        "api_token": "abc123"
    })

    assert "--api-token" in cmd
    assert "abc123" in cmd

    # Test with aggressive detection
    cmd = adapter.build_command({
        "url": "https://example.com",
        "detection_mode": "aggressive"
    })

    assert "--detection-mode" in cmd
    assert "aggressive" in cmd


def test_wpscan_parse_output():
    """Test WPScan JSON output parsing"""
    adapter = WpscanAdapter()

    # Sample WPScan JSON output
    sample_output = '''{
        "version": {
            "number": "5.8.1",
            "confidence": 80,
            "interesting_entries": ["WordPress version 5.8.1 identified"]
        },
        "interesting_findings": [
            {
                "url": "https://example.com/readme.html",
                "type": "readme",
                "to_s": "readme.html found"
            }
        ],
        "plugins": {
            "contact-form-7": {
                "slug": "contact-form-7",
                "version": {
                    "number": "5.4.2"
                },
                "vulnerabilities": [
                    {
                        "title": "Contact Form 7 <= 5.4.2 - Reflected XSS",
                        "references": {
                            "url": ["https://wpscan.com/vulnerability/xxx"]
                        }
                    }
                ]
            }
        },
        "themes": {
            "twentytwentyone": {
                "slug": "twentytwentyone",
                "version": {
                    "number": "1.4"
                }
            }
        }
    }'''

    result = adapter.parse_output(sample_output, "", 0)

    assert "wordpress_version" in result
    assert result["wordpress_version"] == "5.8.1"

    assert "plugins" in result
    assert len(result["plugins"]) == 1
    assert result["plugins"][0]["slug"] == "contact-form-7"

    assert "themes" in result
    assert len(result["themes"]) == 1

    assert "vulnerabilities" in result
    assert len(result["vulnerabilities"]) == 1
    assert result["total_vulnerabilities"] == 1


def test_wpscan_parse_output_no_vulns():
    """Test WPScan parsing with no vulnerabilities"""
    adapter = WpscanAdapter()

    sample_output = '''{
        "version": {"number": "6.0"},
        "plugins": {},
        "themes": {}
    }'''

    result = adapter.parse_output(sample_output, "", 0)

    assert result["vulnerabilities"] == []
    assert result["total_vulnerabilities"] == 0
