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


def test_json_aggregator_optional_sections(tmp_path):
    """Test optional section skipping when source task not found"""
    processor = JsonAggregatorProcessor()

    task = WorkflowTask(
        task_id="aggregate_results",
        name="Aggregate Results",
        task_type=TaskType.JSON_AGGREGATE,
        parameters={
            "output_file": str(tmp_path / "results.json"),
            "sections": [
                {"name": "required_section", "source_task": "task1", "source_field": "data", "optional": False},
                {"name": "optional_section", "source_task": "task2", "source_field": "data", "optional": True},
                {"name": "another_required", "source_task": "task3", "source_field": "data", "optional": False}
            ]
        }
    )

    previous_results = {
        "task1": {"data": ["item1", "item2"]},
        # task2 is missing - should be skipped
        "task3": {"data": ["item3"]}
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == True
    assert result["sections_written"] == 2  # Only task1 and task3

    # Verify JSON content
    with open(tmp_path / "results.json") as f:
        data = json.load(f)

    assert "required_section" in data
    assert "another_required" in data
    assert "optional_section" not in data  # Should be skipped
    assert data["required_section"] == ["item1", "item2"]
    assert data["another_required"] == ["item3"]


def test_json_aggregator_missing_required_task(tmp_path):
    """Test error when required source task is missing"""
    processor = JsonAggregatorProcessor()

    task = WorkflowTask(
        task_id="aggregate_results",
        name="Aggregate Results",
        task_type=TaskType.JSON_AGGREGATE,
        parameters={
            "output_file": str(tmp_path / "results.json"),
            "sections": [
                {"name": "section1", "source_task": "missing_task", "source_field": "data", "optional": False}
            ]
        }
    )

    previous_results = {
        "other_task": {"data": ["value"]}
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == False
    assert "Required source task 'missing_task' not found" in result["error"]
    assert not (tmp_path / "results.json").exists()


def test_json_aggregator_metadata_toggle(tmp_path):
    """Test metadata inclusion and exclusion"""
    processor = JsonAggregatorProcessor()

    # Test with metadata enabled (default)
    task_with_metadata = WorkflowTask(
        task_id="aggregate_with_meta",
        name="Aggregate With Metadata",
        task_type=TaskType.JSON_AGGREGATE,
        parameters={
            "output_file": str(tmp_path / "with_metadata.json"),
            "sections": [
                {"name": "data", "source_task": "task1", "source_field": "results"}
            ],
            "include_metadata": True
        }
    )

    previous_results = {
        "task1": {"results": ["test"]}
    }

    result = processor.execute(task_with_metadata, previous_results)

    assert result["success"] == True

    with open(tmp_path / "with_metadata.json") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "generated_at" in data["metadata"]
    assert "workflow_id" in data["metadata"]
    assert data["metadata"]["workflow_id"] == "aggregate_with_meta"
    assert data["metadata"]["total_sections"] == 1

    # Test with metadata disabled
    task_without_metadata = WorkflowTask(
        task_id="aggregate_no_meta",
        name="Aggregate Without Metadata",
        task_type=TaskType.JSON_AGGREGATE,
        parameters={
            "output_file": str(tmp_path / "without_metadata.json"),
            "sections": [
                {"name": "data", "source_task": "task1", "source_field": "results"}
            ],
            "include_metadata": False
        }
    )

    result = processor.execute(task_without_metadata, previous_results)

    assert result["success"] == True
    assert result["sections_written"] == 1  # Only data section, no metadata

    with open(tmp_path / "without_metadata.json") as f:
        data = json.load(f)

    assert "metadata" not in data
    assert "data" in data
    assert data["data"] == ["test"]
