import pytest
import json
from pathlib import Path
from app.workflows.processors.json_aggregator import JsonAggregatorProcessor
from app.workflows.schemas import WorkflowTask, TaskType

def test_json_aggregator_basic(tmp_path):
    """Test basic JSON aggregation"""
    processor = JsonAggregatorProcessor()

    task = WorkflowTask(
        task_id="aggregate_results",
        name="Aggregate Results",
        task_type=TaskType.JSON_AGGREGATE,
        parameters={
            "output_file": str(tmp_path / "final_results.json"),
            "sections": [
                {"name": "subdomains", "source_task": "merge_subdomains", "source_field": "merged_data"},
                {"name": "ports", "source_task": "scan_masscan", "source_field": "hosts"}
            ]
        }
    )

    previous_results = {
        "merge_subdomains": {
            "merged_data": [
                {"name": "www.example.com", "ips": ["1.1.1.1"]}
            ]
        },
        "scan_masscan": {
            "hosts": [
                {"ip": "1.1.1.1", "ports": [{"port": 80}]}
            ]
        }
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == True
    assert (tmp_path / "final_results.json").exists()

    # Load and verify JSON
    with open(tmp_path / "final_results.json") as f:
        data = json.load(f)

    assert "subdomains" in data
    assert "ports" in data
    assert len(data["subdomains"]) == 1
