"""Subdomain enumeration workflow"""
from app.workflows.schemas import WorkflowDefinition, WorkflowTask

def create_subdomain_enum_workflow(domain: str) -> WorkflowDefinition:
    """
    Comprehensive subdomain enumeration using multiple tools
    """
    
    return WorkflowDefinition(
        workflow_id=f"subdomain_enum_{domain}",
        name="Subdomain Enumeration",
        description="Multi-tool subdomain discovery and validation",
        target=domain,
        tasks=[
            # Subfinder enumeration
            WorkflowTask(
                task_id="enum_subfinder",
                name="Subfinder Enumeration",
                description="Fast subdomain enumeration with subfinder",
                tool="subfinder",
                parameters={
                    "domain": domain,
                    "all": True,
                    "recursive": False
                },
                depends_on=[],
                priority=10
            ),
            
            # Amass enumeration (passive)
            WorkflowTask(
                task_id="enum_amass",
                name="Amass Enumeration",
                description="In-depth subdomain discovery with Amass",
                tool="amass",
                parameters={
                    "domain": domain,
                    "passive": True
                },
                depends_on=[],
                priority=10
            ),
            
            # HTTP probing to validate
            WorkflowTask(
                task_id="validate_subdomains",
                name="Validate Subdomains",
                description="Probe discovered subdomains to verify they're alive",
                tool="httpx",
                parameters={
                    "urls": "${enum_subfinder.unique_subdomains}",
                    "status_code": True,
                    "title": True,
                    "tech_detect": True
                },
                depends_on=["enum_subfinder", "enum_amass"],
                priority=9
            )
        ]
    )