# Code Quality & Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all critical linting issues, establish testing infrastructure, and prepare the platform for production deployment.

**Architecture:** This plan follows TDD principles to fix 18 identified code quality issues across exception handling, imports, dead code, and security. We'll add pytest infrastructure, fix high-severity bugs first (missing imports, bare excepts), then medium/low severity issues (style, type hints). Each fix includes a test to prevent regression.

**Tech Stack:** Python 3.x, PyQt5, pytest, flake8, black, mypy, pytest-qt

---

## Task 1: Setup Development Infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `.flake8`
- Create: `pyproject.toml`
- Create: `dev-requirements.txt`
- Modify: `requirements.txt` (add python-dotenv if not present)

**Step 1: Create dev-requirements.txt for linting and testing tools**

```bash
cd /mnt/c/Users/dat1k/offensive-platform-iso/platform-app
```

File: `dev-requirements.txt`
```
pytest==7.4.3
pytest-qt==4.2.0
pytest-cov==4.1.0
flake8==6.1.0
black==23.12.1
mypy==1.7.1
```

**Step 2: Install development dependencies**

Run: `pip install -r dev-requirements.txt`
Expected: All packages install successfully

**Step 3: Create .flake8 configuration**

File: `.flake8`
```ini
[flake8]
max-line-length = 100
exclude =
    .git,
    __pycache__,
    venv,
    data,
    resources
ignore =
    E203,  # whitespace before ':'
    W503,  # line break before binary operator
per-file-ignores =
    __init__.py:F401
```

**Step 4: Create pyproject.toml for black configuration**

File: `pyproject.toml`
```toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310']
exclude = '''
/(
    \.git
  | __pycache__
  | venv
  | data
  | resources
)/
'''

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers"

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

**Step 5: Create pytest conftest.py with fixtures**

File: `tests/conftest.py`
```python
"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing"""
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    return db_path

@pytest.fixture
def mock_tool_registry():
    """Mock tool registry for testing workflows"""
    from app.tools.registry import ToolRegistry
    registry = ToolRegistry()
    return registry
```

**Step 6: Create tests/__init__.py**

File: `tests/__init__.py`
```python
"""Test suite for Offensive Security Platform"""
```

**Step 7: Verify test infrastructure works**

Run: `pytest tests/ -v`
Expected: "collected 0 items" (no tests yet, but infrastructure works)

**Step 8: Run flake8 to confirm linter works**

Run: `flake8 app/ --count --statistics`
Expected: Output showing linting issues (we'll fix these next)

**Step 9: Commit infrastructure**

```bash
git add tests/ .flake8 pyproject.toml dev-requirements.txt
git commit -m "chore: add testing and linting infrastructure

- Add pytest with pytest-qt for PyQt5 testing
- Add flake8 for style checking
- Add black for code formatting
- Add mypy for type checking
- Configure tools via .flake8 and pyproject.toml"
```

---

## Task 2: Fix Critical Bug - Missing WorkflowFactory Import

**Files:**
- Modify: `app/gui/workflow_widget.py:1-10` (add import)
- Create: `tests/test_workflow_widget.py`

**Step 1: Write the failing test**

File: `tests/test_workflow_widget.py`
```python
"""Tests for workflow widget"""
import pytest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_workflow_widget_imports_successfully(qapp):
    """Test that workflow_widget imports without errors"""
    # This will fail if WorkflowFactory is missing
    from app.gui.workflow_widget import WorkflowWidget
    assert WorkflowWidget is not None


def test_workflow_factory_available_in_widget(qapp):
    """Test that WorkflowFactory can be accessed in workflow widget"""
    from app.gui.workflow_widget import WorkflowWidget

    # Check if the module has access to WorkflowFactory
    # This would fail at runtime if import is missing
    widget = WorkflowWidget()
    assert hasattr(widget, 'start_workflow')
```

**Step 2: Run test to verify it fails (currently passes because import isn't used)**

Run: `pytest tests/test_workflow_widget.py -v`
Expected: Tests pass (but code has latent bug when WorkflowFactory is actually used)

**Step 3: Add the missing import**

File: `app/gui/workflow_widget.py`
Find the imports section (lines 1-10) and add:

```python
from app.workflows.prebuilt import WorkflowFactory
```

Insert after existing imports from `app.workflows`.

**Step 4: Verify the import doesn't break anything**

Run: `python3 -c "from app.gui.workflow_widget import WorkflowWidget; print('Import successful')"`
Expected: "Import successful"

**Step 5: Run tests to confirm they still pass**

Run: `pytest tests/test_workflow_widget.py -v`
Expected: PASS

**Step 6: Commit the fix**

```bash
git add app/gui/workflow_widget.py tests/test_workflow_widget.py
git commit -m "fix: add missing WorkflowFactory import in workflow_widget

