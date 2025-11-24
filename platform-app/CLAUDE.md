# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Offensive Security Platform** - a PyQt5-based desktop application for executing security testing workflows. The platform runs in fullscreen kiosk mode and provides an automated interface for penetration testing tools.

**IMPORTANT SECURITY CONTEXT**: This is an authorized security testing platform designed for legitimate penetration testing, CTF competitions, and security research. All code analysis, debugging, and improvements should maintain the defensive security purpose of this tool.

## Architecture

### Application Structure

```
platform-app/
├── main.py                  # Application entry point
├── app/
│   ├── core/               # Core functionality
│   │   ├── auth.py         # User authentication (bcrypt + JWT)
│   │   ├── database.py     # SQLAlchemy models (User, Scan, Task)
│   │   └── config.py       # Application configuration
│   ├── gui/                # PyQt5 user interface
│   │   ├── main_window.py  # Main window with stacked widgets
│   │   ├── login_widget.py # Login/registration screen
│   │   ├── dashboard_widget.py  # Main dashboard
│   │   ├── workflow_widget.py   # Workflow execution UI
│   │   ├── terminal_widget.py   # Embedded terminal
│   │   └── report_widget.py     # Report viewing/generation
│   ├── tools/              # Security tool adapters
│   │   ├── base.py         # BaseTool abstract class
│   │   ├── registry.py     # ToolRegistry for tool management
│   │   └── adapters/       # Tool-specific adapters
│   │       ├── nmap_adapter.py
│   │       ├── subfinder_adapter.py
│   │       ├── nuclei_adapter.py
│   │       ├── httpx_adapter.py
│   │       ├── ffuf_adapter.py
│   │       ├── gobuster_adapter.py
│   │       ├── sqlmap_adapter.py
│   │       ├── amass_adapter.py
│   │       ├── testssl_adapter.py       # NEW
│   │       ├── wpscan_adapter.py        # NEW
│   │       └── metasploit_adapter.py    # NEW
│   └── workflows/          # Workflow execution engine
│       ├── engine.py       # WorkflowWorker (QThread-based)
│       ├── schemas.py      # Pydantic models for workflows
│       └── prebuilt/       # Pre-defined workflows
│           ├── port_scan.py
│           ├── subdomain_enum.py
│           ├── vuln_scan.py
│           └── web_app_scan.py
└── resources/
    ├── styles/             # QSS stylesheets (dark theme)
    └── icons/              # Application icons
```

### Key Design Patterns

1. **Tool Adapter Pattern**: All security tools inherit from `BaseTool` (app/tools/base.py) and implement:
   - `get_metadata()` - Returns tool metadata (name, category, executable)
   - `validate_parameters()` - Validates input parameters
   - `build_command()` - Builds the command to execute
   - `parse_output()` - Parses tool output into structured data
   - `execute()` - Executes the tool via subprocess

2. **Workflow Engine**: `WorkflowWorker` (app/workflows/engine.py) executes workflows as QThread workers:
   - Dependency resolution: Tasks run only after dependencies complete
   - Sequential execution: Tasks run one at a time (not parallel)
   - Parameter substitution: Tasks can reference outputs from previous tasks using `${task_id.field}` syntax
   - Database tracking: All scans and tasks are persisted to SQLite

3. **Workflow Schema**: Defined in `app/workflows/schemas.py` using Pydantic models:
   - `WorkflowDefinition` - Complete workflow with tasks, metadata, dependencies
   - `WorkflowTask` - Individual task with tool, parameters, dependencies, priority
   - `TaskResult` - Structured result from task execution
   - Includes validators for circular dependency detection and dependency validation

4. **Authentication**: JWT-based authentication with bcrypt password hashing (app/core/auth.py)
   - First boot creates initial user account
   - Session management via JWT tokens

5. **UI Navigation**: Main window uses QStackedWidget for view switching:
   - Login → Dashboard → Workflow/Terminal/Reports → Back to Dashboard

## Development Commands

### Running the Application

**Standard mode (windowed):**
```bash
python3 main.py
```

**Debug mode with verbose logging:**
```bash
python3 main.py --debug
```

**Fullscreen kiosk mode:**
```bash
python3 main.py --fullscreen
```

**Production startup script:**
```bash
bash start.sh
```
Note: start.sh runs in fullscreen with auto-restart on crash

**Check installed security tools:**
```bash
python check_tools.py
```
This verifies which security tools are installed and provides installation instructions for missing tools.

### Environment Setup

**Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Required environment variables:**
- `QT_QPA_PLATFORM=xcb` (for X11 display)
- `DISPLAY=:0` (X display)

### Database Management

The application uses SQLite with SQLAlchemy ORM. Database is auto-created at `data/platform.db` on first run.

