"""Subfinder tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json
from pathlib import Path

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

        # Enable IP resolution if requested
        if params.get("resolve", True):  # Default to True
            cmd.append("-ip")

        if params.get("all"):
            cmd.append("-all")

        if params.get("recursive"):
            cmd.append("-recursive")

        return cmd

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse Subfinder JSON output with IPs"""
        subdomains_data = {}

        for line in output.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    subdomain_name = data.get("host")

                    if not subdomain_name:
                        continue

                    # Extract IP if available
                    ips = []
                    if "ip" in data and data["ip"]:
                        # Subfinder can return a single IP or array
                        if isinstance(data["ip"], list):
                            ips = data["ip"]
                        else:
                            ips = [data["ip"]]

                    # If subdomain already exists, merge IPs
                    if subdomain_name in subdomains_data:
                        existing_ips = set(subdomains_data[subdomain_name].get("ips", []))
                        subdomains_data[subdomain_name]["ips"] = list(existing_ips | set(ips))
                    else:
                        subdomains_data[subdomain_name] = {
                            "name": subdomain_name,
                            "ips": ips,
                            "source": data.get("source", "subfinder")
                        }

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    # Log error but continue processing
                    continue

        # Convert to list
        subdomains_list = list(subdomains_data.values())

        # Save raw and parsed output to files
        domain = None
        for subdomain in subdomains_list:
            # Extract root domain from first subdomain
            parts = subdomain["name"].split(".")
            if len(parts) >= 2:
                domain = ".".join(parts[-2:])
                break

        if domain:
            self._save_results(domain, output, subdomains_list)

        return {
            "subdomains": subdomains_list,
            "count": len(subdomains_list)
        }

    def _save_results(self, domain: str, raw_output: str, parsed_data: List[Dict]):
        """Save raw and parsed results to files"""
        try:
            # Create directory structure
            base_dir = Path("data/scans") / domain
            raw_dir = base_dir / "raw" / "subfinder"
            parsed_dir = base_dir / "parsed" / "subfinder"

            raw_dir.mkdir(parents=True, exist_ok=True)
            parsed_dir.mkdir(parents=True, exist_ok=True)

            # Save raw output
            raw_file = raw_dir / "output.json"
            with open(raw_file, 'w') as f:
                f.write(raw_output)

            # Save parsed output
            parsed_file = parsed_dir / "results.json"
            with open(parsed_file, 'w') as f:
                json.dump(parsed_data, f, indent=2)

        except Exception as e:
            # Silently fail if file saving fails - don't break the workflow
            pass