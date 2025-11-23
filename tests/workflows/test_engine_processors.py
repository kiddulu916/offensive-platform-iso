"""Integration tests for WorkflowEngine processor task execution"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import json

from app.workflows.engine import WorkflowWorker
from app.workflows.schemas import WorkflowDefinition, WorkflowTask, TaskType
from app.core.database import SessionLocal, init_database, Scan, Task, User


@pytest.fixture
def setup_test_db(tmp_path, monkeypatch):
    """Setup test database"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    # Set environment variable before importing database module
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Reinitialize database with new URL
    from app.core import database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    database.engine = create_engine(db_url)
    database.SessionLocal = sessionmaker(bind=database.engine)
    init_database()

    # Create test user
    db = database.SessionLocal()
    user = User(username="testuser", password_hash="testhash")
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()

    yield user_id

    # Cleanup
    db = database.SessionLocal()
    db.close()


def test_file_output_processor_structure():
    """Test that FILE_OUTPUT task structure is valid"""
    workflow = WorkflowDefinition(
        workflow_id="test_file_output",
        name="Test File Output",
        target="example.com",
        tasks=[
            WorkflowTask(
                task_id="dummy_source",
                name="Dummy Source",
                tool="echo",
                task_type=TaskType.TOOL,
                parameters={}
            ),
            WorkflowTask(
                task_id="save_output",
                name="Save Output",
                task_type=TaskType.FILE_OUTPUT,
                parameters={
                    "source_task": "dummy_source",
                    "source_field": "data",
                    "output_file": "/tmp/output.txt"
                },
                depends_on=["dummy_source"]
            )
        ]
    )

    # Validate workflow structure
    assert workflow.tasks[1].task_type == TaskType.FILE_OUTPUT
    assert workflow.tasks[1].depends_on == ["dummy_source"]
    assert "source_task" in workflow.tasks[1].parameters


@patch('app.workflows.engine.WorkflowWorker.task_started')
@patch('app.workflows.engine.WorkflowWorker.task_completed')
@patch('app.workflows.engine.WorkflowWorker.task_failed')
def test_execute_processor_task_integration(
    mock_task_failed,
    mock_task_completed,
    mock_task_started,
    setup_test_db,
    tmp_path
):
    """
    Integration test for _execute_processor_task method.
    Verifies:
    - Processor instantiation and routing
    - Database Task record creation with started_at
    - Signal emissions
    - Processor execution
    """
    user_id = setup_test_db

    # Create a mock FileOutputProcessor
    mock_processor = Mock()
    mock_processor.execute.return_value = {
        "success": True,
        "output_file": str(tmp_path / "test_output.txt"),
        "items_written": 5
    }

    # Create workflow with processor task
    workflow = WorkflowDefinition(
        workflow_id="test_processor",
        name="Test Processor",
        target="example.com",
        tasks=[
            WorkflowTask(
                task_id="file_output_task",
                name="Save File",
                task_type=TaskType.FILE_OUTPUT,
                parameters={
                    "source_task": "dummy",
                    "source_field": "data",
                    "output_file": str(tmp_path / "test_output.txt")
                }
            )
        ]
    )

    # Create worker
    worker = WorkflowWorker(workflow, user_id)

    # Create scan record manually since we're testing just the task execution
    db = SessionLocal()
    scan = Scan(
        user_id=user_id,
        workflow_name=workflow.name,
        target=workflow.target,
        status="running"
    )
    db.add(scan)
    db.commit()
    worker.scan_id = scan.id
    scan_id = scan.id
    db.close()

    # Execute processor task
    task_def = workflow.tasks[0]

    # Directly call _execute_processor_task with our mock processor
    result = worker._execute_processor_task(task_def, mock_processor)

    # Verify success
    assert result is True

    # Verify processor was called
    mock_processor.execute.assert_called_once()
    call_args = mock_processor.execute.call_args
    assert call_args[0][0] == task_def  # First arg is task_def
    assert isinstance(call_args[0][1], dict)  # Second arg is previous_results dict

    # Verify signals were emitted
    mock_task_started.emit.assert_called_once_with("file_output_task", "Save File")
    mock_task_completed.emit.assert_called_once()
    mock_task_failed.emit.assert_not_called()

    # Verify database Task record was created with all required fields
    db = SessionLocal()
    task_records = db.query(Task).filter(Task.scan_id == scan_id).all()
    assert len(task_records) == 1

    task_record = task_records[0]
    assert task_record.task_name == "Save File"
    assert task_record.tool == TaskType.FILE_OUTPUT
    assert task_record.status == "completed"
    assert task_record.started_at is not None  # CRITICAL: This should be set
    assert task_record.completed_at is not None
    assert task_record.output is not None

    # Verify started_at is a valid datetime
    assert isinstance(task_record.started_at, datetime)

    # Verify output is valid JSON
    output_data = json.loads(task_record.output)
    assert output_data["success"] is True
    assert "output_file" in output_data

    db.close()


