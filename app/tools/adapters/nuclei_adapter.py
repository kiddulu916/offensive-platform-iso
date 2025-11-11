"""Nuclei tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json

class NucleiAdapter(BaseTool):
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="nuclei",
            category=ToolCategory.SCANNING,
            description="Fast vulnerability scanner",
            executable="nuclei",
            requires_root=False,
            default_timeout=900
        )
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "url" in params or "urls" in params
    
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        cmd = [self.metadata.executable, "-json", "-silent"]
        
        if "url" in params:
            cmd.extend(["-u", params["url"]])
        elif "urls" in params:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write('\n'.join(params["urls"]))
                cmd.extend(["-list", f.name])
        
        templates = params.get("templates", ["cves", "vulnerabilities"])
        for template in templates:
            cmd.extend(["-t", template])
        
        severity = params.get("severity", ["critical", "high", "medium"])
        cmd.extend(["-severity", ",".join(severity)])
        
        return cmd
    
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        findings = []
        
        for line in output.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    findings.append({
                        "template": data.get("template-id"),
                        "name": data.get("info", {}).get("name"),
                        "severity": data.get("info", {}).get("severity"),
                        "host": data.get("host"),
                        "matched_at": data.get("matched-at")
                    })
                except:
                    pass
        
        severity_counts = {
            "critical": len([f for f in findings if f["severity"] == "critical"]),
            "high": len([f for f in findings if f["severity"] == "high"]),
            "medium": len([f for f in findings if f["severity"] == "medium"]),
            "low": len([f for f in findings if f["severity"] == "low"])
        }
        
        return {
            "findings": findings,
            "total_findings": len(findings),
            "severity_counts": severity_counts
        }