**Schema:**
- `users` - User accounts (username, password_hash, created_at, last_login)
- `scans` - Workflow executions (user_id, workflow_name, target, status, results)
- `tasks` - Individual task executions (scan_id, task_name, tool, status, output, errors)

**Database initialization:**
```python
from app.core.database import init_database
init_database()  # Creates all tables
```

**Direct database access:**
```python
from app.core.database import SessionLocal
db = SessionLocal()
# ... perform queries
db.close()
```

## Newly Added Tools

The following tools were added in this implementation:

**TestSSL.sh** - SSL/TLS security testing
- Executable: `testssl.sh`
- Install: `git clone https://github.com/drwetter/testssl.sh.git && cd testssl.sh && sudo ln -s $PWD/testssl.sh /usr/local/bin/`
- Usage: Scan SSL/TLS configurations for vulnerabilities

**WPScan** - WordPress security scanner
- Executable: `wpscan`
- Install: `gem install wpscan` or `docker pull wpscanteam/wpscan`
- API Token: Register at https://wpscan.com/ for vulnerability data
- Usage: Enumerate WordPress plugins, themes, and vulnerabilities

**Metasploit Framework** - Exploitation framework
- Executable: `msfconsole`
- Install: `curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall && chmod 755 msfinstall && ./msfinstall`
- Usage: Run exploitation modules via resource scripts

## Adding New Security Tools

To add a new tool adapter:

1. Create adapter in `app/tools/adapters/your_tool_adapter.py`:
```python
from app.tools.base import BaseTool, ToolMetadata, ToolCategory

class YourToolAdapter(BaseTool):
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="your-tool",
            category=ToolCategory.SCANNING,
            description="Tool description",
            executable="tool-binary-name",
            default_timeout=300
        )

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        # Validate required parameters
        return "target" in params

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        # Build command array
        return ["tool-binary", "-target", params["target"]]

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        # Parse tool output into structured data
        return {"findings": [...]}
```

2. Register in `app/tools/registry.py`:
```python
from app.tools.adapters.your_tool_adapter import YourToolAdapter

class ToolRegistry:
    def _register_tools(self):
        # ... existing registrations
        self.register("your-tool", YourToolAdapter)
```

## Creating Workflows

Workflows are defined using Pydantic schemas. Example:

```python
from app.workflows.schemas import WorkflowDefinition, WorkflowTask

workflow = WorkflowDefinition(
    workflow_id="custom_scan",
    name="Custom Security Scan",
    target="example.com",
    tasks=[
        WorkflowTask(
            task_id="recon",
            name="Subdomain Enumeration",
            tool="subfinder",
            parameters={"domain": "example.com"},
            priority=10
        ),
        WorkflowTask(
            task_id="scan",
            name="Port Scan",
            tool="nmap",
            parameters={"hosts": "${recon.subdomains}"},  # Reference previous task output
            depends_on=["recon"],  # Runs after recon completes
            priority=5
        )
    ]
)
```

**Key workflow concepts:**
- Tasks execute sequentially (one at a time)
- Dependencies are specified via `depends_on` list of task IDs
- Parameter substitution: `${task_id.field}` references previous task outputs
- Priority determines execution order when multiple tasks are ready
- Workflow engine validates dependencies and detects circular references

## Debugging Workflows

**Inspecting workflow definitions:**
```python
from app.workflows.prebuilt import WorkflowFactory
workflows = WorkflowFactory.list_workflows()
workflow = WorkflowFactory.create_workflow("web_app_full", "example.com")
print(workflow.dict())  # View full workflow structure
```

**Checking tool registry:**
```python
from app.tools.registry import ToolRegistry
registry = ToolRegistry()
tools = registry.list_tools()  # List all available tools
tool = registry.get_tool("nmap")  # Get specific tool instance
```

**Manual tool execution:**
```python
from app.tools.registry import ToolRegistry
registry = ToolRegistry()
nmap = registry.get_tool("nmap")
result = nmap.execute({"target": "scanme.nmap.org", "scan_type": "quick"})
print(result)  # {'success': True/False, 'data': {...}, 'raw_output': '...'}
```

## Logging System

The platform has comprehensive structured logging for debugging and monitoring.

**Log Files** (stored in `data/logs/`):
- `platform.log` - General application logs (startup, shutdown, database)
- `workflows.log` - Detailed workflow execution with scan/task/tool context
- `tools.log` - Tool-specific execution logs (commands, output, timing)

**Viewing Logs:**
```bash
# View recent workflow execution
tail -f data/logs/workflows.log

# View tool execution details
tail -f data/logs/tools.log

# Search for errors
grep "ERROR" data/logs/*.log
```

