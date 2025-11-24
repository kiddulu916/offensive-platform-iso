# Testing Guide

## Overview

The Offensive Security Platform uses pytest for comprehensive test coverage across unit tests, integration tests, and GUI tests.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── gui/                        # GUI component tests (PyQt5)
│   └── test_dashboard_report_integration.py
├── integration/                # End-to-end integration tests
│   ├── test_workflow_execution.py
│   └── test_tool_execution.py
├── tools/                      # Tool adapter unit tests
│   ├── test_nmap_adapter.py
│   ├── test_masscan_adapter.py
│   └── ...
├── workflows/                  # Workflow engine tests
│   ├── test_engine_processors.py
│   ├── test_file_output_processor.py
│   └── ...
└── utils/                      # Utility module tests
    └── test_result_utils.py
```

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only (Fast)
```bash
pytest -m "not integration" -v
```

### Integration Tests Only
```bash
pytest -m integration -v
```

### Specific Test File
```bash
pytest tests/tools/test_nmap_adapter.py -v
```

### Specific Test Function
```bash
pytest tests/test_registry.py::test_registry_contains_new_tools -v
```

### With Coverage Report
```bash
pytest --cov=app --cov-report=html --cov-report=term
# Open htmlcov/index.html in browser
```

### Watch Mode (Auto-run on file changes)
```bash
pip install pytest-watch
ptw -- -m "not integration"
```

## Test Markers

Tests are organized with pytest markers for selective execution:

- `@pytest.mark.integration` - Integration tests requiring external tools
- `@pytest.mark.slow` - Tests taking >5 seconds
- `@pytest.mark.requires_network` - Tests requiring network access
- `@pytest.mark.requires_root` - Tests requiring root privileges (e.g., masscan)

### Examples

**Skip slow tests:**
```bash
pytest -m "not slow" -v
```

**Run only network tests:**
```bash
pytest -m requires_network -v
```

**Skip integration and slow:**
```bash
pytest -m "not integration and not slow" -v
```

## Writing Tests

### Tool Adapter Tests

Every tool adapter should have comprehensive unit tests:

```python
import pytest
from app.tools.adapters.your_adapter import YourAdapter
from app.tools.base import ToolCategory

def test_adapter_metadata():
    """Test adapter returns correct metadata"""
    adapter = YourAdapter()
    metadata = adapter.get_metadata()

    assert metadata.name == "your-tool"
    assert metadata.category == ToolCategory.SCANNING
    assert metadata.executable == "your-tool-binary"
    assert metadata.default_timeout > 0

def test_adapter_validate_parameters():
    """Test parameter validation"""
    adapter = YourAdapter()

    # Valid parameters
    assert adapter.validate_parameters({"target": "example.com"}) == True

    # Invalid parameters
    assert adapter.validate_parameters({}) == False

def test_adapter_build_command():
    """Test command building"""
    adapter = YourAdapter()
    cmd = adapter.build_command({"target": "example.com"})

    assert "your-tool-binary" in cmd
    assert "example.com" in cmd

def test_adapter_parse_output():
    """Test output parsing"""
    adapter = YourAdapter()
    sample_output = "output from tool"

    result = adapter.parse_output(sample_output, "", 0)

    assert "expected_field" in result
    assert isinstance(result["expected_field"], list)
```

### Workflow Processor Tests

Test custom processors with mock task data:

```python
from app.workflows.processors.your_processor import YourProcessor
from app.workflows.schemas import WorkflowTask, TaskType

def test_processor_execute(tmp_path):
    """Test processor execution with mock data"""
    processor = YourProcessor()

    task = WorkflowTask(
        task_id="test_task",
        name="Test Task",
        task_type=TaskType.YOUR_TYPE,
        parameters={
            "param1": "value1",
            "output_file": str(tmp_path / "output.json")
        }
    )

    previous_results = {
        "source_task": {
            "data": [{"item": 1}, {"item": 2}]
        }
    }

    result = processor.execute(task, previous_results)

    assert result["success"] == True
    assert (tmp_path / "output.json").exists()
```

### Integration Tests

Integration tests validate end-to-end functionality:

```python
import pytest
import shutil

@pytest.mark.integration
@pytest.mark.skipif(not shutil.which("tool-name"), reason="tool not installed")
@pytest.mark.timeout(60)
def test_tool_integration():
    """Test tool executes in real environment"""
    from app.tools.registry import ToolRegistry

    registry = ToolRegistry()
    tool = registry.get_tool("tool-name")

    result = tool.execute({"target": "example.com"})

    assert result["success"] == True
    assert len(result["data"]) > 0
```

### GUI Tests

Test PyQt5 widgets with pytest-qt:

```python
import pytest
from PyQt5.QtWidgets import QApplication
from unittest.mock import patch
from app.gui.your_widget import YourWidget

@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_widget_signal_emission(qapp):
    """Test widget emits correct signals"""
    widget = YourWidget()

    with patch.object(widget.some_signal, 'emit') as mock_emit:
        widget.trigger_action()
        mock_emit.assert_called_once()
```

## Coverage Goals

Target coverage percentages by module:

- **Tool Adapters**: 100% (all methods must be tested)
- **Workflow Processors**: 100% (critical business logic)
- **Core Modules**: >85% (auth, database, logging)
- **GUI Modules**: >60% (supplemented with manual testing)
- **Overall Project**: >80%

### Checking Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=term-missing

# Generate HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Continuous Integration

Tests run automatically on:
- Every push to main/develop branches
- Every pull request
- Nightly builds (full integration test suite)

See `.github/workflows/tests.yml` for CI configuration.

## Common Issues

### PyQt5 ImportError

If you see `ModuleNotFoundError: No module named 'PyQt5'`:
```bash
pip install PyQt5
```

### Tool Not Found

Integration tests skip automatically if tools aren't installed:
```bash
# Install missing tools (Kali Linux)
sudo apt-get install subfinder nmap masscan nuclei httpx-toolkit

# Check which tools are installed
python check_tools.py
```

### Database Conflicts

Tests use isolated databases. If you see database lock errors:
```bash
rm -f data/test.db
pytest
```

### Slow Tests

Speed up development by skipping integration tests:
```bash
pytest -m "not integration" --maxfail=1 -x
```

## Best Practices

1. **Test-Driven Development** - Write tests before implementation
2. **Descriptive Names** - Test names should describe what they verify
3. **One Assertion Per Concept** - Multiple asserts OK if testing same concept
4. **Use Fixtures** - Share setup code via pytest fixtures
5. **Mock External Dependencies** - Use `unittest.mock` for external services
6. **Test Edge Cases** - Empty inputs, invalid data, error conditions
7. **Keep Tests Fast** - Unit tests should run in milliseconds
8. **Independent Tests** - Tests should not depend on execution order

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
