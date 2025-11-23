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