**Using Logging in Code:**
```python
# Basic logger
import logging
logger = logging.getLogger(__name__)
logger.info("Something happened")

# Workflow logger with context (includes scan_id, task_id, tool in output)
from app.core.logging_config import get_workflow_logger
logger = get_workflow_logger(scan_id=123, task_id="recon_1", tool="nmap")
logger.info("Task started")  # Automatically includes context

# Tool logger
from app.core.logging_config import get_tool_logger
logger = get_tool_logger(tool_name="subfinder", task_id="recon_1")
logger.info("Executing subfinder")
```

See `docs/LOGGING.md` for detailed logging documentation.

## Testing

Currently no automated test suite. Testing workflow:

1. Run application in windowed mode: `python3 main.py`
2. Create test user account
3. Execute prebuilt workflows from dashboard
4. Verify task execution in workflow widget
5. Check scan results in database: `data/platform.db`
6. Review logs in `data/logs/workflows.log` for execution trace

**Querying scan results:**
```bash
sqlite3 data/platform.db "SELECT * FROM scans ORDER BY started_at DESC LIMIT 5;"
sqlite3 data/platform.db "SELECT * FROM tasks WHERE scan_id=1;"
```

## Kiosk Mode Features

When running with `--fullscreen`:
- Frameless window with no window decorations
- Stays on top of all windows
- Cursor hidden initially (shown after login)
- Alt+F4 disabled (closeEvent ignored)
- Emergency exit: **Ctrl+Alt+Q** (requires double confirmation)

## Important Security Notes

- Default SECRET_KEY in config.py should be changed in production
- Database contains password hashes (bcrypt) - never plain text
- JWT tokens expire after 24 hours (configurable)
- All tool execution happens via subprocess with timeout limits
- First boot requires account creation (no users exist)

## Dependencies

Key Python packages:
- PyQt5 5.15.10 - GUI framework
- SQLAlchemy 2.0.25 - ORM for database
- bcrypt 4.1.2 - Password hashing
- PyJWT 2.8.0 - JWT token management
- Pydantic 2.5.3 - Data validation and schemas
- reportlab 4.0.9 - PDF report generation
- jinja2 3.1.3 - Template rendering
- markdown 3.5.2 - Markdown processing

## Common Issues

1. **QT platform errors**: Ensure `QT_QPA_PLATFORM=xcb` and `DISPLAY=:0` are set
2. **Tool not found errors**:
   - Run `python check_tools.py` to see which tools are installed
   - See `docs/REQUIRED_TOOLS.md` for installation instructions
   - Verify security tools are installed and in PATH
3. **Database locked**: Only one application instance should run at a time
4. **Exit disabled in fullscreen**: Use Ctrl+Alt+Q emergency exit shortcut
5. **Import errors**: Ensure you're running from the project root (`platform-app/`) as `main.py` adds `app/` to the Python path
6. **Workflow debugging**:
   - Run with `--debug` flag for verbose logging
   - Check `data/logs/workflows.log` for detailed task execution trace
   - Check `data/logs/tools.log` for actual commands executed and their output
   - Look for parameter substitution failures or dependency issues in logs

## Code Architecture Notes

**Workflow execution is single-threaded**: The `WorkflowWorker` executes tasks sequentially, NOT in parallel. Even if multiple tasks are ready, only the highest priority task runs at a time. This is by design to avoid overwhelming the system with concurrent scans.

**Parameter substitution mechanism**: In `WorkflowWorker._substitute_parameters()`, tasks can reference previous task outputs using `${task_id.field.nested}` syntax. The engine navigates the output dictionary path to extract the referenced value.

**Tool execution timeout**: All tools inherit a default 300-second timeout from `BaseTool.execute()`. Individual tools can override this via `ToolMetadata.default_timeout` or per-execution via the `timeout` parameter.

**QThread pattern for long operations**: The `WorkflowWorker` runs in a separate QThread to keep the UI responsive. It emits signals (`task_started`, `task_completed`, `progress_updated`) that the GUI widgets connect to for real-time updates.

**Structured logging architecture**: The platform uses a three-tier logging system (`app/core/logging_config.py`):
- `platform.log` uses simple format for general application events
- `workflows.log` uses detailed format with context fields (scan_id, task_id, tool) for workflow execution tracing
- `tools.log` captures all tool execution details including commands, timing, and output
- Loggers created via `get_workflow_logger()` and `get_tool_logger()` automatically inject context into log records
- Log rotation: platform (10MB/5 backups), workflows (20MB/10 backups), tools (20MB/10 backups)

**Available prebuilt workflows:**
- `web_app_full` - Complete web application assessment (subdomain enum → port scan → httpx → nuclei → ffuf → sqlmap)
- `subdomain_enum` - Subdomain discovery using subfinder and amass
- `port_scan` - Nmap-based port and service detection
- `vuln_scan` - Nuclei vulnerability scanning
