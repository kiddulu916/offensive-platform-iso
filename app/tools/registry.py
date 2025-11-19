"""Tool registry - Updated with all adapters"""
from typing import Dict, Type
from app.tools.base import BaseTool

# Import all adapters
from app.tools.adapters.subfinder_adapter import SubfinderAdapter
from app.tools.adapters.sublist3r_adapter import Sublist3rAdapter
from app.tools.adapters.nmap_adapter import NmapAdapter
from app.tools.adapters.httpx_adapter import HttpxAdapter
from app.tools.adapters.nuclei_adapter import NucleiAdapter
from app.tools.adapters.ffuf_adapter import FfufAdapter
from app.tools.adapters.sqlmap_adapter import SqlmapAdapter
from app.tools.adapters.gobuster_adapter import GobusterAdapter
from app.tools.adapters.amass_adapter import AmassAdapter
from app.tools.adapters.testssl_adapter import TestsslAdapter
from app.tools.adapters.wpscan_adapter import WpscanAdapter
from app.tools.adapters.metasploit_adapter import MetasploitAdapter
from app.tools.adapters.burp_adapter import BurpAdapter

class ToolRegistry:
    """Central registry for all security tools"""
    
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        # Reconnaissance
        self.register("subfinder", SubfinderAdapter)
        self.register("sublist3r", Sublist3rAdapter)
        self.register("amass", AmassAdapter)
        self.register("httpx", HttpxAdapter)

        # Scanning
        self.register("nmap", NmapAdapter)
        self.register("nuclei", NucleiAdapter)
        self.register("ffuf", FfufAdapter)
        self.register("gobuster", GobusterAdapter)
        self.register("testssl", TestsslAdapter)
        self.register("wpscan", WpscanAdapter)
        self.register("burp", BurpAdapter)

        # Exploitation
        self.register("sqlmap", SqlmapAdapter)
        self.register("metasploit", MetasploitAdapter)
    
    def register(self, name: str, tool_class: Type[BaseTool]):
        """Register a new tool"""
        self._tools[name] = tool_class
    
    def get_tool(self, name: str) -> BaseTool:
        """Get a tool instance by name"""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        return self._tools[name]()
    
    def list_tools(self) -> list:
        """List all registered tools"""
        return [
            {
                "name": name,
                "metadata": tool_class().get_metadata().__dict__
            }
            for name, tool_class in self._tools.items()
        ]