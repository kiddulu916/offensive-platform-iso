# Logging Infrastructure

This document describes the logging system implemented for the Offensive Security Platform.

## Overview

The platform now has comprehensive structured logging that traces:
- Workflow execution lifecycle
- Task dependency resolution and execution
- Tool command execution and results
- Parameter substitution
- Errors and exceptions at all levels

## Quick Start

### Running with Logging

**Standard mode with INFO level:**
```bash
python main.py
```

**Debug mode with DEBUG level (verbose):**
```bash
python main.py --debug
```

### Log Files

All logs are stored in `data/logs/`:

- **platform.log** - General application logs (startup, shutdown, database operations)
- **workflows.log** - Detailed workflow execution trace with scan_id/task_id/tool context
- **tools.log** - Tool-specific execution logs (commands, stdout/stderr, return codes)

**Log Rotation:**
- Platform logs: 10 MB max, 5 backups
- Workflow logs: 20 MB max, 10 backups
- Tool logs: 20 MB max, 10 backups

## Log Format

### Platform Logs (Simple Format)
```
2025-11-18 14:23:45 | INFO     | __main__ | Starting Offensive Security Platform
2025-11-18 14:23:45 | INFO     | __main__ | Database initialized successfully
```

### Workflow/Tool Logs (Detailed Format with Context)
```
2025-11-18 14:25:12 | INFO     | workflows.engine | [scan:5 task:recon_subdomains tool:subfinder] | Starting task: Subdomain Enumeration
2025-11-18 14:25:12 | DEBUG    | workflows.engine | [scan:5 task:recon_subdomains tool:subfinder] | Raw parameters: {'domain': 'example.com'}
2025-11-18 14:25:12 | INFO     | tools.subfinder  | [scan:N/A task:N/A tool:subfinder] | Command: subfinder -d example.com -o output.txt
2025-11-18 14:25:15 | INFO     | tools.subfinder  | [scan:N/A task:N/A tool:subfinder] | Tool completed in 2.84s - Return code: 0
```

## What Gets Logged

### Workflow Engine (app/workflows/engine.py)

**Workflow Level:**
- Workflow initialization (name, target, total tasks)
- Scan record creation (scan_id)
- Workflow start/completion/cancellation
- Final summary (tasks completed/failed)
- Exceptions and errors

**Task Execution:**
- Task selection based on dependencies and priority
- Task start/completion/failure
- Dependencies satisfied/blocked
- Progress updates

**Parameter Substitution:**
- Reference resolution (`${task_id.field}`)
- Substitution success/failure
- Missing paths or task results

### Tool Execution (app/tools/base.py)

**Every Tool Execution:**
- Tool name and parameters
- Command being executed
- Timeout setting
- Execution duration
- Return code
- STDOUT/STDERR lengths
- STDERR preview (first 500 chars)
- Parsed data structure
- Timeouts and exceptions

### Application Lifecycle (main.py)

- Application startup
- Python version
- Command-line arguments
- Database initialization
- Application exit code

## Using Logging in New Code

