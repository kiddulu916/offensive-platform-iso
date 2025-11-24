"""
Workflow schemas and data models
Defines the structure for workflow definitions, tasks, and results
"""
from enum import Enum
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

# ============================================================================
# Enums
# ============================================================================

class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Some tasks completed, some failed

class Severity(str, Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ToolCategory(str, Enum):
    """Tool categories for classification"""
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    ENUMERATION = "enumeration"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"

class TaskType(str, Enum):
    """Types of tasks in a workflow"""
    TOOL = "tool"  # Execute a security tool
    MERGE = "merge"  # Merge/deduplicate results from previous tasks
    FILE_OUTPUT = "file_output"  # Save results to file
    WEB_CRAWL = "web_crawl"  # Crawl websites for input fields
    EXPLOIT_LOOKUP = "exploit_lookup"  # Look up exploits for vulnerabilities
    JSON_AGGREGATE = "json_aggregate"  # Aggregate results into final JSON

# ============================================================================
# Task Configuration
# ============================================================================

class TaskDependency(BaseModel):
    """Defines dependencies between tasks"""
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of task IDs this task depends on"
    )
    condition: str = Field(
        default="all_completed",
        description="Condition type: 'all_completed', 'any_completed', 'specific_output'"
    )
    condition_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional data for conditional dependencies"
    )
    
    @validator('condition')
    def validate_condition(cls, v):
        """Validate condition type"""
        valid_conditions = ['all_completed', 'any_completed', 'specific_output', 'none']
        if v not in valid_conditions:
            raise ValueError(f"Condition must be one of {valid_conditions}")
        return v

class TaskRetryConfig(BaseModel):
    """Configuration for task retry behavior"""
    max_retries: int = Field(default=2, ge=0, le=5, description="Maximum number of retries")
    retry_delay: int = Field(default=30, ge=0, description="Delay between retries in seconds")
    retry_on_timeout: bool = Field(default=True, description="Retry if task times out")
    retry_on_error: bool = Field(default=True, description="Retry on execution error")

class TaskNotification(BaseModel):
    """Notification settings for task completion"""
    on_start: bool = Field(default=False, description="Notify when task starts")
    on_complete: bool = Field(default=False, description="Notify when task completes")
    on_failure: bool = Field(default=True, description="Notify when task fails")

# ============================================================================
# Task Definition
# ============================================================================

class WorkflowTask(BaseModel):
    """Individual task within a workflow"""

    task_id: str = Field(
        ...,
        description="Unique identifier for the task",
        min_length=1,
        max_length=100
    )

    name: str = Field(
        ...,
        description="Human-readable task name",
        min_length=1,
        max_length=200
    )

    description: str = Field(
        default="",
        description="Detailed description of what the task does",
        max_length=500
    )

    task_type: TaskType = Field(
        default=TaskType.TOOL,
        description="Type of task: 'tool' for tool execution, 'merge' for result merging"
    )

    tool: Optional[str] = Field(
        default=None,
        description="Name of the tool to execute (required for task_type='tool')",
        min_length=1
    )

    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to pass to the tool"
    )

    # Merge-specific fields
    merge_sources: Optional[List[str]] = Field(
        default=None,
        description="List of task IDs whose results to merge (required for task_type='merge')"
    )

    merge_field: Optional[str] = Field(
        default=None,
        description="Field to merge on (e.g., 'subdomains', 'ips')"
    )

    dedupe_key: Optional[str] = Field(
        default="name",
        description="Key to use for deduplication within merged data (e.g., 'name' for subdomains)"
    )

    merge_strategy: Optional[str] = Field(
        default="combine",
        description="Merge strategy: 'combine' (merge IPs/data), 'replace' (last wins), 'append' (keep all)"
    )
    
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of task IDs this task depends on"
    )
    
    priority: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Task priority (1=lowest, 10=highest)"
    )
    
    timeout: int = Field(
        default=300,
        ge=10,
        le=7200,
        description="Task timeout in seconds"
    )
    
    retry_config: TaskRetryConfig = Field(
        default_factory=TaskRetryConfig,
        description="Retry configuration"
    )
    
    notification: TaskNotification = Field(
        default_factory=TaskNotification,
        description="Notification settings"
    )
    
    optional: bool = Field(
        default=False,
        description="If True, workflow continues even if this task fails"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the task"
    )
    
    @validator('task_id')
    def validate_task_id(cls, v):
        """Ensure task_id is a valid identifier"""
        # Allow alphanumeric, hyphens, underscores, and periods (for domain names)
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError("task_id must contain only alphanumeric characters, hyphens, underscores, and periods")
        return v

    @validator('tool')
    def validate_tool_field(cls, v, values):
        """Ensure tool is provided for tool tasks"""
        task_type = values.get('task_type', TaskType.TOOL)
        if task_type == TaskType.TOOL and not v:
            raise ValueError("'tool' field is required for task_type='tool'")
        return v

    @validator('merge_sources')
    def validate_merge_sources(cls, v, values):
        """Ensure merge_sources is provided for merge tasks"""
        task_type = values.get('task_type', TaskType.TOOL)
        if task_type == TaskType.MERGE and not v:
            raise ValueError("'merge_sources' field is required for task_type='merge'")
        if v and len(v) < 1:
            raise ValueError("'merge_sources' must contain at least one task ID")
        return v

    @validator('merge_strategy')
    def validate_merge_strategy(cls, v):
        """Validate merge strategy"""
        valid_strategies = ['combine', 'replace', 'append']
        if v and v not in valid_strategies:
            raise ValueError(f"merge_strategy must be one of {valid_strategies}")
        return v

    class Config:
        use_enum_values = True

