"""Nmap tool adapter"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import xml.etree.ElementTree as ET

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
        return "target" in params
    
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
        
        target = params["target"]
        if isinstance(target, list):
            cmd.extend(target)
        else:
            cmd.append(target)
        
        return cmd
    
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        try:
            root = ET.fromstring(output)
        except:
            return {"error": "Failed to parse nmap XML output", "hosts": []}
        
        hosts = []
        
        for host_elem in root.findall('.//host'):
            address_elem = host_elem.find('.//address[@addrtype="ipv4"]')
            if address_elem is None:
                continue
            
            host_ip = address_elem.get('addr')
            hostname_elem = host_elem.find('.//hostname')
            hostname = hostname_elem.get('name') if hostname_elem is not None else None
            
            ports = []
            for port_elem in host_elem.findall('.//port'):
                state_elem = port_elem.find('.//state')
                if state_elem is not None and state_elem.get('state') == 'open':
                    service_elem = port_elem.find('.//service')
                    ports.append({
                        "port": int(port_elem.get('portid')),
                        "protocol": port_elem.get('protocol'),
                        "service": service_elem.get('name') if service_elem is not None else 'unknown',
                        "version": service_elem.get('version', '') if service_elem is not None else ''
                    })
            
            if ports:
                hosts.append({
                    "ip": host_ip,
                    "hostname": hostname,
                    "ports": ports
                })
        
        return {
            "hosts": hosts,
            "total_hosts": len(hosts)
        }