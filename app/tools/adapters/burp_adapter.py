"""Burp Suite Professional adapter for web application security scanning"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json
import xml.etree.ElementTree as ET
import tempfile
from pathlib import Path


class BurpAdapter(BaseTool):

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="burp",
            category=ToolCategory.SCANNING,
            description="Burp Suite Professional web application scanner",
            executable="burp",
            requires_root=False,
            default_timeout=1800  # 30 minutes for thorough scans
        )

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate that url or urls is provided"""
        return "url" in params or "urls" in params

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """Build Burp Suite scanner command"""
        # Create temporary files for scan
        temp_dir = Path(tempfile.mkdtemp())
        project_file = temp_dir / "burp_project.burp"
        report_file = temp_dir / "burp_report.xml"

        # Store for cleanup
        self._temp_project = str(project_file)
        self._temp_report = str(report_file)

        # Base command
        cmd = [
            self.metadata.executable,
            "--project-file", str(project_file),
            "--unpacked-project"
        ]

        # Target URL(s)
        if "url" in params:
            urls = [params["url"]]
        else:
            urls = params["urls"]

        # Scan configuration
        scan_type = params.get("scan_type", "crawl_and_audit")

        for url in urls:
            cmd.extend(["--scan", url])

        # Report output
        report_format = params.get("report_format", "xml")
        cmd.extend([
            "--report-output", str(report_file),
            "--report-type", report_format
        ])

        return cmd

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse Burp Suite XML report"""
        issues = []
        severity_counts = {
            "High": 0,
            "Medium": 0,
            "Low": 0,
            "Information": 0
        }

        if not output.strip():
            return {
                "issues": issues,
                "total_issues": 0,
                "severity_counts": severity_counts
            }

        try:
            root = ET.fromstring(output)

            for issue_elem in root.findall('.//issue'):
                issue = {
                    "serial_number": issue_elem.findtext('serialNumber', ''),
                    "type": issue_elem.findtext('type', ''),
                    "name": issue_elem.findtext('name', ''),
                    "host": issue_elem.findtext('host', ''),
                    "path": issue_elem.findtext('path', ''),
                    "severity": issue_elem.findtext('severity', 'Information'),
                    "confidence": issue_elem.findtext('confidence', '')
                }

                issues.append(issue)

                # Count by severity
                severity = issue["severity"]
                if severity in severity_counts:
                    severity_counts[severity] += 1

        except ET.ParseError:
            # Return empty results if XML parsing fails
            pass

        return {
            "issues": issues,
            "total_issues": len(issues),
            "severity_counts": severity_counts
        }
