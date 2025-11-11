"""Complete web application security assessment workflow"""
from app.workflows.schemas import WorkflowDefinition, WorkflowTask

def create_web_app_workflow(target_url: str) -> WorkflowDefinition:
    """
    Create a comprehensive web application scanning workflow
    
    Phases:
    1. Reconnaissance - Subdomain enumeration
    2. Discovery - HTTP probing and directory fuzzing
    3. Vulnerability Scanning - Multiple vulnerability checks
    4. Exploitation - SQL injection testing
    """
    
    # Extract domain from URL
    domain = target_url.replace("https://", "").replace("http://", "").split("/")[0]
    base_domain = ".".join(domain.split(".")[-2:]) if "." in domain else domain
    
    return WorkflowDefinition(
        workflow_id=f"webapp_full_{domain}",
        name="Full Web Application Security Scan",
        description="Complete assessment from reconnaissance to vulnerability scanning",
        target=target_url,
        tasks=[
            # Phase 1: Reconnaissance
            WorkflowTask(
                task_id="recon_subdomains",
                name="Subdomain Enumeration",
                description="Discover all subdomains using subfinder",
                tool="subfinder",
                parameters={
                    "domain": base_domain,
                    "all": True
                },
                depends_on=[],
                priority=10
            ),
            
            # Phase 2: Discovery
            WorkflowTask(
                task_id="discovery_http_probe",
                name="HTTP Probing",
                description="Probe discovered subdomains for web services",
                tool="httpx",
                parameters={
                    "urls": "${recon_subdomains.unique_subdomains}",
                    "status_code": True,
                    "title": True,
                    "tech_detect": True,
                    "threads": 50
                },
                depends_on=["recon_subdomains"],
                priority=9
            ),
            
            WorkflowTask(
                task_id="discovery_directories",
                name="Directory Discovery",
                description="Discover hidden directories and files",
                tool="ffuf",
                parameters={
                    "url": f"{target_url}/FUZZ",
                    "wordlist": "/usr/share/wordlists/dirb/common.txt",
                    "extensions": ["php", "html", "js", "txt", "xml"],
                    "match_codes": [200, 204, 301, 302, 307, 401, 403],
                    "threads": 40
                },
                depends_on=["discovery_http_probe"],
                priority=8
            ),
            
            # Phase 3: Vulnerability Scanning
            WorkflowTask(
                task_id="vuln_nuclei_scan",
                name="Nuclei Vulnerability Scan",
                description="Comprehensive vulnerability assessment",
                tool="nuclei",
                parameters={
                    "urls": "${discovery_http_probe.live_urls}",
                    "templates": ["cves", "vulnerabilities", "exposures"],
                    "severity": ["critical", "high", "medium"],
                    "concurrency": 25
                },
                depends_on=["discovery_http_probe"],
                priority=7
            ),
            
            # Phase 4: Exploitation (SQL Injection)
            WorkflowTask(
                task_id="exploit_sqli_test",
                name="SQL Injection Testing",
                description="Test for SQL injection vulnerabilities",
                tool="sqlmap",
                parameters={
                    "url": target_url,
                    "level": 2,
                    "risk": 2,
                    "threads": 3,
                    "enum_dbs": True
                },
                depends_on=["discovery_directories"],
                priority=6
            )
        ]
    )