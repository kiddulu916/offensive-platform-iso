"""Tests for tool registry with new adapters"""
import pytest
from app.tools.registry import ToolRegistry


def test_registry_contains_new_tools():
    """Test that registry includes all new adapters"""
    registry = ToolRegistry()
    tools = registry.list_tools()
    tool_names = [t["name"] for t in tools]

    # Check new tools are registered
    assert "testssl" in tool_names
    assert "wpscan" in tool_names
    assert "metasploit" in tool_names


def test_registry_get_new_tools():
    """Test getting new tool instances"""
    registry = ToolRegistry()

    # Should not raise exceptions
    testssl = registry.get_tool("testssl")
    assert testssl is not None
    assert testssl.get_metadata().name == "testssl"

    wpscan = registry.get_tool("wpscan")
    assert wpscan is not None

    metasploit = registry.get_tool("metasploit")
    assert metasploit is not None
