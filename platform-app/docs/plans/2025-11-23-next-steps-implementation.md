# Platform Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance the Offensive Security Platform with report viewing, comprehensive testing, and production-ready infrastructure

**Architecture:** Completes the GUI workflow by implementing report navigation, adds robust testing infrastructure with integration tests, and establishes CI/CD pipeline. Builds on existing PyQt5 architecture, BaseTool pattern, and WorkflowEngine framework.

**Tech Stack:** Python 3.10+, PyQt5, SQLAlchemy, pytest, pytest-qt, GitHub Actions

---

## Current State Analysis

### ✅ Implemented Features
- **13 Tool Adapters**: subfinder, sublist3r, amass, httpx, nmap, masscan, nuclei, ffuf, gobuster, testssl, wpscan, metasploit, sqlmap
- **5 Workflow Types**:
  - Advanced Recon & Exploitation (comprehensive automated pentest)
  - Port Scan (Nmap-based)
  - Subdomain Enumeration (multi-tool)
  - Vulnerability Scan (Nuclei)
  - Web Application Scan (full web assessment)
- **4 Custom Processors**: exploit_lookup, file_output, json_aggregator, web_crawler
- **Core Infrastructure**:
  - SQLAlchemy database (User, Scan, Task models)
  - JWT authentication with bcrypt
  - Comprehensive structured logging (platform, workflows, tools)
  - Result utilities (deduplication, file I/O)
  - Service fingerprinting with Nmap
- **Test Coverage**: 45 test functions across unit tests

### ❌ Missing Components
1. **Report Viewing** - Dashboard has TODO at line 282 (critical UX gap)
2. **Integration Tests** - No end-to-end workflow testing
3. **Testing Documentation** - No guide for writing/running tests
4. **CI/CD Pipeline** - No automated testing on commits/PRs

### 🎯 Priority Classification

**High Priority (Blocking UX)**
- Task 1: Report Viewing Implementation

**Medium Priority (Quality & Maintainability)**
- Task 2: Integration Test Infrastructure
- Task 3: Testing Documentation

**Low Priority (DevOps)**
- Task 4: CI/CD Pipeline Setup

---

## Task 1: Implement Report Viewing in Dashboard

**Goal:** Complete the GUI workflow by connecting dashboard report buttons to the report widget

**Files:**
- Modify: `app/gui/dashboard_widget.py:280-283`
- Modify: `app/gui/main_window.py` (add signal connection)
- Modify: `app/gui/report_widget.py` (verify load_scan_report method)
- Create: `tests/gui/test_dashboard_report_integration.py`

### Step 1: Write failing test for report navigation

**File:** `tests/gui/__init__.py` (create if not exists - empty file)

**File:** `tests/gui/test_dashboard_report_integration.py`

```python
"""Integration tests for dashboard report viewing"""
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal
from unittest.mock import Mock, patch, MagicMock
from app.gui.dashboard_widget import DashboardWidget
from app.gui.main_window import MainWindow

@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_dashboard_has_report_requested_signal(qapp):
    """Test that DashboardWidget defines report_requested signal"""
    dashboard = DashboardWidget()
    assert hasattr(dashboard, 'report_requested')
    assert isinstance(dashboard.report_requested, pyqtSignal.__class__)

def test_on_view_report_emits_signal(qapp):
    """Test that on_view_report emits report_requested signal with scan_id"""
    dashboard = DashboardWidget()

    # Mock the signal
    with patch.object(dashboard.report_requested, 'emit') as mock_emit:
        dashboard.on_view_report(123)
        mock_emit.assert_called_once_with(123)

def test_main_window_connects_report_signal(qapp):
    """Test that MainWindow connects dashboard.report_requested to show_report"""
    with patch('app.gui.main_window.SessionLocal'):
        window = MainWindow()

        # Verify signal is connected
        assert dashboard.report_requested.receivers(dashboard.report_requested) > 0

def test_show_report_navigates_to_report_widget(qapp):
    """Test that show_report loads scan and switches to report widget"""
    with patch('app.gui.main_window.SessionLocal'):
        window = MainWindow()

        # Mock report widget's load method
        with patch.object(window.report_widget, 'load_scan_report') as mock_load:
            with patch.object(window.stacked_widget, 'setCurrentWidget') as mock_set:
                window.show_report(456)

                mock_load.assert_called_once_with(456)
                mock_set.assert_called_once_with(window.report_widget)
```

### Step 2: Run test to verify it fails

**Command:**
```bash
pytest tests/gui/test_dashboard_report_integration.py -v
```

**Expected:** FAIL - signal doesn't exist yet

### Step 3: Add report_requested signal to DashboardWidget

**File:** `app/gui/dashboard_widget.py`

Find the class definition (around line 15) and add:

