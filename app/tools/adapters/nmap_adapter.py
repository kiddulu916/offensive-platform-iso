"""Nmap tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import json
from pathlib import Path

class NmapAdapter(BaseTool):

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="nmap",
            category=ToolCategory.SCANNING,
            description="Network exploration and security auditing",
            executable="nmap",
            requires_root=True,
            default_timeout=600
        )

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        return "target" in params or "domain" in params

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        cmd = [self.metadata.executable, "-oX", "-"]

        scan_type = params.get("scan_type", "default")
        if scan_type == "quick":
            cmd.extend(["-T4", "-F"])
        elif scan_type == "stealth":
            cmd.extend(["-sS", "-T2"])
        else:
            cmd.extend(["-sV", "-sC"])

        if params.get("ports"):
            cmd.extend(["-p", params["ports"]])

        # Check if we should use IPs from file
        if "domain" in params:
            domain = params["domain"]
            ips_file = Path("data/scans") / domain / "lists" / "ips.txt"

            if ips_file.exists():
                # Read IPs from file
                with open(ips_file, 'r') as f:
                    ips = [line.strip() for line in f if line.strip()]
                cmd.extend(ips)
            else:
                # Fallback to direct target if no ips.txt file
                target = params.get("target", domain)
                if isinstance(target, list):
                    cmd.extend(target)
                else:
                    cmd.append(target)
        else:
            # Use target parameter
            target = params["target"]
            if isinstance(target, list):
                cmd.extend(target)
            else:
                cmd.append(target)

        return cmd

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse nmap XML output and update combined results"""
        try:
            root = ET.fromstring(output)
        except:
            return {"error": "Failed to parse nmap XML output", "hosts": []}

        hosts = []
        ip_port_map = {}

        for host_elem in root.findall('.//host'):
            address_elem = host_elem.find('.//address[@addrtype="ipv4"]')
            if address_elem is None:
                continue

            host_ip = address_elem.get('addr')
            hostname_elem = host_elem.find('.//hostname')
            hostname = hostname_elem.get('name') if hostname_elem is not None else None

            ports = []
            ports_dict = {}

            for port_elem in host_elem.findall('.//port'):
                state_elem = port_elem.find('.//state')
                if state_elem is not None and state_elem.get('state') == 'open':
                    service_elem = port_elem.find('.//service')
                    port_num = int(port_elem.get('portid'))
                    service_name = service_elem.get('name') if service_elem is not None else 'unknown'
                    service_version = service_elem.get('version', '') if service_elem is not None else ''

                    port_info = {
                        "port": port_num,
                        "protocol": port_elem.get('protocol'),
                        "service": service_name,
                        "version": service_version
                    }
                    ports.append(port_info)

                    # Build ports dict for updating subdomains.json
                    service_desc = f"{service_name}"
                    if service_version:
                        service_desc += f" {service_version}"
                    ports_dict[str(port_num)] = service_desc

            if ports:
                hosts.append({
                    "ip": host_ip,
                    "hostname": hostname,
                    "ports": ports
                })

                # Store port mapping for this IP
                ip_port_map[host_ip] = ports_dict

        # Extract domain for file operations
        domain = self._extract_domain_from_params()

        if domain:
            # Save raw and parsed nmap output
            self._save_nmap_results(domain, output, hosts)

            # Update subdomains.json with port information
            self._update_subdomains_with_ports(domain, ip_port_map)

        return {
            "hosts": hosts,
            "total_hosts": len(hosts),
            "ip_port_map": ip_port_map
        }

    def _extract_domain_from_params(self) -> str:
        """Extract domain from current execution context"""
        # Domain is stored in instance variable during execute()
        return getattr(self, '_current_domain', None)

    def execute(self, params: Dict[str, Any], timeout: int = None) -> Dict[str, Any]:
        """Override execute to capture domain parameter"""
        # Store domain for later use in parse_output
        self._current_domain = params.get("domain")
        return super().execute(params, timeout)

    def _save_nmap_results(self, domain: str, raw_output: str, parsed_data: List[Dict]):
        """Save raw and parsed nmap results to files"""
        try:
            # Create directory structure
            base_dir = Path("data/scans") / domain
            raw_dir = base_dir / "raw" / "nmap"
            parsed_dir = base_dir / "parsed" / "nmap"

            raw_dir.mkdir(parents=True, exist_ok=True)
            parsed_dir.mkdir(parents=True, exist_ok=True)

            # Save raw XML output
            raw_file = raw_dir / "output.xml"
            with open(raw_file, 'w') as f:
                f.write(raw_output)

            # Save parsed output
            parsed_file = parsed_dir / "results.json"
            with open(parsed_file, 'w') as f:
                json.dump(parsed_data, f, indent=2)

        except Exception as e:
            # Silently fail if file saving fails - don't break the workflow
            pass

    def _update_subdomains_with_ports(self, domain: str, ip_port_map: Dict[str, Dict]):
        """Update subdomains.json with port information"""
        try:
            subdomains_file = Path("data/scans") / domain / "final" / "subdomains.json"

            if not subdomains_file.exists():
                return

            # Read existing subdomains data
            with open(subdomains_file, 'r') as f:
                subdomains_data = json.load(f)

            # Update each subdomain with port information based on its IPs
            for subdomain in subdomains_data:
                subdomain_ips = subdomain.get("ips", [])

                # Ensure ips is a list
                if not isinstance(subdomain_ips, list):
                    subdomain_ips = [subdomain_ips]

                # Collect all ports for this subdomain's IPs
                all_ports = {}
                for ip in subdomain_ips:
                    if ip in ip_port_map:
                        all_ports.update(ip_port_map[ip])

                # Add ports to subdomain
                if all_ports:
                    subdomain["ports"] = all_ports

            # Save updated subdomains data
            with open(subdomains_file, 'w') as f:
                json.dump(subdomains_data, f, indent=2)

        except Exception as e:
            # Silently fail if update fails - don't break the workflow
            pass