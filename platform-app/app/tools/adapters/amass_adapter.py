"""Amass tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json
from pathlib import Path

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
        """Parse Amass JSON output with ASNs, IPs, and subdomains"""
        subdomains_data = {}

        for line in output.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    subdomain_name = data.get("name")

                    if not subdomain_name:
                        continue

                    # Extract IPs
                    ips = []
                    if "addresses" in data:
                        for addr in data["addresses"]:
                            if "ip" in addr:
                                ips.append(addr["ip"])

                    # Extract ASNs
                    asns = []
                    if "addresses" in data:
                        for addr in data["addresses"]:
                            if "asn" in addr and addr["asn"]:
                                asn_str = f"AS{addr['asn']}" if not str(addr['asn']).startswith("AS") else str(addr['asn'])
                                if asn_str not in asns:
                                    asns.append(asn_str)

                    # If subdomain already exists, merge data
                    if subdomain_name in subdomains_data:
                        existing_ips = set(subdomains_data[subdomain_name].get("ips", []))
                        existing_asns = set(subdomains_data[subdomain_name].get("asns", []))

                        subdomains_data[subdomain_name]["ips"] = list(existing_ips | set(ips))
                        subdomains_data[subdomain_name]["asns"] = list(existing_asns | set(asns))
                    else:
                        subdomains_data[subdomain_name] = {
                            "name": subdomain_name,
                            "ips": ips,
                            "asns": asns,
                            "source": data.get("source", "amass")
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
            raw_dir = base_dir / "raw" / "amass"
            parsed_dir = base_dir / "parsed" / "amass"

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