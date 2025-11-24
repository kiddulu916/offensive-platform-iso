"""Complete web application security assessment workflow"""
from app.workflows.schemas import WorkflowDefinition, WorkflowTask, TaskType

def create_web_app_workflow(target_url: str) -> WorkflowDefinition:
    """
    Create a comprehensive web application scanning workflow

    Phases:
    1. Reconnaissance - Subdomain enumeration with multiple tools
    2. Merge - Deduplicate and combine results
    3. Port Scanning - Identify open ports and services
    4. Discovery - HTTP probing and directory fuzzing
    5. Vulnerability Scanning - Multiple vulnerability checks
    6. Exploitation - SQL injection testing
    """

    # Extract domain from URL
    domain = target_url.replace("https://", "").replace("http://", "").split("/")[0]
    base_domain = ".".join(domain.split(".")[-2:]) if "." in domain else domain

    return WorkflowDefinition(
        workflow_id=f"webapp_full_{domain}",
        name="Full Web Application Security Scan",
        description="Complete assessment from reconnaissance to exploitation",
        target=target_url,
        tasks=[
            # Phase 1: Reconnaissance
            WorkflowTask(
                task_id="recon_amass",
                name="Amass Subdomain Enumeration",
                description="In-depth subdomain discovery with Amass (ASNs, IPs, subdomains)",
                tool="amass",
                parameters={
                    "domain": base_domain,
                    "passive": True
                },
                depends_on=[],
                priority=10
            ),

            WorkflowTask(
                task_id="recon_subfinder",
                name="Subfinder Subdomain Enumeration",
                description="Fast subdomain enumeration with Subfinder",
                tool="subfinder",
                parameters={
                    "domain": base_domain,
                    "all": True,
                    "resolve": True
                },
                depends_on=[],
                priority=10
            ),

            # Phase 2: Merge and Deduplicate
            WorkflowTask(
                task_id="merge_subdomains",
                name="Merge and Deduplicate Subdomains",
                description="Combine Amass and Subfinder results, merge IPs, remove duplicates",
                task_type=TaskType.MERGE,
                tool=None,
                parameters={},
                merge_sources=["recon_amass", "recon_subfinder"],
                merge_field="subdomains",
                dedupe_key="name",
                merge_strategy="combine",
                depends_on=["recon_amass", "recon_subfinder"],
                priority=9
            ),

            # Phase 3: Port Scanning
            WorkflowTask(
                task_id="scan_ports",
                name="Port Scanning",
                description="Scan discovered IPs for open ports and services",
                tool="nmap",
                parameters={
                    "domain": base_domain,  # Will use ips.txt from merge task
                    "scan_type": "default"
                },
                depends_on=["merge_subdomains"],
                priority=8
            ),

            # Phase 4: Discovery
            WorkflowTask(
                task_id="discovery_http_probe",
                name="HTTP Probing",
                description="Probe discovered subdomains for web services",
                tool="httpx",
                parameters={
                    "urls": "${merge_subdomains.merged_data}",
                    "status_code": True,
                    "title": True,
                    "tech_detect": True,
                    "threads": 50
                },
                depends_on=["scan_ports"],
                priority=7
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
                priority=6
            ),

            # Phase 5: Vulnerability Scanning
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
                priority=5
            ),

            # Phase 6: Exploitation (SQL Injection)
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
                priority=4
            )
        ]
    )