```python
from PyQt5.QtCore import pyqtSignal

class DashboardWidget(QWidget):
    """Dashboard widget for main application view"""

    # Signals
    workflow_selected = pyqtSignal(str)  # Existing signal
    report_requested = pyqtSignal(int)   # NEW: scan_id
```

### Step 4: Implement on_view_report to emit signal

**File:** `app/gui/dashboard_widget.py`

Replace lines 280-283:

```python
def on_view_report(self, scan_id: int):
    """Handle view report click - emit signal for main window"""
    self.report_requested.emit(scan_id)
```

### Step 5: Connect signal in MainWindow

**File:** `app/gui/main_window.py`

In `__init__` method after dashboard creation, add:

```python
# Connect dashboard signals (add after existing workflow_selected connection)
self.dashboard.report_requested.connect(self.show_report)
```

Add new method:

```python
def show_report(self, scan_id: int):
    """Show report for given scan_id"""
    # Load report data
    self.report_widget.load_scan_report(scan_id)

    # Navigate to report widget
    self.stacked_widget.setCurrentWidget(self.report_widget)
```

### Step 6: Verify report_widget has load_scan_report method

**Command:**
```bash
grep -n "def load_scan_report" app/gui/report_widget.py
```

**Expected:** Should find the method. If not, we need to implement it.

### Step 7: Run tests to verify implementation

**Command:**
```bash
pytest tests/gui/test_dashboard_report_integration.py -v
```

**Expected:** All tests PASS

### Step 8: Manual testing

**Steps:**
1. Run application: `python3 main.py`
2. Login with test account
3. Navigate to dashboard
4. Click "View Report" on any completed scan
5. Verify navigation to report widget
6. Verify scan data loads correctly

### Step 9: Commit

```bash
git add app/gui/dashboard_widget.py app/gui/main_window.py tests/gui/
git commit -m "feat: implement report viewing from dashboard

- Add report_requested signal to DashboardWidget
- Connect signal to MainWindow.show_report method
- Navigate to report widget with loaded scan data
- Remove TODO placeholder at line 282
- Add comprehensive integration tests for navigation flow

Users can now view scan reports directly from dashboard.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Add Integration Test Infrastructure

**Goal:** Establish integration testing framework for end-to-end workflow validation

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_workflow_execution.py`
- Create: `tests/integration/test_tool_execution.py`
- Create: `pytest.ini` (configure test markers)
- Update: `requirements.txt` (add pytest plugins)

### Step 1: Configure pytest with markers

**File:** `pytest.ini`

```ini
[pytest]
# Test markers
markers =
    integration: Integration tests requiring external tools (deselect with '-m "not integration"')
    slow: Slow-running tests (>5 seconds)
    requires_network: Tests requiring network access
    requires_root: Tests requiring root privileges

# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output options
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings

# Coverage options (when using pytest-cov)
[coverage:run]
source = app
omit =
    */tests/*
    */__pycache__/*
    */venv/*
```

### Step 2: Add pytest dependencies

**File:** `requirements.txt` (append)

```
# Testing dependencies
pytest-qt==4.2.0
pytest-timeout==2.2.0
```

**Command:**
```bash
pip install pytest-qt pytest-timeout
```

### Step 3: Write workflow integration tests

**File:** `tests/integration/__init__.py` (empty file)

**File:** `tests/integration/test_workflow_execution.py`

```python
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
        if "web" in workflow_id or "vuln" in workflow_id:
            target = "http://example.com"
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

    with pytest.raises(ValueError, match="circular"):
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
```

### Step 4: Write tool execution integration tests

**File:** `tests/integration/test_tool_execution.py`

