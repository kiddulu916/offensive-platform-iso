"""Subfinder tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json

class SubfinderAdapter(BaseTool):
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="subfinder",
            category=ToolCategory.RECONNAISSANCE,
            description="Fast subdomain enumeration tool",
            executable="subfinder",
            requires_root=False
        )
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "domain" in params
    
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        cmd = [
            self.metadata.executable,
            "-d", params["domain"],
            "-json",
            "-silent"
        ]
        
        if params.get("all"):
            cmd.append("-all")
        
        if params.get("recursive"):
            cmd.append("-recursive")
        
        return cmd
    
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        subdomains = []
        
        for line in output.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    subdomains.append({
                        "subdomain": data.get("host"),
                        "source": data.get("source")
                    })
                except:
                    pass
        
        unique_subdomains = list(set(s["subdomain"] for s in subdomains if s["subdomain"]))
        
        return {
            "subdomains": subdomains,
            "unique_subdomains": unique_subdomains,
            "count": len(unique_subdomains)
        }