# ============================================================================
# Workflow Definition
# ============================================================================

class WorkflowMetadata(BaseModel):
    """Metadata for a workflow"""
    author: Optional[str] = Field(default=None, description="Workflow creator")
    version: str = Field(default="1.0.0", description="Workflow version")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[ToolCategory] = Field(default=None, description="Workflow category")
    estimated_duration: Optional[int] = Field(default=None, description="Estimated duration in seconds")

class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    
    workflow_id: str = Field(
        ...,
        description="Unique identifier for the workflow",
        min_length=1,
        max_length=100
    )
    
    name: str = Field(
        ...,
        description="Human-readable workflow name",
        min_length=1,
        max_length=200
    )
    
    description: str = Field(
        default="",
        description="Detailed description of the workflow",
        max_length=1000
    )
    
    target: str = Field(
        ...,
        description="Target for the workflow (URL, IP, domain, etc.)",
        min_length=1
    )
    
    tasks: List[WorkflowTask] = Field(
        ...,
        description="List of tasks in the workflow",
        min_items=1
    )
    
    metadata: WorkflowMetadata = Field(
        default_factory=WorkflowMetadata,
        description="Workflow metadata"
    )
    
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Global variables for the workflow"
    )
    
    stop_on_failure: bool = Field(
        default=False,
        description="If True, stop workflow when any non-optional task fails"
    )
    
    max_parallel_tasks: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of tasks to run in parallel"
    )
    
    @validator('workflow_id')
    def validate_workflow_id(cls, v):
        """Ensure workflow_id is a valid identifier"""
        # Allow alphanumeric, hyphens, underscores, and periods (for domain names)
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError("workflow_id must contain only alphanumeric characters, hyphens, underscores, and periods")
        return v
    
    @validator('tasks')
    def validate_task_dependencies(cls, v):
        """Validate that task dependencies reference valid task IDs"""
        task_ids = {task.task_id for task in v}
        
        for task in v:
            for dep_id in task.depends_on:
                if dep_id not in task_ids:
                    raise ValueError(f"Task '{task.task_id}' depends on non-existent task '{dep_id}'")
        
        return v
    
    @validator('tasks')
    def validate_no_circular_dependencies(cls, v):
        """Ensure there are no circular dependencies"""
        def has_circular_dependency(task_id: str, visited: set, rec_stack: set, deps: Dict[str, List[str]]) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dep in deps.get(task_id, []):
                if dep not in visited:
                    if has_circular_dependency(dep, visited, rec_stack, deps):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        # Build dependency map
        deps = {task.task_id: task.depends_on for task in v}
        
        visited = set()
        rec_stack = set()
        
        for task in v:
            if task.task_id not in visited:
                if has_circular_dependency(task.task_id, visited, rec_stack, deps):
                    raise ValueError(f"Circular dependency detected involving task '{task.task_id}'")
        
        return v
    
    class Config:
        use_enum_values = True

# ============================================================================
# Task Results
# ============================================================================

class TaskResult(BaseModel):
    """Result from a task execution"""
    
    task_id: str = Field(..., description="ID of the task that was executed")
    
    status: TaskStatus = Field(..., description="Execution status")
    
    output: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured output data from the tool"
    )
    
    raw_output: str = Field(
        default="",
        description="Raw output from the tool"
    )
    
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings"
    )
    
    execution_time: float = Field(
        default=0.0,
        ge=0,
        description="Execution time in seconds"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp when task completed"
    )
    
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of times task was retried"
    )
    
    exit_code: Optional[int] = Field(
        default=None,
        description="Exit code from the tool"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the execution"
    )
    
    class Config:
        use_enum_values = True

# ============================================================================
# Workflow Results
# ============================================================================

class WorkflowStatistics(BaseModel):
    """Statistics about workflow execution"""
    total_tasks: int = Field(default=0, description="Total number of tasks")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    failed_tasks: int = Field(default=0, description="Number of failed tasks")
    skipped_tasks: int = Field(default=0, description="Number of skipped tasks")
    total_execution_time: float = Field(default=0.0, description="Total execution time in seconds")
    start_time: Optional[datetime] = Field(default=None, description="Workflow start time")
    end_time: Optional[datetime] = Field(default=None, description="Workflow end time")

