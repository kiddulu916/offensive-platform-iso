"""Amass tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json

class AmassAdapter(BaseTool):
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="amass",
            category=ToolCategory.RECONNAISSANCE,
            description="In-depth DNS enumeration and network mapping",
            executable="amass",
            requires_root=False,
            default_timeout=900
        )
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "domain" in params
    
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        cmd = [
            self.metadata.executable,
            "enum",
            "-d", params["domain"],
            "-json", "/dev/stdout"
        ]
        
        # Passive mode
        if params.get("passive"):
            cmd.append("-passive")
        
        # Active mode
        if params.get("active"):
            cmd.append("-active")
        
        # Brute force
        if params.get("brute"):
            cmd.append("-brute")
        
        return cmd
    
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        subdomains = []
        
        for line in output.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    if data.get("name"):
                        subdomains.append({
                            "subdomain": data.get("name"),
                            "source": data.get("source"),
                            "tag": data.get("tag")
                        })
                except:
                    pass
        
        unique_subdomains = list(set(s["subdomain"] for s in subdomains))
        
        return {
            "subdomains": subdomains,
            "unique_subdomains": unique_subdomains,
            "count": len(unique_subdomains)
        }