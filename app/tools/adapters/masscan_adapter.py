"""Masscan tool adapter - high-speed port scanner"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json
from pathlib import Path
import tempfile
import os

class MasscanAdapter(BaseTool):

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="masscan",
            category=ToolCategory.SCANNING,
            description="Ultra-fast TCP port scanner for large-scale networks",
            executable="masscan",
            requires_root=True,  # Masscan requires root for raw sockets
            default_timeout=1800  # 30 minutes for large scans
        )

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate that targets and ports are provided"""
        if "targets" not in params or not params["targets"]:
            return False
        if "ports" not in params and "port_range" not in params:
            # Default to common ports if not specified
            params["ports"] = "80,443,8080,8443,22,21,25,3306,3389"
        return True

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """Build masscan command with JSON output"""

        # Masscan requires targets as comma-separated or from file
        targets = params.get("targets", [])
        if isinstance(targets, list):
            target_str = ",".join(targets)
        else:
            target_str = targets

        # Build port specification
        ports = params.get("ports", "80,443")
        if isinstance(ports, list):
            ports = ",".join(map(str, ports))

        cmd = [
            self.metadata.executable,
            target_str,
            f"-p{ports}",
            "-oJ", "-",  # JSON output to stdout
            "--rate", str(params.get("rate", 10000))  # Default 10k packets/sec
        ]

        # Add optional parameters
        if params.get("banners"):
            cmd.append("--banners")

        if params.get("ping"):
            cmd.append("--ping")

        if params.get("exclude"):
            cmd.extend(["--exclude", params["exclude"]])

        return cmd

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse masscan JSON output into structured host/port data"""
        hosts_dict = {}

        for line in output.strip().split('\n'):
            if not line or line.startswith('#'):
                continue

            try:
                data = json.loads(line.rstrip(','))

                ip = data.get("ip")
                if not ip:
                    continue

                # Initialize host if not seen
                if ip not in hosts_dict:
                    hosts_dict[ip] = {
                        "ip": ip,
                        "ports": [],
                        "services": []
                    }

                # Extract port information
                if "ports" in data:
                    for port_info in data["ports"]:
                        port_entry = {
                            "port": port_info.get("port"),
                            "protocol": port_info.get("proto", "tcp"),
                            "state": port_info.get("status", "open"),
                            "service": None  # Masscan doesn't detect service names
                        }

                        # Add banner if available
                        if "service" in port_info:
                            port_entry["banner"] = port_info["service"].get("banner", "")

                        hosts_dict[ip]["ports"].append(port_entry)

            except json.JSONDecodeError:
                continue
            except Exception:
                continue

        hosts_list = list(hosts_dict.values())

        # Save results
        if hosts_list:
            self._save_results(hosts_list, output)

        return {
            "hosts": hosts_list,
            "total_hosts": len(hosts_list),
            "total_ports": sum(len(h["ports"]) for h in hosts_list)
        }

    def _save_results(self, parsed_data: List[Dict], raw_output: str):
        """Save masscan results to files"""
        try:
            base_dir = Path("data/scans/masscan")
            raw_dir = base_dir / "raw"
            parsed_dir = base_dir / "parsed"

            raw_dir.mkdir(parents=True, exist_ok=True)
            parsed_dir.mkdir(parents=True, exist_ok=True)

            # Save raw JSON output
            import time
            timestamp = int(time.time())
            raw_file = raw_dir / f"scan_{timestamp}.json"
            with open(raw_file, 'w') as f:
                f.write(raw_output)

            # Save parsed output
            parsed_file = parsed_dir / f"results_{timestamp}.json"
            with open(parsed_file, 'w') as f:
                json.dump(parsed_data, f, indent=2)

        except Exception:
            pass