class WorkflowResult(BaseModel):
    """Complete result from a workflow execution"""
    
    workflow_id: str = Field(..., description="ID of the executed workflow")
    
    scan_id: Optional[int] = Field(default=None, description="Database scan ID")
    
    status: WorkflowStatus = Field(..., description="Overall workflow status")
    
    task_results: Dict[str, TaskResult] = Field(
        default_factory=dict,
        description="Results from each task, keyed by task_id"
    )
    
    statistics: WorkflowStatistics = Field(
        default_factory=WorkflowStatistics,
        description="Execution statistics"
    )
    
    errors: List[str] = Field(
        default_factory=list,
        description="Workflow-level errors"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="Workflow-level warnings"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        use_enum_values = True

# ============================================================================
# Vulnerability Finding
# ============================================================================

class VulnerabilityFinding(BaseModel):
    """Represents a single vulnerability finding"""
    
    id: Optional[str] = Field(default=None, description="Unique finding ID")
    
    title: str = Field(..., description="Vulnerability title")
    
    description: str = Field(default="", description="Detailed description")
    
    severity: Severity = Field(..., description="Severity level")
    
    cvss_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="CVSS score if applicable"
    )
    
    cve_id: Optional[str] = Field(default=None, description="CVE identifier")
    
    affected_url: Optional[str] = Field(default=None, description="Affected URL or endpoint")
    
    affected_parameter: Optional[str] = Field(default=None, description="Affected parameter")
    
    evidence: str = Field(default="", description="Evidence/proof of vulnerability")
    
    remediation: str = Field(default="", description="Remediation steps")
    
    references: List[str] = Field(
        default_factory=list,
        description="Reference URLs"
    )
    
    discovered_by: str = Field(default="", description="Tool that discovered the finding")
    
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the finding was discovered"
    )
    
    verified: bool = Field(default=False, description="Whether finding has been verified")
    
    false_positive: bool = Field(default=False, description="Marked as false positive")
    
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    
    class Config:
        use_enum_values = True

# ============================================================================
# Report Structures
# ============================================================================

class ReportSection(BaseModel):
    """A section in a report"""
    title: str = Field(..., description="Section title")
    content: str = Field(default="", description="Section content")
    subsections: List['ReportSection'] = Field(default_factory=list, description="Nested subsections")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured data for the section")

# Allow recursive model
ReportSection.update_forward_refs()

class ScanReport(BaseModel):
    """Complete scan report"""
    
    scan_id: int = Field(..., description="Database scan ID")
    
    workflow_name: str = Field(..., description="Name of the workflow")
    
    target: str = Field(..., description="Scan target")
    
    start_time: datetime = Field(..., description="Scan start time")
    
    end_time: Optional[datetime] = Field(default=None, description="Scan end time")
    
    status: WorkflowStatus = Field(..., description="Scan status")
    
    executive_summary: str = Field(default="", description="Executive summary")
    
    findings: List[VulnerabilityFinding] = Field(
        default_factory=list,
        description="All vulnerability findings"
    )
    
    sections: List[ReportSection] = Field(
        default_factory=list,
        description="Report sections"
    )
    
    statistics: WorkflowStatistics = Field(
        default_factory=WorkflowStatistics,
        description="Execution statistics"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Security recommendations"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        use_enum_values = True

# ============================================================================
# Custom Workflow Builder
# ============================================================================

class WorkflowTemplate(BaseModel):
    """Template for creating custom workflows"""
    
    template_id: str = Field(..., description="Template identifier")
    
    name: str = Field(..., description="Template name")
    
    description: str = Field(default="", description="Template description")
    
    category: ToolCategory = Field(..., description="Template category")
    
    required_parameters: List[str] = Field(
        default_factory=list,
        description="Required parameters for instantiation"
    )
    
    optional_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional parameters with defaults"
    )
    
    tasks: List[WorkflowTask] = Field(
        ...,
        description="Task templates"
    )
    
    class Config:
        use_enum_values = True

# ============================================================================
# Helper Functions
# ============================================================================

def create_task_result(
    task_id: str,
    status: TaskStatus,
    output: Dict[str, Any] = None,
    errors: List[str] = None,
    execution_time: float = 0.0
) -> TaskResult:
    """Helper function to create a TaskResult"""
    return TaskResult(
        task_id=task_id,
        status=status,
        output=output or {},
        errors=errors or [],
        execution_time=execution_time,
        timestamp=datetime.utcnow().isoformat()
    )

def create_workflow_statistics(
    total_tasks: int = 0,
    completed_tasks: int = 0,
    failed_tasks: int = 0,
    skipped_tasks: int = 0,
    total_execution_time: float = 0.0
) -> WorkflowStatistics:
    """Helper function to create WorkflowStatistics"""
    return WorkflowStatistics(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        skipped_tasks=skipped_tasks,
        total_execution_time=total_execution_time,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow()
    )