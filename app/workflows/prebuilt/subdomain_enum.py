"""Subdomain enumeration workflow"""
from app.workflows.schemas import WorkflowDefinition, WorkflowTask, TaskType

def create_subdomain_enum_workflow(domain: str) -> WorkflowDefinition:
    """
    Comprehensive subdomain enumeration using multiple tools with merge/deduplication
    """

    return WorkflowDefinition(
        workflow_id=f"subdomain_enum_{domain}",
        name="Subdomain Enumeration",
        description="Multi-tool subdomain discovery with deduplication and validation",
        target=domain,
        tasks=[
            # Amass enumeration (passive) - Run first for comprehensive data
            WorkflowTask(
                task_id="enum_amass",
                name="Amass Enumeration",
                description="In-depth subdomain discovery with Amass (ASNs, IPs, subdomains)",
                tool="amass",
                parameters={
                    "domain": domain,
                    "passive": True
                },
                depends_on=[],
                priority=10
            ),

            # Subfinder enumeration - Run second for additional coverage
            WorkflowTask(
                task_id="enum_subfinder",
                name="Subfinder Enumeration",
                description="Fast subdomain enumeration with subfinder",
                tool="subfinder",
                parameters={
                    "domain": domain,
                    "all": True,
                    "recursive": False,
                    "resolve": True  # Resolve IPs
                },
                depends_on=[],
                priority=9
            ),

            # Merge and deduplicate results
            WorkflowTask(
                task_id="merge_subdomains",
                name="Merge and Deduplicate Subdomains",
                description="Combine results from Amass and Subfinder, merge IPs, remove duplicates",
                task_type=TaskType.MERGE,
                tool=None,  # Not used for merge tasks
                parameters={},
                merge_sources=["enum_amass", "enum_subfinder"],
                merge_field="subdomains",
                dedupe_key="name",
                merge_strategy="combine",  # Merge IPs for same subdomain
                depends_on=["enum_amass", "enum_subfinder"],
                priority=8
            ),

            # HTTP probing to validate merged results
            WorkflowTask(
                task_id="validate_subdomains",
                name="Validate Subdomains",
                description="Probe discovered subdomains to verify they're alive",
                tool="httpx",
                parameters={
                    "urls": "${merge_subdomains.merged_data}",
                    "status_code": True,
                    "title": True,
                    "tech_detect": True
                },
                depends_on=["merge_subdomains"],
                priority=7
            )
        ]
    )