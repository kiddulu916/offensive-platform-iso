"""
Prebuilt workflow factory
"""
from app.workflows.schemas import WorkflowDefinition
from app.workflows.prebuilt.web_app_scan import create_web_app_workflow
from app.workflows.prebuilt.subdomain_enum import create_subdomain_enum_workflow
from app.workflows.prebuilt.port_scan import create_port_scan_workflow
from app.workflows.prebuilt.vuln_scan import create_vuln_scan_workflow


class WorkflowFactory:
    """Factory for creating prebuilt workflows"""
    
    @staticmethod
    def create_workflow(workflow_id: str, target: str) -> WorkflowDefinition:
        """Create a workflow by ID"""
        
        if workflow_id == "web_app_full":
            return create_web_app_workflow(target)
        
        elif workflow_id == "subdomain_enum":
            # Extract domain from URL if needed
            domain = target.replace("https://", "").replace("http://", "").split("/")[0]
            return create_subdomain_enum_workflow(domain)
        
        elif workflow_id == "port_scan":
            # Extract host from URL if needed
            host = target.replace("https://", "").replace("http://", "").split("/")[0]
            return create_port_scan_workflow(host)
        
        elif workflow_id == "vuln_scan":
            return create_vuln_scan_workflow(target)
        
        else:
            raise ValueError(f"Unknown workflow ID: {workflow_id}")
    
    @staticmethod
    def list_workflows():
        """List all available workflows"""
        return [
            {
                "id": "web_app_full",
                "name": "Full Web Application Scan",
                "description": "Complete assessment from reconnaissance to exploitation",
                "requires": "URL"
            },
            {
                "id": "subdomain_enum",
                "name": "Subdomain Enumeration",
                "description": "Discover and enumerate all subdomains",
                "requires": "Domain"
            },
            {
                "id": "port_scan",
                "name": "Port Scanning",
                "description": "Comprehensive port and service detection",
                "requires": "IP or Hostname"
            },
            {
                "id": "vuln_scan",
                "name": "Vulnerability Scanning",
                "description": "Automated vulnerability assessment",
                "requires": "URL"
            }
        ]