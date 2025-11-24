"""Integration tests for workflow execution engine"""
import pytest
import shutil
from pathlib import Path
from app.workflows.prebuilt import WorkflowFactory
from app.workflows.schemas import TaskStatus

# Skip all tests if tools not installed
pytestmark = pytest.mark.integration

def test_workflow_factory_lists_all_workflows():
    """Test that WorkflowFactory returns all registered workflows"""
    workflows = WorkflowFactory.list_workflows()

    assert len(workflows) >= 5
    workflow_ids = [w["id"] for w in workflows]

    assert "port_scan" in workflow_ids
    assert "subdomain_enum" in workflow_ids
    assert "vuln_scan" in workflow_ids
    assert "web_app_full" in workflow_ids
    assert "advanced_recon_exploit" in workflow_ids

def test_workflow_instantiation():
    """Test that all workflows can be instantiated with valid structure"""
    workflows = WorkflowFactory.list_workflows()

    for workflow_info in workflows:
        workflow_id = workflow_info["id"]

        # Use appropriate target for each workflow type
        # Use simple targets without protocols to avoid workflow_id validation issues
        if "web" in workflow_id or "vuln" in workflow_id:
            target = "example.com"
        else:
            target = "example.com"

        workflow = WorkflowFactory.create_workflow(workflow_id, target)

        # Validate workflow structure
        assert workflow is not None
        assert workflow.workflow_id
        assert workflow.name
        assert workflow.target == target
        assert len(workflow.tasks) > 0

        # Validate each task
        for task in workflow.tasks:
            assert task.task_id
            assert task.name
            # Task must have either tool or task_type
            assert task.tool or task.task_type

@pytest.mark.skipif(not shutil.which("subfinder"), reason="subfinder not installed")
def test_subdomain_enum_workflow_structure():
    """Test subdomain enumeration workflow has correct structure"""
    workflow = WorkflowFactory.create_workflow("subdomain_enum", "example.com")

    assert "subdomain" in workflow.name.lower()
    assert workflow.target == "example.com"

    # Should have at least 2 tasks (enumeration + aggregation)
    assert len(workflow.tasks) >= 2

    # Verify task dependencies are valid
    task_ids = {task.task_id for task in workflow.tasks}
    for task in workflow.tasks:
        if task.depends_on:
            for dep in task.depends_on:
                assert dep in task_ids, f"Task {task.task_id} depends on non-existent task {dep}"

@pytest.mark.skipif(not shutil.which("nmap"), reason="nmap not installed")
def test_port_scan_workflow_structure():
    """Test port scan workflow targets single host"""
    workflow = WorkflowFactory.create_workflow("port_scan", "192.168.1.1")

    assert "port" in workflow.name.lower() or "scan" in workflow.name.lower()
    assert workflow.target == "192.168.1.1"
    assert len(workflow.tasks) > 0

def test_advanced_recon_workflow_has_all_phases():
    """Test advanced recon workflow includes all expected phases"""
    workflow = WorkflowFactory.create_workflow("advanced_recon_exploit", "example.com")

    task_names = [task.name.lower() for task in workflow.tasks]

    # Verify key phases are present
    has_subdomain_enum = any("subdomain" in name or "enum" in name for name in task_names)
    has_port_scan = any("port" in name or "masscan" in name or "nmap" in name for name in task_names)
    has_exploit_lookup = any("exploit" in name for name in task_names)

    assert has_subdomain_enum, "Missing subdomain enumeration phase"
    assert has_port_scan, "Missing port scanning phase"
    assert has_exploit_lookup, "Missing exploit lookup phase"

def test_workflow_validates_circular_dependencies():
    """Test that workflow validation catches circular dependencies"""
    from app.workflows.schemas import WorkflowDefinition, WorkflowTask
    from pydantic_core import ValidationError

    with pytest.raises(ValidationError, match="Circular"):
        WorkflowDefinition(
            workflow_id="test_circular",
            name="Test Circular",
            target="example.com",
            tasks=[
                WorkflowTask(
                    task_id="task_a",
                    name="Task A",
                    tool="nmap",
                    depends_on=["task_b"]
                ),
                WorkflowTask(
                    task_id="task_b",
                    name="Task B",
                    tool="subfinder",
                    depends_on=["task_a"]  # Circular!
                )
            ]
        )
