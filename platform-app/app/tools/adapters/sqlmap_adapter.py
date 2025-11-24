"""SQLMap tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import re

class SqlmapAdapter(BaseTool):
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="sqlmap",
            category=ToolCategory.EXPLOITATION,
            description="Automatic SQL injection and database takeover tool",
            executable="sqlmap",
            requires_root=False,
            default_timeout=1200
        )
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "url" in params
    
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        cmd = [
            self.metadata.executable,
            "-u", params["url"],
            "--batch",
            "--random-agent"
        ]
        
        # Risk and level
        level = params.get("level", 1)
        risk = params.get("risk", 1)
        cmd.extend(["--level", str(level), "--risk", str(risk)])
        
        # Threads
        threads = params.get("threads", 1)
        cmd.extend(["--threads", str(threads)])
        
        # Test type
        if params.get("test_all"):
            cmd.append("--test-filter")
        
        # Database enumeration
        if params.get("enum_dbs"):
            cmd.append("--dbs")
        
        return cmd
    
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        vulnerabilities = []
        
        # Look for vulnerable parameters
        param_pattern = r"Parameter: (.*?) \(.*?\) is vulnerable"
        for match in re.finditer(param_pattern, output):
            vulnerabilities.append({
                "parameter": match.group(1),
                "type": "SQL Injection"
            })
        
        # Look for injection types
        injection_types = []
        if "boolean-based blind" in output:
            injection_types.append("Boolean-based blind")
        if "time-based blind" in output:
            injection_types.append("Time-based blind")
        if "error-based" in output:
            injection_types.append("Error-based")
        if "UNION query" in output:
            injection_types.append("UNION query")
        
        # Look for databases
        databases = []
        if "[*]" in output:
            db_section = False
            for line in output.split('\n'):
                if "available databases" in line.lower():
                    db_section = True
                elif db_section and line.strip().startswith("[*]"):
                    db_name = line.strip().replace("[*]", "").strip()
                    if db_name:
                        databases.append(db_name)
                elif db_section and not line.strip().startswith("["):
                    db_section = False
        
        is_vulnerable = len(vulnerabilities) > 0
        
        return {
            "vulnerable": is_vulnerable,
            "vulnerabilities": vulnerabilities,
            "injection_types": injection_types,
            "databases": databases,
            "severity": "critical" if is_vulnerable else "none"
        }