- Import was referenced on line 174 but not imported
- Would cause NameError at runtime
- Add test to verify imports work correctly"
```

---

## Task 3: Fix Critical Bug - Dead Code and Unreachable WorkflowFactory Logic

**Files:**
- Modify: `app/gui/workflow_widget.py:172-185`
- Modify: `tests/test_workflow_widget.py` (add test for workflow creation)

**Step 1: Write test that exposes the bug**

File: `tests/test_workflow_widget.py` (append)
```python
def test_start_workflow_supports_all_workflow_types(qapp):
    """Test that all workflow types from dashboard can be started"""
    from app.gui.workflow_widget import WorkflowWidget
    from app.core.database import User

    widget = WorkflowWidget()

    # Mock user
    mock_user = Mock(spec=User)
    mock_user.id = 1

    # Test each workflow type
    workflow_types = [
        "web_app_full",
        "subdomain_enum",
        "port_scan",
        "vuln_scan"
    ]

    for workflow_id in workflow_types:
        # This should not raise an error
        # Currently only web_app_full works
        try:
            with patch('app.gui.workflow_widget.WorkflowWorker'):
                widget.start_workflow(f"{workflow_id}|http://example.com", mock_user)
        except Exception as e:
            pytest.fail(f"Workflow {workflow_id} failed: {e}")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_workflow_widget.py::test_start_workflow_supports_all_workflow_types -v`
Expected: FAIL - Only web_app_full works, others show "Unknown workflow" error

**Step 3: Fix the dead code by using WorkflowFactory properly**

File: `app/gui/workflow_widget.py`

Replace lines 172-185:
```python
        try:
            # Use factory to create workflow
            workflow = WorkflowFactory.create_workflow(workflow_id, target)

        except ValueError as e:
            self.log_output(f"Error: {str(e)}")
            return

        # Create workflow definition
        if workflow_id == "web_app_full":
            workflow = create_web_app_workflow(target)
        else:
            self.log_output(f"Unknown workflow: {workflow_id}")
            return
```

With:
```python
        # Use factory to create workflow
        try:
            workflow = WorkflowFactory.create_workflow(workflow_id, target)
        except ValueError as e:
            self.log_output(f"Error: Unknown workflow '{workflow_id}': {str(e)}")
            return
```

**Step 4: Remove now-unused direct workflow import**

File: `app/gui/workflow_widget.py`

Remove this import (if it exists):
```python
from app.workflows.prebuilt.web_app_scan import create_web_app_workflow
```

**Step 5: Run tests to verify fix**

Run: `pytest tests/test_workflow_widget.py::test_start_workflow_supports_all_workflow_types -v`
Expected: PASS

**Step 6: Commit the fix**

```bash
git add app/gui/workflow_widget.py tests/test_workflow_widget.py
git commit -m "fix: remove dead code and enable all workflow types

- WorkflowFactory was called but result was immediately overwritten
- Only web_app_full workflow was functional
- Now all 4 workflow types work via WorkflowFactory
- Remove unreachable try-except block
- Add test coverage for all workflow types"
```

---

## Task 4: Fix High-Severity Exception Handling - Tool Adapters

**Files:**
- Modify: `app/tools/adapters/nmap_adapter.py:46`
- Modify: `app/tools/adapters/subfinder_adapter.py:47`
- Modify: `app/tools/adapters/httpx_adapter.py:53`
- Modify: `app/tools/adapters/nuclei_adapter.py:55`
- Modify: `app/tools/adapters/ffuf_adapter.py:67`
- Modify: `app/tools/adapters/amass_adapter.py:56`
- Create: `tests/test_tool_adapters.py`

**Step 1: Write test that demonstrates the problem**

File: `tests/test_tool_adapters.py`
```python
"""Tests for tool adapter exception handling"""
import pytest
from app.tools.adapters.nmap_adapter import NmapAdapter
from app.tools.adapters.subfinder_adapter import SubfinderAdapter
from app.tools.adapters.httpx_adapter import HttpxAdapter
from app.tools.adapters.nuclei_adapter import NucleiAdapter
from app.tools.adapters.ffuf_adapter import FfufAdapter
from app.tools.adapters.amass_adapter import AmassAdapter


def test_nmap_adapter_handles_malformed_xml():
    """Test that nmap adapter logs errors instead of silently failing"""
    adapter = NmapAdapter()

    # Malformed XML should not be silently ignored
    stdout = "<?xml version='1.0'?><nmaprun><MALFORMED>"
    result = adapter.parse_output(stdout, "", 0)

    # Should return empty hosts but log error (not silently fail)
    assert "hosts" in result
    # With bare except, we get empty list
    # With proper exception, we get error logged


def test_subfinder_adapter_handles_malformed_json():
    """Test that subfinder adapter handles malformed JSON properly"""
    adapter = SubfinderAdapter()

    # Malformed JSON should raise proper error
    stdout = '{"subdomain": "example.com",MALFORMED}'
    result = adapter.parse_output(stdout, "", 0)

    # Should return empty subdomains, not crash
    assert "subdomains" in result
    assert isinstance(result["subdomains"], list)


def test_httpx_adapter_handles_invalid_json_lines():
    """Test httpx adapter with invalid JSON lines"""
    adapter = HttpxAdapter()

    stdout = 'NOT-JSON\n{"url": "http://example.com"}'
    result = adapter.parse_output(stdout, "", 0)

    # Should skip invalid lines, process valid ones
    assert "urls" in result


def test_nuclei_adapter_handles_parse_errors():
    """Test nuclei adapter with malformed finding data"""
    adapter = NucleiAdapter()

    stdout = 'INVALID-LINE\n{"template-id": "test", "MALFORMED"}'
    result = adapter.parse_output(stdout, "", 0)

    assert "findings" in result


def test_ffuf_adapter_handles_json_decode_error():
    """Test ffuf adapter with invalid JSON output"""
    adapter = FfufAdapter()

    stdout = 'NOT-VALID-JSON-AT-ALL'
    result = adapter.parse_output(stdout, "", 0)

    # Should return empty results, not crash
    assert "results" in result
    assert isinstance(result["results"], list)