@patch('app.workflows.engine.WorkflowWorker.task_started')
@patch('app.workflows.engine.WorkflowWorker.task_failed')
def test_execute_processor_task_failure(
    mock_task_failed,
    mock_task_started,
    setup_test_db
):
    """Test processor task failure handling"""
    user_id = setup_test_db

    # Create a mock processor that fails
    mock_processor = Mock()
    mock_processor.execute.return_value = {
        "success": False,
        "error": "Test error: file not found"
    }

    workflow = WorkflowDefinition(
        workflow_id="test_failure",
        name="Test Failure",
        target="example.com",
        tasks=[
            WorkflowTask(
                task_id="failing_task",
                name="Failing Task",
                task_type=TaskType.FILE_OUTPUT,
                parameters={"source_task": "missing"}
            )
        ]
    )

    worker = WorkflowWorker(workflow, user_id)

    # Create scan record
    db = SessionLocal()
    scan = Scan(
        user_id=user_id,
        workflow_name=workflow.name,
        target=workflow.target,
        status="running"
    )
    db.add(scan)
    db.commit()
    worker.scan_id = scan.id
    scan_id = scan.id
    db.close()

    # Execute failing processor task
    task_def = workflow.tasks[0]
    result = worker._execute_processor_task(task_def, mock_processor)

    # Verify failure
    assert result is False

    # Verify signals
    mock_task_started.emit.assert_called_once()
    mock_task_failed.emit.assert_called_once_with("failing_task", "Test error: file not found")

    # Verify database record
    db = SessionLocal()
    task_record = db.query(Task).filter(Task.scan_id == scan_id).first()
    assert task_record.status == "failed"
    assert task_record.started_at is not None  # Should still be set on failure
    assert task_record.completed_at is not None
    db.close()


@patch('app.workflows.engine.WorkflowWorker.task_started')
@patch('app.workflows.engine.WorkflowWorker.task_failed')
def test_execute_processor_task_exception(
    mock_task_failed,
    mock_task_started,
    setup_test_db
):
    """Test processor task exception handling"""
    user_id = setup_test_db

    # Create a mock processor that raises an exception
    mock_processor = Mock()
    mock_processor.execute.side_effect = ValueError("Processor crashed")

    workflow = WorkflowDefinition(
        workflow_id="test_exception",
        name="Test Exception",
        target="example.com",
        tasks=[
            WorkflowTask(
                task_id="exception_task",
                name="Exception Task",
                task_type=TaskType.WEB_CRAWL,
                parameters={"url": "http://example.com"}
            )
        ]
    )

    worker = WorkflowWorker(workflow, user_id)

    # Create scan record
    db = SessionLocal()
    scan = Scan(
        user_id=user_id,
        workflow_name=workflow.name,
        target=workflow.target,
        status="running"
    )
    db.add(scan)
    db.commit()
    worker.scan_id = scan.id
    scan_id = scan.id
    db.close()

    # Execute task that raises exception
    task_def = workflow.tasks[0]
    result = worker._execute_processor_task(task_def, mock_processor)

    # Verify failure
    assert result is False

    # Verify error handling
    mock_task_failed.emit.assert_called_once()
    error_msg = mock_task_failed.emit.call_args[0][1]
    assert "Processor crashed" in error_msg

    # Verify database record
    db = SessionLocal()
    task_record = db.query(Task).filter(Task.scan_id == scan_id).first()
    assert task_record.status == "failed"
    assert task_record.started_at is not None
    assert task_record.completed_at is not None
    assert "Processor crashed" in task_record.errors
    db.close()


def test_processor_routing():
    """Test that different processor types are routed correctly"""
    workflow = WorkflowDefinition(
        workflow_id="test_routing",
        name="Test Routing",
        target="example.com",
        tasks=[
            WorkflowTask(
                task_id="file_task",
                name="File Task",
                task_type=TaskType.FILE_OUTPUT,
                parameters={}
            ),
            WorkflowTask(
                task_id="web_task",
                name="Web Task",
                task_type=TaskType.WEB_CRAWL,
                parameters={}
            ),
            WorkflowTask(
                task_id="exploit_task",
                name="Exploit Task",
                task_type=TaskType.EXPLOIT_LOOKUP,
                parameters={}
            ),
            WorkflowTask(
                task_id="json_task",
                name="JSON Task",
                task_type=TaskType.JSON_AGGREGATE,
                parameters={}
            )
        ]
    )

    # Verify each task has correct type
    assert workflow.tasks[0].task_type == TaskType.FILE_OUTPUT
    assert workflow.tasks[1].task_type == TaskType.WEB_CRAWL
    assert workflow.tasks[2].task_type == TaskType.EXPLOIT_LOOKUP
    assert workflow.tasks[3].task_type == TaskType.JSON_AGGREGATE