### Get a Basic Logger
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Something happened")
logger.debug("Detailed information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.exception("Exception with traceback")  # Use in except blocks
```

### Get a Workflow Logger with Context
```python
from app.core.logging_config import get_workflow_logger

logger = get_workflow_logger(
    scan_id=123,
    task_id="recon_1",
    tool="nmap"
)
logger.info("Task started")  # Will include scan:123 task:recon_1 tool:nmap in log
```

### Get a Tool Logger with Context
```python
from app.core.logging_config import get_tool_logger

logger = get_tool_logger(tool_name="subfinder", task_id="recon_1")
logger.info("Executing subfinder")  # Will include tool:subfinder in log
```

## Testing the Logging System

### Option 1: Run Manual Test Script

```bash
# Install dependencies first
pip install -r requirements.txt

# Run the test script
python test_logging_manual.py
```

This will:
1. Initialize the logging system
2. Create test loggers with context
3. Execute a test tool (echo command)
4. Verify log files were created
5. Display log file contents

### Option 2: Run the Application

```bash
# Run in debug mode to see all logs in console
python main.py --debug

# Or run normally (INFO level)
python main.py
```

Then:
1. Create/login to user account
2. Execute any workflow from the dashboard
3. Check `data/logs/workflows.log` for detailed execution trace

### Option 3: Check Existing Logs

If you've already run the application:
```bash
# View most recent platform logs
tail -n 50 data/logs/platform.log

# View workflow execution trace
tail -n 100 data/logs/workflows.log

# View tool execution logs
tail -n 100 data/logs/tools.log

# Search for errors
grep "ERROR" data/logs/*.log
grep "EXCEPTION" data/logs/*.log
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (parameter values, substitution details, data structures)
- **INFO**: Confirmation that things are working as expected (task started, tool completed)
- **WARNING**: Indication of potential issues (parameter substitution failed, dependencies blocked)
- **ERROR**: Errors that prevented task completion
- **CRITICAL**: Severe errors that might crash the application

**Default Level:** INFO
**Debug Mode:** DEBUG (use `--debug` flag)

## Debugging Workflows with Logs

### Example: Task Failed

Look for the task in workflows.log:
```
2025-11-18 14:25:12 | INFO  | [scan:5 task:port_scan tool:nmap] | Starting task: Port Scan
2025-11-18 14:25:12 | DEBUG | [scan:5 task:port_scan tool:nmap] | Raw parameters: {'hosts': '${recon.subdomains}'}
2025-11-18 14:25:12 | DEBUG | [scan:5 task:port_scan tool:nmap] | Parameter substitution: hosts -> recon.subdomains
2025-11-18 14:25:12 | DEBUG | [scan:5 task:port_scan tool:nmap] | Substituted parameters: {'hosts': ['sub1.example.com', 'sub2.example.com']}
2025-11-18 14:25:12 | INFO  | [scan:5 task:port_scan tool:nmap] | Executing tool: nmap
```

Then check tools.log for the actual command:
```
2025-11-18 14:25:12 | INFO  | tools.nmap | Command: nmap -sV -Pn sub1.example.com sub2.example.com
2025-11-18 14:25:45 | INFO  | tools.nmap | Tool completed in 32.8s - Return code: 0
```

### Example: Parameter Substitution Failed

```
2025-11-18 14:25:12 | WARNING | [scan:5 task:scan tool:nmap] | Parameter substitution failed: path 'recon.subdomains' not found in task recon output
2025-11-18 14:25:12 | DEBUG   | [scan:5 task:scan tool:nmap] | Substituted hosts with empty list (path not found)
```

This tells you:
1. Which task tried to reference another task's output
2. What path it was looking for
3. That it defaulted to an empty list

### Example: Dependency Issues

```
2025-11-18 14:25:30 | ERROR | [scan:5 task:N/A tool:N/A] | Workflow blocked: 3 tasks cannot run due to failed dependencies
2025-11-18 14:25:30 | WARNING | [scan:5 task:nuclei tool:nuclei] | Skipping task nuclei_scan (Vulnerability Scan) - dependencies failed
```

## Configuration

Logging configuration is in `app/core/logging_config.py`.

**Key Settings:**
- Log directory: `settings.LOGS_DIR` (default: `data/logs/`)
- Log levels: Configurable via `LoggingConfig.setup_logging(level=...)`
- File sizes: Configured in `RotatingFileHandler` settings
- Format strings: `DETAILED_FORMAT` and `SIMPLE_FORMAT`

## Troubleshooting

### Logs not being created
- Check that `data/logs/` directory exists and is writable
- Verify `LoggingConfig.setup_logging()` is called in `main.py`
- Check for import errors

### Missing context in logs
- Ensure you're using `get_workflow_logger()` or `get_tool_logger()` instead of `logging.getLogger()`
- Verify you're passing the correct scan_id, task_id, and tool parameters

### Logs too verbose
- Run without `--debug` flag for INFO level
- Filter logs: `grep -v DEBUG data/logs/workflows.log`

### Logs too sparse
- Run with `--debug` flag
- Check that logger.debug() calls are present in the code

## Next Steps

With logging in place, you can now:

1. **Run Real Workflows**: Execute actual pentesting workflows against test targets
2. **Diagnose Issues**: Use logs to trace exactly what happened when tasks fail
3. **Performance Analysis**: Check execution times in logs to identify slow tools
4. **Error Patterns**: Grep logs for common errors to identify systemic issues
5. **Add More Instrumentation**: Add logging to GUI components, database operations, etc.

## Example Workflow Execution Log

Here's what a complete workflow execution looks like in the logs:

```
# Platform initialization
2025-11-18 14:23:45 | INFO | __main__ | Starting Offensive Security Platform
2025-11-18 14:23:45 | INFO | __main__ | Database initialized successfully

# Workflow start
2025-11-18 14:25:10 | INFO | workflows.engine | [scan:N/A task:N/A tool:N/A] | Initializing workflow: Subdomain Enumeration
2025-11-18 14:25:10 | INFO | workflows.engine | [scan:N/A task:N/A tool:N/A] | Target: example.com
2025-11-18 14:25:10 | INFO | workflows.engine | [scan:5 task:N/A tool:N/A] | Scan record created: scan_id=5

# Task execution
2025-11-18 14:25:10 | INFO | workflows.engine | [scan:5 task:subfinder tool:subfinder] | Selected task for execution: subfinder_scan
2025-11-18 14:25:10 | INFO | workflows.engine | [scan:5 task:subfinder tool:subfinder] | Starting task: Subfinder Scan
2025-11-18 14:25:10 | INFO | tools.subfinder | Command: subfinder -d example.com -silent
2025-11-18 14:25:15 | INFO | tools.subfinder | Tool completed in 4.82s - Return code: 0
2025-11-18 14:25:15 | INFO | workflows.engine | [scan:5 task:subfinder tool:subfinder] | Task subfinder completed successfully

# Workflow completion
2025-11-18 14:25:15 | INFO | workflows.engine | [scan:5 task:N/A tool:N/A] | Workflow execution completed in 5.23s
2025-11-18 14:25:15 | INFO | workflows.engine | [scan:5 task:N/A tool:N/A] | Workflow summary: 1 completed, 0 failed
```