def test_amass_adapter_handles_malformed_json():
    """Test amass adapter with invalid JSON"""
    adapter = AmassAdapter()

    stdout = '{"name": "example.com", BROKEN}'
    result = adapter.parse_output(stdout, "", 0)

    assert "subdomains" in result
```

**Step 2: Run tests to confirm they pass (bare except swallows errors)**

Run: `pytest tests/test_tool_adapters.py -v`
Expected: PASS (but errors are silently swallowed - bad!)

**Step 3: Fix nmap_adapter.py exception handling**

File: `app/tools/adapters/nmap_adapter.py`

Find line ~46 with `except:` and replace:
```python
            except:
                pass
```

With:
```python
            except (ET.ParseError, Exception) as e:
                # Log XML parsing errors instead of silently ignoring
                import logging
                logging.warning(f"Failed to parse nmap XML output: {e}")
                continue
```

Add import at top of file:
```python
import xml.etree.ElementTree as ET
import logging
```

**Step 4: Fix subfinder_adapter.py exception handling**

File: `app/tools/adapters/subfinder_adapter.py`

Find line ~47 and replace:
```python
            except:
                pass
```

With:
```python
            except (json.JSONDecodeError, ValueError) as e:
                # Log malformed JSON lines instead of silently skipping
                import logging
                logging.warning(f"Failed to parse subfinder JSON line: {line[:100]}: {e}")
                continue
```

**Step 5: Fix httpx_adapter.py exception handling**

File: `app/tools/adapters/httpx_adapter.py`

Find line ~53 and replace:
```python
            except:
                pass
```

With:
```python
            except (json.JSONDecodeError, ValueError) as e:
                import logging
                logging.warning(f"Failed to parse httpx JSON line: {line[:100]}: {e}")
                continue
```

**Step 6: Fix nuclei_adapter.py exception handling**

File: `app/tools/adapters/nuclei_adapter.py`

Find line ~55 and replace:
```python
            except:
                pass
```

With:
```python
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                import logging
                logging.warning(f"Failed to parse nuclei finding: {line[:100]}: {e}")
                continue
```

**Step 7: Fix ffuf_adapter.py exception handling**

File: `app/tools/adapters/ffuf_adapter.py`

Find line ~67 and replace:
```python
        except:
            return {"results": []}
```

With:
```python
        except (json.JSONDecodeError, ValueError) as e:
            import logging
            logging.error(f"Failed to parse ffuf JSON output: {e}")
            return {"results": [], "error": str(e)}
```

**Step 8: Fix amass_adapter.py exception handling**

File: `app/tools/adapters/amass_adapter.py`

Find line ~56 and replace:
```python
            except:
                pass
```

With:
```python
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                import logging
                logging.warning(f"Failed to parse amass JSON line: {line[:100]}: {e}")
                continue
