"""Gobuster tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List

class GobusterAdapter(BaseTool):
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="gobuster",
            category=ToolCategory.SCANNING,
            description="Directory/file and DNS busting tool",
            executable="gobuster",
            requires_root=False,
            default_timeout=600
        )
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "url" in params or "domain" in params
    
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        mode = params.get("mode", "dir")  # dir, dns, vhost
        
        cmd = [self.metadata.executable, mode]
        
        if mode == "dir":
            cmd.extend(["-u", params["url"]])
            wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
            cmd.extend(["-w", wordlist])
            
            # Extensions
            if params.get("extensions"):
                exts = ",".join(params["extensions"])
                cmd.extend(["-x", exts])
            
            # Threads
            threads = params.get("threads", 10)
            cmd.extend(["-t", str(threads)])
            
            # Status codes
            if params.get("status_codes"):
                codes = ",".join(map(str, params["status_codes"]))
                cmd.extend(["-s", codes])
            
        elif mode == "dns":
            cmd.extend(["-d", params["domain"]])
            wordlist = params.get("wordlist", "/usr/share/wordlists/subdomains.txt")
            cmd.extend(["-w", wordlist])
        
        return cmd
    
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        findings = []
        
        for line in output.split('\n'):
            if line.startswith('/') or 'Found:' in line:
                # Parse directory/file findings
                parts = line.split()
                if len(parts) >= 3:
                    findings.append({
                        "path": parts[0],
                        "status": parts[1].strip('()'),
                        "size": parts[2] if len(parts) > 2 else ""
                    })
        
        return {
            "findings": findings,
            "total": len(findings),
            "paths": [f["path"] for f in findings]
        }