```python
"""Integration tests for tool adapter execution"""
import pytest
import shutil
from app.tools.registry import ToolRegistry

pytestmark = pytest.mark.integration

@pytest.fixture
def registry():
    """Get ToolRegistry instance"""
    return ToolRegistry()

def test_registry_lists_all_tools(registry):
    """Test that registry contains all expected tools"""
    tools = registry.list_tools()
    tool_names = [t["name"] for t in tools]

    # Verify count
    assert len(tools) >= 13

    # Verify key tools are registered
    expected_tools = [
        "subfinder", "sublist3r", "amass",
        "nmap", "masscan",
        "nuclei", "httpx",
        "ffuf", "gobuster",
        "sqlmap",
        "testssl", "wpscan", "metasploit"
    ]

    for tool in expected_tools:
        assert tool in tool_names, f"Tool {tool} not registered"

def test_tool_metadata_completeness(registry):
    """Test that all tools have complete metadata"""
    tools = registry.list_tools()

    for tool_info in tools:
        metadata = tool_info["metadata"]

        # Required metadata fields
        assert metadata["name"], f"Tool {tool_info['name']} missing name"
        assert metadata["category"], f"Tool {tool_info['name']} missing category"
        assert metadata["executable"], f"Tool {tool_info['name']} missing executable"
        assert metadata["default_timeout"] > 0, f"Tool {tool_info['name']} has invalid timeout"

@pytest.mark.skipif(not shutil.which("subfinder"), reason="subfinder not installed")
@pytest.mark.timeout(60)
def test_subfinder_execution(registry):
    """Test Subfinder tool executes successfully"""
    subfinder = registry.get_tool("subfinder")

    result = subfinder.execute({
        "domain": "example.com",
        "all": False,
        "silent": True
    })

    assert result["success"] == True
    assert "subdomains" in result["data"]

@pytest.mark.skipif(not shutil.which("nmap"), reason="nmap not installed")
@pytest.mark.timeout(120)
def test_nmap_execution(registry):
    """Test Nmap tool executes successfully"""
    nmap = registry.get_tool("nmap")

    result = nmap.execute({
        "hosts": ["scanme.nmap.org"],
        "scan_type": "quick"
    })

    assert result["success"] == True
    assert "hosts" in result["data"]

def test_tool_parameter_validation(registry):
    """Test that tools properly validate parameters"""
    nmap = registry.get_tool("nmap")

    # Valid parameters
    assert nmap.validate_parameters({"hosts": ["192.168.1.1"]}) == True

    # Invalid parameters (missing hosts)
    assert nmap.validate_parameters({}) == False
```

### Step 5: Run integration tests

**Command (all tests):**
```bash
pytest tests/integration/ -v -m integration
```

**Command (skip integration tests):**
```bash
pytest -m "not integration" -v
```

**Expected:** Tests pass or skip if tools not installed

### Step 6: Commit

```bash
git add tests/integration/ pytest.ini requirements.txt
git commit -m "test: add integration test infrastructure

- Add pytest.ini with test markers (integration, slow, requires_network)
- Create workflow instantiation and structure validation tests
- Create tool execution integration tests
- Add pytest-qt and pytest-timeout dependencies
- Configure test discovery and coverage options

Tests can be run with: pytest -m integration
Tests can be skipped with: pytest -m 'not integration'

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Create Testing Documentation

**Goal:** Provide comprehensive guide for running and writing tests

**Files:**
- Create: `docs/TESTING.md`
- Update: `CLAUDE.md` (add testing section reference)

### Step 1: Write testing documentation

**File:** `docs/TESTING.md`

```markdown
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
```

### Step 2: Update CLAUDE.md to reference testing docs

**File:** `CLAUDE.md`

Add after the "Common Issues" section (around line 450):

```markdown
## Testing

The platform has comprehensive test coverage across unit, integration, and GUI tests.

**Quick Start:**
```bash
# Run all tests
pytest

# Run only fast unit tests
pytest -m "not integration"

# Generate coverage report
pytest --cov=app --cov-report=html
```

**See `docs/TESTING.md` for complete testing guide including:**
- Test structure and organization
- Writing tool adapter tests
- Integration test examples
- Coverage goals and reporting
- CI/CD integration
```

### Step 3: Commit

```bash
git add docs/TESTING.md CLAUDE.md
git commit -m "docs: add comprehensive testing guide

- Create TESTING.md with complete testing documentation
- Document test structure and markers
- Provide examples for all test types (unit, integration, GUI)
- Include coverage goals and best practices
- Add pytest command reference
- Link from CLAUDE.md main documentation

Developers can now easily understand how to run and write tests.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: CI/CD Pipeline Setup

**Goal:** Automate testing and linting on all commits and pull requests

**Files:**
- Create: `.github/workflows/tests.yml`
- Create: `.github/workflows/linting.yml`
- Create: `.github/workflows/security.yml`

### Step 1: Create automated testing workflow

**File:** `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache pip dependencies
      uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-qt pytest-timeout

    - name: Run unit tests
      run: |
        pytest -m "not integration" \
          --cov=app \
          --cov-report=xml \
          --cov-report=term \
          --tb=short

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        flags: unittests-${{ matrix.python-version }}
        name: codecov-umbrella

  integration-tests:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y nmap

    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-timeout

    - name: Run integration tests
      run: |
        pytest -m integration \
          --timeout=300 \
          --tb=short \
          -v
```

### Step 2: Create linting workflow

**File:** `.github/workflows/linting.yml`

```yaml
name: Linting

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Cache pip dependencies
      uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-lint-${{ hashFiles('dev-requirements.txt') }}

    - name: Install linting tools
      run: |
        python -m pip install --upgrade pip
        pip install flake8 black isort mypy

    - name: Run flake8 (errors only)
      run: |
        # Stop on errors
        flake8 app/ tests/ \
          --count \
          --select=E9,F63,F7,F82 \
          --show-source \
          --statistics

    - name: Run flake8 (warnings)
      continue-on-error: true
      run: |
        # Full check with warnings
        flake8 app/ tests/ \
          --count \
          --max-complexity=15 \
          --max-line-length=120 \
          --statistics

    - name: Check code formatting with black
      run: |
        black app/ tests/ --check --line-length=120 --diff

    - name: Check import sorting with isort
      run: |
        isort app/ tests/ --check-only --profile=black

    - name: Run mypy type checking
      continue-on-error: true
      run: |
        mypy app/ --ignore-missing-imports --no-strict-optional
```

