import pytest
import json
from app.tools.adapters.masscan_adapter import MasscanAdapter
from app.tools.base import ToolCategory

def test_masscan_metadata():
    adapter = MasscanAdapter()
    metadata = adapter.get_metadata()
    assert metadata.name == "masscan"
    assert metadata.category == ToolCategory.SCANNING
    assert metadata.executable == "masscan"
    assert metadata.requires_root == True

def test_masscan_validate_parameters():
    adapter = MasscanAdapter()
    assert adapter.validate_parameters({"targets": ["192.168.1.1"], "ports": "80,443"}) == True
    assert adapter.validate_parameters({"targets": []}) == False

def test_masscan_build_command():
    adapter = MasscanAdapter()
    cmd = adapter.build_command({
        "targets": ["192.168.1.1", "192.168.1.2"],
        "ports": "80,443,8080",
        "rate": 10000
    })
    assert "masscan" in cmd
    assert "192.168.1.1,192.168.1.2" in cmd
    assert "-p80,443,8080" in cmd
    assert "--rate" in cmd
    assert "10000" in cmd

def test_masscan_parse_json_output():
    adapter = MasscanAdapter()
    json_output = """
    { "ip": "192.168.1.1", "timestamp": "1234567890", "ports": [ {"port": 80, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 64} ] }
    { "ip": "192.168.1.1", "timestamp": "1234567891", "ports": [ {"port": 443, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 64} ] }
    """
    result = adapter.parse_output(json_output, "", 0)
    assert "hosts" in result
    assert len(result["hosts"]) == 1
    assert result["hosts"][0]["ip"] == "192.168.1.1"
    assert len(result["hosts"][0]["ports"]) == 2
