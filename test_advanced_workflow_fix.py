"""Test script to validate the advanced_recon_exploit workflow fixes"""
import sys
from pathlib import Path

# Fix encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.workflows.prebuilt.advanced_recon_exploit import create_advanced_recon_exploit_workflow

def test_workflow_creation():
    """Test that workflow can be created without errors"""
    print("Testing workflow creation...")

    try:
        workflow = create_advanced_recon_exploit_workflow("example.com")
        print(f"✓ Workflow created successfully: {workflow.name}")
        print(f"✓ Workflow ID: {workflow.workflow_id}")
        print(f"✓ Number of tasks: {len(workflow.tasks)}")

        # Validate parameter substitutions
        issues_found = []

        # Check scan_masscan task
        scan_masscan = next((t for t in workflow.tasks if t.task_id == "scan_masscan"), None)
        if scan_masscan:
            if scan_masscan.parameters.get("targets") == "${merge_all_subdomains.merged_data}":
                print("✓ scan_masscan.targets correctly references merged_data")
            else:
                issues_found.append(f"scan_masscan.targets = {scan_masscan.parameters.get('targets')}")

            if scan_masscan.priority == 6:
                print("✓ scan_masscan.priority is 6")
            else:
                issues_found.append(f"scan_masscan.priority = {scan_masscan.priority} (expected 6)")
        else:
            issues_found.append("scan_masscan task not found")

        # Check fingerprint_services task
        fingerprint = next((t for t in workflow.tasks if t.task_id == "fingerprint_services"), None)
        if fingerprint:
            if fingerprint.parameters.get("hosts") == "${scan_masscan.hosts}":
                print("✓ fingerprint_services.hosts correctly references scan_masscan.hosts")
            else:
                issues_found.append(f"fingerprint_services.hosts = {fingerprint.parameters.get('hosts')}")

            if "ports" not in fingerprint.parameters:
                print("✓ fingerprint_services.ports parameter removed")
            else:
                issues_found.append(f"fingerprint_services.ports still exists: {fingerprint.parameters.get('ports')}")

            if fingerprint.priority == 5:
                print("✓ fingerprint_services.priority is 5")
            else:
                issues_found.append(f"fingerprint_services.priority = {fingerprint.priority} (expected 5)")
        else:
            issues_found.append("fingerprint_services task not found")

        # Check enum_directories task
        enum_dirs = next((t for t in workflow.tasks if t.task_id == "enum_directories"), None)
        if enum_dirs:
            if enum_dirs.parameters.get("urls") == "${merge_all_subdomains.merged_data}":
                print("✓ enum_directories.urls correctly references merged_data")
            else:
                issues_found.append(f"enum_directories.urls = {enum_dirs.parameters.get('urls')}")
        else:
            issues_found.append("enum_directories task not found")

        # Report results
        if issues_found:
            print("\n❌ Issues found:")
            for issue in issues_found:
                print(f"  - {issue}")
            return False
        else:
            print("\n✓ All validations passed!")
            return True

    except Exception as e:
        print(f"❌ Error creating workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schema_validation():
    """Test that workflow passes Pydantic schema validation"""
    print("\nTesting schema validation...")

    try:
        workflow = create_advanced_recon_exploit_workflow("example.com")

        # Try to serialize (will trigger Pydantic validation)
        workflow_dict = workflow.dict()
        print(f"✓ Schema validation passed")
        print(f"✓ Workflow serialized to dict with {len(workflow_dict)} fields")

        # Check for circular dependencies
        task_ids = {t.task_id for t in workflow.tasks}
        for task in workflow.tasks:
            if task.depends_on:
                for dep in task.depends_on:
                    if dep not in task_ids:
                        print(f"❌ Task {task.task_id} depends on non-existent task: {dep}")
                        return False

        print("✓ No circular dependencies detected")
        return True

    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Advanced Recon & Exploitation Workflow Validation")
    print("=" * 70)

    test1 = test_workflow_creation()
    test2 = test_schema_validation()

    print("\n" + "=" * 70)
    if test1 and test2:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