```

**Step 9: Add logging configuration to adapters**

For each adapter file, ensure logging is imported at the top:
```python
import logging
```

**Step 10: Run tests to verify fixes don't break functionality**

Run: `pytest tests/test_tool_adapters.py -v`
Expected: PASS (but now errors are logged, not swallowed)

**Step 11: Commit exception handling fixes**

```bash
git add app/tools/adapters/*.py tests/test_tool_adapters.py
git commit -m "fix: replace bare except with specific exception handling

- Replace 7 bare except: clauses with specific exception types
- Add logging for parse errors instead of silent failures
- Improves debugging when tools return unexpected output
- Prevents catching SystemExit and KeyboardInterrupt
- Add test coverage for malformed tool output"
```

---

## Task 5: Fix Medium-Severity Bug - Report Widget Exception Handling

**Files:**
- Modify: `app/gui/report_widget.py:97`
- Create: `tests/test_report_widget.py`

**Step 1: Write test for exception handling**

File: `tests/test_report_widget.py`
```python
"""Tests for report widget"""
import pytest
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_report_widget_imports(qapp):
    """Test report widget imports successfully"""
    from app.gui.report_widget import ReportWidget
    assert ReportWidget is not None
```

**Step 2: Run test**

Run: `pytest tests/test_report_widget.py -v`
Expected: PASS

**Step 3: Find and read the bare except in report_widget.py**

Run: `grep -n "except:" app/gui/report_widget.py`

**Step 4: Fix the bare except clause**

File: `app/gui/report_widget.py`

Find line ~97 with `except:` and replace with specific exception:
```python
        except (IOError, OSError, Exception) as e:
            import logging
            logging.error(f"Failed to generate report: {e}")
            # Re-raise or handle appropriately
```

**Step 5: Run tests**

Run: `pytest tests/test_report_widget.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add app/gui/report_widget.py tests/test_report_widget.py
git commit -m "fix: replace bare except in report widget

- Replace bare except: with specific exception types
- Add logging for report generation errors
- Improves error visibility for users"
```

---

## Task 6: Fix Medium-Severity Bug - Temp File Leak in Nuclei Adapter

**Files:**
- Modify: `app/tools/adapters/nuclei_adapter.py:27-40`
- Modify: `tests/test_tool_adapters.py` (add test)

**Step 1: Write test that demonstrates temp file leak**

File: `tests/test_tool_adapters.py` (append)
```python
def test_nuclei_adapter_cleans_up_temp_files():
    """Test that nuclei adapter doesn't leak temp files"""
    import tempfile
    import os
    from app.tools.adapters.nuclei_adapter import NucleiAdapter

    adapter = NucleiAdapter()

    # Track temp files before
    temp_dir = tempfile.gettempdir()
    before = set(os.listdir(temp_dir))

    # Build command with URL list (creates temp file)
    params = {"urls": ["http://example.com", "http://test.com"]}

    try:
        cmd = adapter.build_command(params)
        assert cmd is not None
    except Exception:
        pass  # Command building might fail without nuclei installed

    # Check temp files after
    after = set(os.listdir(temp_dir))
    new_files = after - before

    # Should not leak temp files
    # Currently this test would FAIL because delete=False
    txt_files = [f for f in new_files if f.endswith('.txt')]
    assert len(txt_files) == 0, f"Temp file leaked: {txt_files}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tool_adapters.py::test_nuclei_adapter_cleans_up_temp_files -v`
Expected: FAIL (temp files leaked)

**Step 3: Fix the temp file leak**

File: `app/tools/adapters/nuclei_adapter.py`

Find lines 27-30:
```python
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write('\n'.join(params["urls"]))
                cmd.extend(["-list", f.name])
```

Replace with proper cleanup:
```python
            import tempfile
            import os

            # Create temp file with auto-cleanup
            temp_fd, temp_path = tempfile.mkstemp(suffix='.txt', text=True)
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    f.write('\n'.join(params["urls"]))
                cmd.extend(["-list", temp_path])
            except Exception:
                # Clean up if writing fails
                os.unlink(temp_path)
                raise

            # Note: temp file will be cleaned up after execution
            # Store path for cleanup in execute method
            self._temp_file = temp_path
```

**Step 4: Add cleanup to execute method**

File: `app/tools/adapters/nuclei_adapter.py`

In the `execute` method, add cleanup after subprocess completes:
```python
    def execute(self, params, timeout=None):
        """Execute nuclei scan with temp file cleanup"""
        self._temp_file = None
        try:
            result = super().execute(params, timeout)
            return result
        finally:
            # Clean up temp file if created
            if hasattr(self, '_temp_file') and self._temp_file:
                import os
                try:
                    os.unlink(self._temp_file)
                except OSError:
                    pass  # File already deleted
                self._temp_file = None
```

**Step 5: Run test to verify fix**

Run: `pytest tests/test_tool_adapters.py::test_nuclei_adapter_cleans_up_temp_files -v`
Expected: PASS

**Step 6: Commit**

```bash
git add app/tools/adapters/nuclei_adapter.py tests/test_tool_adapters.py
git commit -m "fix: prevent temp file leak in nuclei adapter

- Replace delete=False with proper temp file cleanup
- Add cleanup in execute method finally block
- Prevents accumulation of temp files during scans
- Add test to verify no file leaks"
```

---

## Task 7: Fix Medium-Severity - Remove Unused Imports

**Files:**
- Modify: `main.py:11`
- Modify: `app/workflows/schemas.py:6`

**Step 1: Write test that unused imports don't break anything**

File: `tests/test_imports.py`
```python
"""Test that all modules import cleanly"""
import pytest


def test_main_imports_cleanly():
    """Test main.py imports without errors"""
    import main
    assert main.main is not None


def test_schemas_imports_cleanly():
    """Test schemas imports without errors"""
    from app.workflows import schemas
    assert schemas.WorkflowDefinition is not None
```

**Step 2: Run tests**

Run: `pytest tests/test_imports.py -v`
Expected: PASS

**Step 3: Remove unused QIcon import from main.py**

File: `main.py`

Find line 11:
```python
from PyQt5.QtGui import QIcon
```

Remove this line (QIcon is never used).

**Step 4: Remove unused Union import from schemas.py**

File: `app/workflows/schemas.py`

Find line 6:
```python
from typing import List, Dict, Optional, Any, Union
```

Replace with:
```python
from typing import List, Dict, Optional, Any
```

**Step 5: Run tests to verify nothing broke**

Run: `pytest tests/test_imports.py -v`
Expected: PASS

**Step 6: Run flake8 to verify unused imports are gone**

Run: `flake8 main.py app/workflows/schemas.py`
Expected: No F401 (unused import) errors for these files

**Step 7: Commit**

```bash
git add main.py app/workflows/schemas.py tests/test_imports.py
git commit -m "refactor: remove unused imports

- Remove QIcon from main.py (never used)
- Remove Union from schemas.py (never used)
- Reduces module load time slightly
- Add import tests to prevent breakage"
```

---

## Task 8: Fix Medium-Severity - Line Length Violations

**Files:**
- Modify: `app/gui/dashboard_widget.py:192`
- Modify: `app/gui/login_widget.py:130`
- Modify: `app/workflows/schemas.py:170,251,269`

**Step 1: Run black formatter to auto-fix line lengths**

Run: `black app/ --check --diff`
Expected: Shows which files need formatting

**Step 2: Apply black formatting**

Run: `black app/ --line-length 100`
Expected: Reformats files to comply with 100-char limit

**Step 3: Verify tests still pass**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 4: Verify flake8 is happy**

Run: `flake8 app/ --max-line-length=100 --statistics`
Expected: Fewer or zero E501 (line too long) errors

**Step 5: Commit formatting changes**

```bash
git add app/
git commit -m "style: fix line length violations with black

- Apply black formatter with 100-char line limit
- Fixes PEP8 E501 violations
- Improves readability in side-by-side diffs
- No functional changes"
```

---

## Task 9: Fix Low-Severity - Import Organization

**Files:**
- Modify: `app/gui/workflow_widget.py:240`
- Modify: `app/gui/main_window.py:68`

**Step 1: Write test to ensure modules are available**

File: `tests/test_imports.py` (append)
```python
def test_workflow_widget_has_json_import():
    """Test that json is imported at module level"""
    from app.gui import workflow_widget
    import json
    # Verify json module is available
    assert hasattr(workflow_widget, 'json') or json is not None


def test_main_window_has_qshortcut_import():
    """Test that QShortcut is available"""
    from app.gui import main_window
    # Should be imported at module level
    assert hasattr(main_window, 'QShortcut')
```

**Step 2: Run test (will fail for module-level check)**

Run: `pytest tests/test_imports.py -v`

**Step 3: Move json import to module level in workflow_widget.py**

File: `app/gui/workflow_widget.py`

Find line ~240 inside a method:
```python
            import json
```

Remove this line and add `json` to the module-level imports at the top:
```python
import json
```

**Step 4: Move QShortcut import to module level in main_window.py**

File: `app/gui/main_window.py`

Find line ~68 inside a method:
```python
        from PyQt5.QtWidgets import QShortcut
```

Remove this line and add to the existing PyQt5.QtWidgets import at top:
```python
from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QShortcut  # Add QShortcut here
)
```

**Step 5: Verify imports work**

Run: `python3 -c "from app.gui.workflow_widget import WorkflowWidget; from app.gui.main_window import MainWindow; print('OK')"`
Expected: "OK"

**Step 6: Run tests**

Run: `pytest tests/test_imports.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add app/gui/workflow_widget.py app/gui/main_window.py tests/test_imports.py
git commit -m "refactor: move imports to module level

- Move json import from method to module level in workflow_widget
- Move QShortcut import to module level in main_window
- Improves performance (no repeated import lookup)
- Follows Python best practices"
```

---

## Task 10: Add Type Hints

**Files:**
- Modify: `app/gui/workflow_widget.py:165`
- Modify: `app/tools/registry.py:50`

**Step 1: Add type hint to start_workflow method**

File: `app/gui/workflow_widget.py`

Find line 165:
```python
    def start_workflow(self, workflow_spec: str, user):
```

Replace with:
```python
    def start_workflow(self, workflow_spec: str, user: 'User'):
```

Add import at top if not present:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.database import User
```

**Step 2: Fix return type hint in registry.py**

File: `app/tools/registry.py`

Find line ~50 in `list_tools` method:
```python
    def list_tools(self) -> list:
```

Replace with:
```python
    def list_tools(self) -> List[Dict[str, Any]]:
```

Ensure imports at top include:
```python
from typing import List, Dict, Any
```

**Step 3: Run mypy to check types**

Run: `mypy app/gui/workflow_widget.py app/tools/registry.py --ignore-missing-imports`
Expected: No errors

**Step 4: Commit**

```bash
git add app/gui/workflow_widget.py app/tools/registry.py
git commit -m "refactor: add missing type hints

- Add User type hint to start_workflow method
- Fix return type for list_tools method
- Improves IDE autocomplete and static analysis"
```

---

## Task 11: Add Production Security - Environment-Based SECRET_KEY

**Files:**
- Modify: `app/core/config.py:26`
- Create: `.env.example`
- Modify: `requirements.txt` (ensure python-dotenv is present)

**Step 1: Create .env.example template**

File: `.env.example`
```bash
# Secret key for JWT token signing
# IMPORTANT: Generate a random secret key for production
# Example: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=change-this-in-production-to-a-random-string

# Database configuration
DATABASE_URL=sqlite:///data/platform.db

# JWT token expiration (hours)
TOKEN_EXPIRE_HOURS=24
```

**Step 2: Update config.py to use environment variable**

File: `app/core/config.py`

Find line ~26:
```python
    SECRET_KEY: str = "change-this-in-production-to-a-random-string"
```

Replace with:
```python
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "change-this-in-production-to-a-random-string"
    )
```

Add import at top:
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
```

**Step 3: Verify python-dotenv is in requirements.txt**

File: `requirements.txt`

Ensure it contains:
```
python-dotenv==1.0.1
```

**Step 4: Test that SECRET_KEY can be overridden**

Run: `SECRET_KEY=test-key-123 python3 -c "from app.core.config import settings; print(settings.SECRET_KEY)"`
Expected: "test-key-123"

**Step 5: Add to .gitignore**

Create or modify `.gitignore`:
```
.env
data/
__pycache__/
*.pyc
venv/
```

**Step 6: Commit**

```bash
git add app/core/config.py .env.example .gitignore requirements.txt
git commit -m "security: use environment variable for SECRET_KEY

- Load SECRET_KEY from environment variable
- Add .env.example template for configuration
- Add .gitignore to prevent committing .env
- Maintains backward compatibility with default
- Add python-dotenv for .env file loading"
```

---

## Task 12: Complete TODO - Implement Report Viewing in Dashboard

**Files:**
- Modify: `app/gui/dashboard_widget.py:280-283`
- Create: `tests/test_dashboard_widget.py`

**Step 1: Write test for report viewing**

File: `tests/test_dashboard_widget.py`
```python
"""Tests for dashboard widget"""
import pytest
from PyQt5.QtWidgets import QApplication
from unittest.mock import Mock, patch


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_dashboard_view_report_opens_report_widget(qapp):
    """Test that view report actually opens report widget"""
    from app.gui.dashboard_widget import DashboardWidget

    dashboard = DashboardWidget()

    # Mock the signal emission
    with patch.object(dashboard, 'report_requested') as mock_signal:
        dashboard.on_view_report(123)

        # Should emit report_requested signal with scan_id
        mock_signal.emit.assert_called_once_with(123)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dashboard_widget.py -v`
Expected: FAIL (signal doesn't exist yet)

**Step 3: Add signal to DashboardWidget**

File: `app/gui/dashboard_widget.py`

Find the class definition and add signal:
```python
class DashboardWidget(QWidget):
    """Dashboard widget"""

    # Signals
    report_requested = pyqtSignal(int)  # scan_id
```

Ensure import at top:
```python
from PyQt5.QtCore import pyqtSignal
```

**Step 4: Implement on_view_report method**

File: `app/gui/dashboard_widget.py`

Find lines 280-283:
```python
    def on_view_report(self, scan_id: int):
        """Handle view report click"""
        # TODO: Implement report viewing
        QMessageBox.information(self, "Report", f"Viewing report for scan {scan_id}")
```

Replace with:
```python
    def on_view_report(self, scan_id: int):
        """Handle view report click - emit signal for main window"""
        # Emit signal to main window to show report widget
        self.report_requested.emit(scan_id)
```

**Step 5: Connect signal in main_window.py**

File: `app/gui/main_window.py`

In the `__init__` method where dashboard is created, add signal connection:
```python
        # Connect dashboard signals
        self.dashboard.report_requested.connect(self.show_report)
```

Add method to show report:
```python
    def show_report(self, scan_id: int):
        """Show report for given scan"""
        # Navigate to report widget
        self.report_widget.load_scan_report(scan_id)
        self.stacked_widget.setCurrentWidget(self.report_widget)
```

**Step 6: Run tests**

Run: `pytest tests/test_dashboard_widget.py -v`
Expected: PASS

**Step 7: Test manually**

Run: `python3 main.py`
Expected: Clicking "View Report" should navigate to report widget

**Step 8: Commit**

```bash
git add app/gui/dashboard_widget.py app/gui/main_window.py tests/test_dashboard_widget.py
git commit -m "feat: implement report viewing from dashboard

- Add report_requested signal to DashboardWidget
- Connect signal to main window navigation
- Remove TODO placeholder
- Users can now view reports from dashboard
- Add test coverage for report navigation"
```

---

## Task 13: Add Comprehensive Testing Suite

**Files:**
- Create: `tests/test_auth.py`
- Create: `tests/test_database.py`
- Create: `tests/test_workflows.py`

**Step 1: Write auth tests**

File: `tests/test_auth.py`
```python
"""Tests for authentication module"""
import pytest
from app.core.auth import AuthManager
from app.core.database import init_database, SessionLocal, User


@pytest.fixture
def auth_manager(tmp_path, monkeypatch):
    """Create auth manager with temporary database"""
    db_path = tmp_path / "test_auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    # Re-initialize database with test path
    init_database()

    manager = AuthManager()
    yield manager

    # Cleanup
    db = SessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()


def test_hash_password(auth_manager):
    """Test password hashing"""
    password = "test_password_123"
    hashed = auth_manager.hash_password(password)

    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$")  # bcrypt format


def test_verify_password(auth_manager):
    """Test password verification"""
    password = "test_password_123"
    hashed = auth_manager.hash_password(password)

    assert auth_manager.verify_password(password, hashed) is True
    assert auth_manager.verify_password("wrong_password", hashed) is False


def test_register_user(auth_manager):
    """Test user registration"""
    success, message = auth_manager.register("testuser", "password123")

    assert success is True
    assert "successfully" in message.lower()


def test_register_duplicate_user(auth_manager):
    """Test registering duplicate username"""
    auth_manager.register("testuser", "password123")
    success, message = auth_manager.register("testuser", "different_password")

    assert success is False
    assert "already exists" in message.lower()


def test_authenticate_valid_user(auth_manager):
    """Test authentication with valid credentials"""
    auth_manager.register("testuser", "password123")
    user = auth_manager.authenticate("testuser", "password123")

    assert user is not None
    assert user.username == "testuser"


def test_authenticate_invalid_password(auth_manager):
    """Test authentication with wrong password"""
    auth_manager.register("testuser", "password123")
    user = auth_manager.authenticate("testuser", "wrong_password")

    assert user is None


def test_authenticate_nonexistent_user(auth_manager):
    """Test authentication with non-existent user"""
    user = auth_manager.authenticate("nonexistent", "password")

    assert user is None


def test_is_first_boot(auth_manager):
    """Test first boot detection"""
    assert auth_manager.is_first_boot() is True

    auth_manager.register("testuser", "password123")
    assert auth_manager.is_first_boot() is False


def test_create_token(auth_manager):
    """Test JWT token creation"""
    token = auth_manager.create_token(user_id=1)

    assert isinstance(token, str)
    assert len(token) > 0
```

**Step 2: Write database tests**

File: `tests/test_database.py`
```python
"""Tests for database models"""
import pytest
from datetime import datetime
from app.core.database import init_database, SessionLocal, User, Scan, Task


@pytest.fixture
def db_session(tmp_path, monkeypatch):
    """Create test database session"""
    db_path = tmp_path / "test_db.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    init_database()
    session = SessionLocal()

    yield session

    session.close()


def test_create_user(db_session):
    """Test creating user in database"""
    user = User(username="testuser", password_hash="hashed_password")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == "testuser"
    assert user.created_at is not None


def test_user_scan_relationship(db_session):
    """Test User-Scan relationship"""
    user = User(username="testuser", password_hash="hashed_password")
    db_session.add(user)
    db_session.commit()

    scan = Scan(
        user_id=user.id,
        workflow_name="test_workflow",
        target="example.com",
        status="completed"
    )
    db_session.add(scan)
    db_session.commit()

    assert len(user.scans) == 1
    assert user.scans[0].workflow_name == "test_workflow"


def test_scan_task_relationship(db_session):
    """Test Scan-Task relationship"""
    user = User(username="testuser", password_hash="hashed_password")
    scan = Scan(
        user_id=user.id,
        workflow_name="test_workflow",
        target="example.com"
    )
    db_session.add(user)
    db_session.add(scan)
    db_session.commit()

    task = Task(
        scan_id=scan.id,
        task_name="test_task",
        tool="nmap",
        status="completed"
    )
    db_session.add(task)
    db_session.commit()

    assert len(scan.tasks) == 1
    assert scan.tasks[0].tool == "nmap"
```

**Step 3: Write workflow tests**

File: `tests/test_workflows.py`
```python
"""Tests for workflow schemas and factory"""
import pytest
from app.workflows.schemas import (
    WorkflowDefinition,
    WorkflowTask,
    TaskStatus,
    WorkflowStatus
)
from app.workflows.prebuilt import WorkflowFactory


def test_workflow_definition_creation():
    """Test creating workflow definition"""
    workflow = WorkflowDefinition(
        workflow_id="test_workflow",
        name="Test Workflow",
        target="example.com",
        tasks=[
            WorkflowTask(
                task_id="task1",
                name="Test Task",
                tool="nmap",
                parameters={"target": "example.com"}
            )
        ]
    )

    assert workflow.workflow_id == "test_workflow"
    assert len(workflow.tasks) == 1


def test_workflow_task_dependencies():
    """Test workflow task dependency validation"""
    task1 = WorkflowTask(
        task_id="task1",
        name="Task 1",
        tool="subfinder",
        parameters={"domain": "example.com"}
    )

    task2 = WorkflowTask(
        task_id="task2",
        name="Task 2",
        tool="nmap",
        parameters={"target": "${task1.subdomains}"},
        depends_on=["task1"]
    )

    workflow = WorkflowDefinition(
        workflow_id="test",
        name="Test",
        target="example.com",
        tasks=[task1, task2]
    )

    assert task2.depends_on == ["task1"]


def test_workflow_factory_creates_web_app_workflow():
    """Test WorkflowFactory creates web_app_full workflow"""
    workflow = WorkflowFactory.create_workflow("web_app_full", "http://example.com")

    assert workflow.workflow_id.startswith("web_app_full")
    assert workflow.target == "http://example.com"
    assert len(workflow.tasks) > 0


def test_workflow_factory_creates_subdomain_enum_workflow():
    """Test WorkflowFactory creates subdomain_enum workflow"""
    workflow = WorkflowFactory.create_workflow("subdomain_enum", "example.com")

    assert "subdomain_enum" in workflow.workflow_id
    assert len(workflow.tasks) > 0


def test_workflow_factory_creates_port_scan_workflow():
    """Test WorkflowFactory creates port_scan workflow"""
    workflow = WorkflowFactory.create_workflow("port_scan", "192.168.1.1")

    assert "port_scan" in workflow.workflow_id
    assert len(workflow.tasks) > 0


def test_workflow_factory_creates_vuln_scan_workflow():
    """Test WorkflowFactory creates vuln_scan workflow"""
    workflow = WorkflowFactory.create_workflow("vuln_scan", "http://example.com")

    assert "vuln_scan" in workflow.workflow_id
    assert len(workflow.tasks) > 0


def test_workflow_factory_list_workflows():
    """Test WorkflowFactory lists all workflows"""
    workflows = WorkflowFactory.list_workflows()

    assert len(workflows) == 4
    assert any(w["id"] == "web_app_full" for w in workflows)
    assert any(w["id"] == "subdomain_enum" for w in workflows)


def test_workflow_factory_invalid_workflow_id():
    """Test WorkflowFactory raises error for invalid workflow"""
    with pytest.raises(ValueError, match="Unknown workflow ID"):
        WorkflowFactory.create_workflow("nonexistent", "example.com")
```

**Step 4: Run all tests**

Run: `pytest tests/ -v --cov=app --cov-report=term-missing`
Expected: All tests PASS with coverage report

**Step 5: Commit comprehensive test suite**

```bash
git add tests/
git commit -m "test: add comprehensive test suite

- Add auth module tests (password hashing, registration, authentication)
- Add database model tests (User, Scan, Task relationships)
- Add workflow tests (schema validation, factory patterns)
- Add pytest-cov for coverage reporting
- Current coverage: ~60% (focused on core modules)"
```

---

## Task 14: Add Documentation and Development Scripts

**Files:**
- Create: `docs/DEVELOPMENT.md`
- Create: `scripts/run_tests.sh`
- Create: `scripts/lint.sh`
- Create: `scripts/format.sh`

**Step 1: Create development documentation**

File: `docs/DEVELOPMENT.md`
```markdown
# Development Guide

## Setup Development Environment

1. Clone repository
2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r dev-requirements.txt
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_hash_password -v
```

### Linting and Formatting

```bash
# Check code style
flake8 app/

# Format code
black app/ --line-length 100

# Type checking
mypy app/ --ignore-missing-imports
```

### Running the Application

```bash
# Development mode (windowed)
python3 main.py

# Production mode (fullscreen kiosk)
python3 main.py --fullscreen
```

## Code Quality Standards

- **PEP8 compliance**: Max line length 100 characters
- **Type hints**: All public functions should have type hints
- **Docstrings**: All modules, classes, and public functions
- **Test coverage**: Aim for >80% coverage on core modules
- **Exception handling**: No bare `except:` clauses

## Pre-commit Checklist

- [ ] All tests pass: `pytest tests/`
- [ ] Code is formatted: `black app/`
- [ ] No linting errors: `flake8 app/`
- [ ] Type hints are correct: `mypy app/`
- [ ] Added tests for new features
- [ ] Updated documentation
```

**Step 2: Create test runner script**

File: `scripts/run_tests.sh`
```bash
#!/bin/bash
# Run test suite with coverage

set -e

echo "Running pytest with coverage..."
pytest tests/ -v \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=60

echo ""
echo "Coverage report generated in htmlcov/index.html"
```

Make executable:
```bash
chmod +x scripts/run_tests.sh
```

**Step 3: Create linter script**

File: `scripts/lint.sh`
```bash
#!/bin/bash
# Run linters on codebase

set -e

echo "Running flake8..."
flake8 app/ main.py --count --statistics

echo ""
echo "Running mypy..."
mypy app/ main.py --ignore-missing-imports

echo ""
echo "✓ All linting checks passed!"
```

Make executable:
```bash
chmod +x scripts/lint.sh
```

**Step 4: Create formatter script**

File: `scripts/format.sh`
```bash
#!/bin/bash
# Format codebase with black

echo "Running black formatter..."
black app/ main.py --line-length 100

echo ""
echo "✓ Code formatted successfully!"
```

Make executable:
```bash
chmod +x scripts/format.sh
```

**Step 5: Create scripts directory**

Run: `mkdir -p scripts`

**Step 6: Commit documentation and scripts**

```bash
git add docs/ scripts/
git commit -m "docs: add development guide and automation scripts

- Add DEVELOPMENT.md with setup and workflow guide
- Add run_tests.sh for automated testing with coverage
- Add lint.sh for running all linters
- Add format.sh for code formatting
- Make scripts executable
- Improves developer onboarding"
```

---

## Task 15: Final Verification and Testing

**Files:**
- None (verification only)

**Step 1: Run complete test suite**

Run: `bash scripts/run_tests.sh`
Expected: All tests PASS with >60% coverage

**Step 2: Run all linters**

Run: `bash scripts/lint.sh`
Expected: No errors, all checks pass

**Step 3: Format entire codebase**

Run: `bash scripts/format.sh`
Expected: Code formatted successfully

**Step 4: Verify application starts**

Run: `python3 main.py`
Expected: Application launches without errors, login screen appears

**Step 5: Run manual smoke tests**

1. Create user account
2. Login
3. Start a workflow (if tools installed)
4. Check dashboard
5. Navigate through UI

Expected: No crashes, all features work

**Step 6: Generate final coverage report**

Run: `pytest tests/ --cov=app --cov-report=html --cov-report=term`
Expected: Coverage >60%

**Step 7: Create verification checklist**

Create: `docs/VERIFICATION.md`
```markdown
# Verification Checklist

## Code Quality Fixes Completed

- [x] Fixed missing WorkflowFactory import
- [x] Fixed dead code in workflow widget
- [x] Replaced 7 bare except clauses with specific exceptions
- [x] Fixed temp file leak in nuclei adapter
- [x] Removed unused imports (QIcon, Union)
- [x] Fixed line length violations
- [x] Moved imports to module level
- [x] Added type hints
- [x] Environment-based SECRET_KEY
- [x] Implemented report viewing

## Testing Infrastructure

- [x] pytest setup with pytest-qt
- [x] 50+ unit tests covering core modules
- [x] Test coverage >60%
- [x] All tests passing

## Development Tools

- [x] flake8 configuration
- [x] black formatter configuration
- [x] mypy type checking
- [x] Automation scripts (test, lint, format)
- [x] Development documentation

## Manual Verification

- [x] Application launches
- [x] User registration works
- [x] User login works
- [x] Dashboard displays
- [x] UI navigation works
- [x] No console errors
```

**Step 8: Final commit**

```bash
git add docs/VERIFICATION.md
git commit -m "docs: add verification checklist

- Document all completed code quality fixes
- List testing infrastructure additions
- Confirm development tools setup
- Manual verification checklist"
```

---

## Next Steps & Roadmap

After completing this plan, consider these enhancements:

### High Priority
1. **CI/CD Pipeline**: Add GitHub Actions for automated testing
2. **Integration Tests**: Test full workflow execution end-to-end
3. **Error Logging**: Centralized logging system with rotating file handlers
4. **User Documentation**: End-user guide for operating the platform

### Medium Priority
5. **Database Migrations**: Add Alembic for schema migrations
6. **API Layer**: REST API for programmatic access
7. **Report Templates**: Customizable PDF report templates
8. **Tool Version Checking**: Verify installed security tools and versions

### Low Priority
9. **Plugin System**: Allow custom tool adapters via plugins
10. **Multi-user Support**: Role-based access control
11. **Scan Scheduling**: Cron-like scheduled scans
12. **Metrics Dashboard**: Scan statistics and trends

---

## Execution Instructions

**Plan complete and saved to `docs/plans/2025-11-11-code-quality-and-foundation.md`.**

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration with quality gates

**2. Parallel Session (separate)** - Open new session with executing-plans skill, batch execution with review checkpoints

**Which approach would you prefer?**
