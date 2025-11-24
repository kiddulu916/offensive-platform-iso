"""Sublist3r tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json
from pathlib import Path

class Sublist3rAdapter(BaseTool):

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="sublist3r",
            category=ToolCategory.RECONNAISSANCE,
            description="Fast subdomain enumeration using multiple search engines",
            executable="sublist3r",
            requires_root=False,
            default_timeout=600
        )

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "domain" in params

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        cmd = [
            self.metadata.executable,
            "-d", params["domain"],
            "-o", "/dev/stdout"  # Output to stdout
        ]

        # Enable brute force if requested
        if params.get("brute"):
            cmd.append("-b")

        # Specify ports for brute force
        if params.get("ports"):
            cmd.extend(["-p", params["ports"]])

        # Verbose mode
        if params.get("verbose"):
            cmd.append("-v")

        return cmd

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse Sublist3r text output into structured subdomain list"""
        subdomains_list = []

        for line in output.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('['):  # Filter out log lines
                subdomains_list.append({
                    "name": line,
                    "ips": [],  # Sublist3r doesn't provide IPs by default
                    "source": "sublist3r"
                })

        # Save results
        if subdomains_list:
            domain = subdomains_list[0]["name"].split(".")[-2:]
            domain = ".".join(domain) if len(domain) >= 2 else "unknown"
            self._save_results(domain, output, subdomains_list)

        return {
            "subdomains": subdomains_list,
            "count": len(subdomains_list)
        }

    def _save_results(self, domain: str, raw_output: str, parsed_data: List[Dict]):
        """Save raw and parsed results to files"""
        try:
            base_dir = Path("data/scans") / domain
            raw_dir = base_dir / "raw" / "sublist3r"
            parsed_dir = base_dir / "parsed" / "sublist3r"

            raw_dir.mkdir(parents=True, exist_ok=True)
            parsed_dir.mkdir(parents=True, exist_ok=True)

            # Save raw output
            raw_file = raw_dir / "output.txt"
            with open(raw_file, 'w') as f:
                f.write(raw_output)

            # Save parsed output
            parsed_file = parsed_dir / "results.json"
            with open(parsed_file, 'w') as f:
                json.dump(parsed_data, f, indent=2)

        except Exception:
            pass  # Silently fail if file saving fails
