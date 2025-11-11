"""Port scanning workflow"""
from app.workflows.schemas import WorkflowDefinition, WorkflowTask

def create_port_scan_workflow(target: str) -> WorkflowDefinition:
    """
    Comprehensive port scanning and service detection
    """
    
    return WorkflowDefinition(
        workflow_id=f"port_scan_{target}",
        name="Port Scanning & Service Detection",
        description="Network reconnaissance and service enumeration",
        target=target,
        tasks=[
            # Quick port scan
            WorkflowTask(
                task_id="scan_quick",
                name="Quick Port Scan",
                description="Fast scan of common ports",
                tool="nmap",
                parameters={
                    "target": target,
                    "scan_type": "quick",
                    "ports": "1-1000"
                },
                depends_on=[],
                priority=10
            ),
            
            # Full port scan
            WorkflowTask(
                task_id="scan_full",
                name="Full Port Scan",
                description="Comprehensive scan of all ports",
                tool="nmap",
                parameters={
                    "target": target,
                    "scan_type": "default",
                    "ports": "1-65535"
                },
                depends_on=["scan_quick"],
                priority=9
            ),
            
            # Service detection on open ports
            WorkflowTask(
                task_id="detect_services",
                name="Service Version Detection",
                description="Identify services and versions on open ports",
                tool="nmap",
                parameters={
                    "target": target,
                    "scan_type": "version"
                },
                depends_on=["scan_full"],
                priority=8
            )
        ]
    )