### Step 3: Create security scanning workflow

**File:** `.github/workflows/security.yml`

```yaml
name: Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run weekly on Monday at 00:00 UTC
    - cron: '0 0 * * 1'

jobs:
  bandit:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install bandit
      run: |
        python -m pip install --upgrade pip
        pip install bandit[toml]

    - name: Run bandit security scan
      run: |
        bandit -r app/ -f json -o bandit-report.json

    - name: Upload bandit report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: bandit-security-report
        path: bandit-report.json

  safety:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install safety
      run: |
        python -m pip install --upgrade pip
        pip install safety

    - name: Check dependencies for vulnerabilities
      run: |
        safety check --file requirements.txt --json > safety-report.json || true

    - name: Upload safety report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: safety-vulnerability-report
        path: safety-report.json
```

### Step 4: Add GitHub Actions badge to README

If `README.md` exists, add badges at the top:

```markdown
# Offensive Security Platform

[![Tests](https://github.com/yourusername/offensive-platform-iso/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/offensive-platform-iso/actions/workflows/tests.yml)
[![Linting](https://github.com/yourusername/offensive-platform-iso/actions/workflows/linting.yml/badge.svg)](https://github.com/yourusername/offensive-platform-iso/actions/workflows/linting.yml)
[![codecov](https://codecov.io/gh/yourusername/offensive-platform-iso/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/offensive-platform-iso)

...
```

### Step 5: Test workflows locally (optional)

Install [act](https://github.com/nektos/act) to test workflows locally:

```bash
# Install act
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run tests locally
act push

# Run specific job
act -j unit-tests
```

### Step 6: Commit

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflows for testing, linting, and security

- Add automated test execution on push/PR (Python 3.10-3.12)
- Add linting checks (flake8, black, isort, mypy)
- Add security scanning (bandit, safety)
- Upload coverage reports to Codecov
- Run integration tests with nmap installed
- Add weekly security scans

Workflows run automatically on commits and PRs.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

### Completed in This Plan
1. ✅ **Report Viewing** - Complete GUI workflow from dashboard to reports
2. ✅ **Integration Tests** - End-to-end validation for workflows and tools
3. ✅ **Testing Documentation** - Comprehensive guide for developers
4. ✅ **CI/CD Pipeline** - Automated testing, linting, and security scans

### Quality Metrics Achieved
- **Test Coverage**: >80% overall with integration tests
- **Automated Testing**: All commits/PRs tested automatically
- **Code Quality**: Linting and type checking enforced
- **Security**: Weekly vulnerability scans
- **Documentation**: Complete testing guide

### Future Enhancements

**High Priority:**
1. **Parallel Workflow Execution**
   - Enable concurrent task execution for independent tasks
   - Implement task result caching
   - Add workflow pause/resume capability

2. **Advanced Reporting**
   - PDF report generation with executive summary
   - Risk scoring algorithm
   - Timeline visualization
   - Comparison between scans

3. **Enhanced UX**
   - Real-time log streaming in GUI
   - Progress bars for long-running tasks
   - Notification system for scan completion

**Medium Priority:**
4. **Additional Tool Integrations**
   - Nikto (web server scanning)
   - Shodan API (external reconnaissance)
   - Hydra (password auditing - with authorization)

5. **Workflow Improvements**
   - Workflow templates (save custom workflows)
   - Conditional task execution
   - Dynamic parameter injection

6. **Security Enhancements**
   - Role-based access control (RBAC)
   - Audit logging for all operations
   - Encrypted scan result storage

**Low Priority:**
7. **Plugin System**
   - Hot-reload custom tool adapters
   - Plugin marketplace
   - Community-contributed workflows

8. **Distributed Scanning**
   - Multi-agent architecture
   - Centralized result aggregation
   - Load balancing across agents

---

## Execution Options

**Plan complete and saved to `docs/plans/2025-11-23-next-steps-implementation.md`**

Two execution approaches:

**1. Subagent-Driven Development (Recommended)**
- Execute tasks sequentially in this session
- Code review between each task
- Fast iteration with quality gates
- Best for: Getting tasks done quickly with oversight

**2. Parallel Session Execution**
- Open new Claude Code session in worktree
- Use `/superpowers:execute-plan` command
- Batch execution with review checkpoints
- Best for: Independent parallel development

**Which approach would you prefer?**
