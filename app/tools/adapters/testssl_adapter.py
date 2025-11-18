"""TestSSL tool adapter for SSL/TLS security testing"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json
import re


class TestsslAdapter(BaseTool):

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="testssl",
            category=ToolCategory.SCANNING,
            description="SSL/TLS security testing tool",
            executable="testssl.sh",
            requires_root=False,
            default_timeout=300
        )

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate that host or url is provided"""
        return "host" in params or "url" in params

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """Build testssl.sh command with parameters"""
        cmd = [self.metadata.executable]

        # JSON output to stdout
        cmd.extend(["--jsonfile-pretty", "-"])

        # Specific check options
        if params.get("protocols"):
            cmd.append("--protocols")

        if params.get("ciphers"):
            cmd.append("--ciphers")

        if params.get("vulnerabilities"):
            cmd.append("--vulnerable")

        # Severity filter
        if "severity" in params:
            severities = params["severity"]
            if isinstance(severities, list):
                cmd.extend(["--severity", ",".join(severities)])

        # Append target (host or url)
        target = params.get("host") or params.get("url")
        cmd.append(target)

        return cmd

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse testssl.sh JSON output"""
        findings = []
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "OK": 0,
            "INFO": 0
        }
        vulnerabilities = []

        if not output.strip():
            return {
                "findings": findings,
                "total_findings": 0,
                "severity_counts": severity_counts,
                "vulnerabilities": vulnerabilities
            }

        try:
            data = json.loads(output)

            for item in data:
                finding = {
                    "id": item.get("id", ""),
                    "finding": item.get("finding", ""),
                    "severity": item.get("severity", "INFO")
                }
                findings.append(finding)

                # Count by severity
                severity = finding["severity"]
                if severity in severity_counts:
                    severity_counts[severity] += 1

                # Track vulnerabilities (non-OK findings)
                if severity not in ["OK", "INFO"]:
                    vulnerabilities.append(finding)

        except json.JSONDecodeError:
            # Fallback: return empty results if JSON parsing fails
            pass

        return {
            "findings": findings,
            "total_findings": len(findings),
            "severity_counts": severity_counts,
            "vulnerabilities": vulnerabilities
        }
