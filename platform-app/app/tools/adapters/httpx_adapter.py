"""HTTPx tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json

class HttpxAdapter(BaseTool):
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="httpx",
            category=ToolCategory.RECONNAISSANCE,
            description="Fast HTTP probe",
            executable="httpx",
            requires_root=False
        )
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "urls" in params or "url" in params
    
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        cmd = [self.metadata.executable, "-json", "-silent"]
        
        if "url" in params:
            cmd.extend(["-u", params["url"]])
        
        if params.get("status_code"):
            cmd.append("-status-code")
        
        if params.get("tech_detect"):
            cmd.append("-tech-detect")
        
        if params.get("title"):
            cmd.append("-title")
        
        threads = params.get("threads", 50)
        cmd.extend(["-threads", str(threads)])
        
        return cmd
    
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        results = []
        
        for line in output.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    results.append({
                        "url": data.get("url"),
                        "status_code": data.get("status_code"),
                        "title": data.get("title"),
                        "technologies": data.get("tech", [])
                    })
                except:
                    pass
        
        return {
            "results": results,
            "total": len(results),
            "live_urls": [r["url"] for r in results]
        }