"""
Test logging infrastructure
"""
import pytest
import logging
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.core.logging_config import LoggingConfig, get_workflow_logger, get_tool_logger
from app.workflows.schemas import WorkflowDefinition, WorkflowTask
from app.workflows.engine import WorkflowWorker


def test_logging_setup(tmp_path):
    """Test that logging can be initialized"""
    # Override logs directory
    with patch('app.core.logging_config.settings') as mock_settings:
        mock_settings.LOGS_DIR = tmp_path / "logs"
        mock_settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Setup logging
        LoggingConfig.setup_logging(level=logging.DEBUG)

        # Verify log files are created
        assert (tmp_path / "logs" / "platform.log").exists()
        assert (tmp_path / "logs" / "workflows.log").exists()
        assert (tmp_path / "logs" / "tools.log").exists()


def test_workflow_logger_with_context():
    """Test that workflow logger includes context"""
    logger = get_workflow_logger(scan_id=123, task_id="test_task", tool="nmap")

    # Logger should have context in extra dict
    assert logger.extra['scan_id'] == 123
    assert logger.extra['task_id'] == "test_task"
    assert logger.extra['tool'] == "nmap"


def test_tool_logger_with_context():
    """Test that tool logger includes context"""
    logger = get_tool_logger(tool_name="subfinder", task_id="recon_1")

    # Logger should have context
    assert logger.extra['tool'] == "subfinder"
    assert logger.extra['task_id'] == "recon_1"


def test_workflow_logging_integration(tmp_path, caplog):
    """Test that workflow execution generates logs"""
    # Override logs directory
    with patch('app.core.logging_config.settings') as mock_settings:
        mock_settings.LOGS_DIR = tmp_path / "logs"
        mock_settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

        LoggingConfig.setup_logging(level=logging.DEBUG)

    # Create a simple workflow
    workflow = WorkflowDefinition(
        workflow_id="test_workflow",
        name="Test Workflow",
        target="example.com",
        tasks=[
            WorkflowTask(
                task_id="task1",
                name="Test Task",
                tool="nmap",
                parameters={"target": "example.com"},
                priority=10
            )
        ]
    )

    # Mock database operations
    with patch('app.workflows.engine.SessionLocal') as mock_db_session, \
         patch('app.workflows.engine.ToolRegistry') as mock_registry:

        # Setup mock database
        mock_db = MagicMock()
        mock_db_session.return_value = mock_db

        # Setup mock scan object
        mock_scan = Mock()
        mock_scan.id = 1
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_scan

        # Setup mock tool
        mock_tool = Mock()
        mock_tool.execute.return_value = {
            "success": True,
            "data": {"result": "test"},
            "raw_output": "test output",
            "errors": "",
            "execution_time": 1.5,
            "return_code": 0
        }
        mock_tool_instance = Mock()
        mock_tool_instance.get_tool.return_value = mock_tool
        mock_registry.return_value = mock_tool_instance

        # Create and run workflow worker (don't start thread, just run directly)
        with caplog.at_level(logging.INFO):
            worker = WorkflowWorker(workflow, user_id=1)
            worker.run()

            # Check that key log messages were generated
            assert any("Initializing workflow: Test Workflow" in record.message for record in caplog.records)
            assert any("scan_id=1" in record.message for record in caplog.records)
            assert any("Starting task: Test Task" in record.message for record in caplog.records)


def test_tool_execution_logging(caplog):
    """Test that tool execution generates logs"""
    from app.tools.base import BaseTool, ToolMetadata, ToolCategory

    class TestTool(BaseTool):
        def get_metadata(self):
            return ToolMetadata(
                name="test-tool",
                category=ToolCategory.SCANNING,
                description="Test tool",
                executable="echo"
            )

        def validate_parameters(self, params):
            return True

        def build_command(self, params):
            return ["echo", "test"]

        def parse_output(self, output, stderr, return_code):
            return {"output": output.strip()}

    with caplog.at_level(logging.DEBUG):
        tool = TestTool()
        result = tool.execute({"test": "param"})

        # Check logging occurred
        assert any("Executing tool: test-tool" in record.message for record in caplog.records)
        assert any("Command: echo test" in record.message for record in caplog.records)
        assert any("Tool completed" in record.message for record in caplog.records)

    assert result["success"] == True
    assert "output" in result["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
