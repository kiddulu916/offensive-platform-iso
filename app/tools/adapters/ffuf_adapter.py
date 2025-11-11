"""FFUF tool adapter - Directory/file fuzzer"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json

class FfufAdapter(BaseTool):
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="ffuf",
            category=ToolCategory.SCANNING,
            description="Fast web fuzzer for directory and file discovery",
            executable="ffuf",
            requires_root=False,
            default_timeout=600
        )
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "url" in params
    
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        cmd = [
            self.metadata.executable,
            "-u", params["url"],
            "-json"
        ]
        
        # Wordlist
        wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        cmd.extend(["-w", wordlist])
        
        # Match codes
        match_codes = params.get("match_codes", [200, 204, 301, 302, 307, 401, 403])
        cmd.extend(["-mc", ",".join(map(str, match_codes))])
        
        # Threads
        threads = params.get("threads", 40)
        cmd.extend(["-t", str(threads)])
        
        # Extensions
        if params.get("extensions"):
            exts = ",".join(params["extensions"])
            cmd.extend(["-e", exts])
        
        return cmd
    
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        try:
            data = json.loads(output)
            results = data.get("results", [])
            
            findings = []
            for result in results:
                findings.append({
                    "url": result.get("url"),
                    "status": result.get("status"),
                    "length": result.get("length"),
                    "words": result.get("words"),
                    "lines": result.get("lines")
                })
            
            return {
                "findings": findings,
                "total": len(findings),
                "urls": [f["url"] for f in findings]
            }
        except:
            return {"findings": [], "total": 0, "urls": []}