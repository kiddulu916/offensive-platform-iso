"""Vulnerability scanning workflow"""
from app.workflows.schemas import WorkflowDefinition, WorkflowTask

def create_vuln_scan_workflow(target_url: str) -> WorkflowDefinition:
    """
    Focused vulnerability assessment workflow
    """
    
    return WorkflowDefinition(
        workflow_id=f"vuln_scan_{target_url}",
        name="Vulnerability Assessment",
        description="Automated vulnerability scanning and detection",
        target=target_url,
        tasks=[
            # HTTP probing first
            WorkflowTask(
                task_id="probe_target",
                name="Target Probing",
                description="Verify target is accessible",
                tool="httpx",
                parameters={
                    "url": target_url,
                    "status_code": True,
                    "tech_detect": True
                },
                depends_on=[],
                priority=10
            ),
            
            # Nuclei vulnerability scan
            WorkflowTask(
                task_id="nuclei_scan",
                name="Nuclei Vulnerability Scan",
                description="Scan for known vulnerabilities",
                tool="nuclei",
                parameters={
                    "url": target_url,
                    "templates": ["cves", "vulnerabilities", "misconfiguration"],
                    "severity": ["critical", "high", "medium", "low"]
                },
                depends_on=["probe_target"],
                priority=9
            ),
            
            # SQL injection testing
            WorkflowTask(
                task_id="sqli_test",
                name="SQL Injection Test",
                description="Test for SQL injection vulnerabilities",
                tool="sqlmap",
                parameters={
                    "url": target_url,
                    "level": 3,
                    "risk": 2
                },
                depends_on=["probe_target"],
                priority=8
            )
        ]
    )