import pytest
from app.tools.adapters.sublist3r_adapter import Sublist3rAdapter
from app.tools.base import ToolCategory

def test_sublist3r_metadata():
    adapter = Sublist3rAdapter()
    metadata = adapter.get_metadata()
    assert metadata.name == "sublist3r"
    assert metadata.category == ToolCategory.RECONNAISSANCE
    assert metadata.executable == "sublist3r"

def test_sublist3r_validate_parameters():
    adapter = Sublist3rAdapter()
    assert adapter.validate_parameters({"domain": "example.com"}) == True
    assert adapter.validate_parameters({}) == False

def test_sublist3r_build_command():
    adapter = Sublist3rAdapter()
    cmd = adapter.build_command({"domain": "example.com"})
    assert cmd == ["sublist3r", "-d", "example.com", "-o", "/dev/stdout"]

def test_sublist3r_parse_output():
    adapter = Sublist3rAdapter()
    output = "www.example.com\nmail.example.com\nftp.example.com\n"
    result = adapter.parse_output(output, "", 0)
    assert "subdomains" in result
    assert len(result["subdomains"]) == 3
    assert result["subdomains"][0]["name"] == "www.example.com"
