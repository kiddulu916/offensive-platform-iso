import pytest
from pathlib import Path
from app.workflows.processors.file_output import FileOutputProcessor
from app.workflows.schemas import WorkflowTask, TaskType

def test_file_output_processor_subdomains(tmp_path):
    """Test saving subdomain list to file"""
    processor = FileOutputProcessor()

    task = WorkflowTask(
        task_id="save_subdomains",
        name="Save Subdomains",
        task_type=TaskType.FILE_OUTPUT,
        parameters={
            "source_task": "enum_amass",
            "source_field": "subdomains",
            "output_file": str(tmp_path / "subdomains.txt"),
            "extract_field": "name"
        }
    )

    previous_results = {
        "enum_amass": {
            "subdomains": [
                {"name": "www.example.com", "ips": ["1.1.1.1"]},
                {"name": "mail.example.com", "ips": ["2.2.2.2"]}
            ]
        }
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == True
    assert (tmp_path / "subdomains.txt").exists()

    lines = (tmp_path / "subdomains.txt").read_text().strip().split('\n')
    assert len(lines) == 2
    assert "www.example.com" in lines

def test_file_output_processor_ips(tmp_path):
    """Test saving IP list to file"""
    processor = FileOutputProcessor()

    task = WorkflowTask(
        task_id="save_ips",
        name="Save IPs",
        task_type=TaskType.FILE_OUTPUT,
        parameters={
            "source_task": "scan_masscan",
            "source_field": "hosts",
            "output_file": str(tmp_path / "ips.txt"),
            "extract_field": "ip"
        }
    )

    previous_results = {
        "scan_masscan": {
            "hosts": [
                {"ip": "1.1.1.1", "ports": []},
                {"ip": "2.2.2.2", "ports": []}
            ]
        }
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == True
    lines = (tmp_path / "ips.txt").read_text().strip().split('\n')
    assert set(lines) == {"1.1.1.1", "2.2.2.2"}

def test_file_output_processor_json_format(tmp_path):
    """Test saving data in JSON format"""
    processor = FileOutputProcessor()

    task = WorkflowTask(
        task_id="save_json",
        name="Save JSON Data",
        task_type=TaskType.FILE_OUTPUT,
        parameters={
            "source_task": "scan_results",
            "source_field": "hosts",
            "output_file": str(tmp_path / "hosts.json"),
            "format": "json"
        }
    )

    previous_results = {
        "scan_results": {
            "hosts": [
                {"ip": "1.1.1.1", "ports": [80, 443]},
                {"ip": "2.2.2.2", "ports": [22, 80]}
            ]
        }
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == True
    assert (tmp_path / "hosts.json").exists()

    import json
    with open(tmp_path / "hosts.json") as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["ip"] == "1.1.1.1"

def test_file_output_missing_source_task(tmp_path):
    """Test error handling when source task is not found"""
    processor = FileOutputProcessor()

    task = WorkflowTask(
        task_id="save_data",
        name="Save Data",
        task_type=TaskType.FILE_OUTPUT,
        parameters={
            "source_task": "nonexistent_task",
            "source_field": "data",
            "output_file": str(tmp_path / "output.txt")
        }
    )

    previous_results = {
        "other_task": {"data": ["value1", "value2"]}
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == False
    assert "not found in previous results" in result["error"]

def test_file_output_missing_field(tmp_path):
    """Test error handling when source field is not found"""
    processor = FileOutputProcessor()

    task = WorkflowTask(
        task_id="save_data",
        name="Save Data",
        task_type=TaskType.FILE_OUTPUT,
        parameters={
            "source_task": "scan_task",
            "source_field": "nonexistent_field",
            "output_file": str(tmp_path / "output.txt")
        }
    )

    previous_results = {
        "scan_task": {"hosts": ["host1", "host2"]}
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == False
    assert "not found in source task results" in result["error"]

def test_file_output_single_value(tmp_path):
    """Test handling of single value (non-list) data"""
    processor = FileOutputProcessor()

    task = WorkflowTask(
        task_id="save_single",
        name="Save Single Value",
        task_type=TaskType.FILE_OUTPUT,
        parameters={
            "source_task": "task1",
            "source_field": "target",
            "output_file": str(tmp_path / "target.txt")
        }
    )

    previous_results = {
        "task1": {"target": "example.com"}
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == True
    assert (tmp_path / "target.txt").exists()

    content = (tmp_path / "target.txt").read_text().strip()
    assert content == "example.com"

def test_file_output_nested_list_flattening(tmp_path):
    """Test that nested lists are flattened when extracting fields"""
    processor = FileOutputProcessor()

    task = WorkflowTask(
        task_id="save_ips",
        name="Save All IPs",
        task_type=TaskType.FILE_OUTPUT,
        parameters={
            "source_task": "enum_task",
            "source_field": "subdomains",
            "output_file": str(tmp_path / "all_ips.txt"),
            "extract_field": "ips"
        }
    )

    previous_results = {
        "enum_task": {
            "subdomains": [
                {"name": "www.example.com", "ips": ["1.1.1.1", "1.1.1.2"]},
                {"name": "mail.example.com", "ips": ["2.2.2.2"]},
                {"name": "ftp.example.com", "ips": ["3.3.3.3", "3.3.3.4", "3.3.3.5"]}
            ]
        }
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == True
    lines = (tmp_path / "all_ips.txt").read_text().strip().split('\n')

    # Should be flattened to 6 IPs total, not 3 lists
    assert len(lines) == 6
    assert "1.1.1.1" in lines
    assert "1.1.1.2" in lines
    assert "2.2.2.2" in lines
    assert "3.3.3.3" in lines
    assert "3.3.3.4" in lines
    assert "3.3.3.5" in lines
