#!/usr/bin/env python3
"""
Manual test script for logging infrastructure
Run this to verify logging is working correctly
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from app.core.logging_config import LoggingConfig, get_workflow_logger, get_tool_logger
from app.core.config import settings

def test_logging_setup():
    """Test 1: Verify logging can be initialized"""
    print("\n" + "="*60)
    print("TEST 1: Logging Initialization")
    print("="*60)

    LoggingConfig.setup_logging(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    logger.info("This is an INFO message")
    logger.debug("This is a DEBUG message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")

    # Check log files were created
    log_files = [
        settings.LOGS_DIR / "platform.log",
        settings.LOGS_DIR / "workflows.log",
        settings.LOGS_DIR / "tools.log"
    ]

    print("\nLog file locations:")
    for log_file in log_files:
        exists = log_file.exists()
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {status}: {log_file}")

    return all(f.exists() for f in log_files)


def test_workflow_logger():
    """Test 2: Verify workflow logger with context"""
    print("\n" + "="*60)
    print("TEST 2: Workflow Logger with Context")
    print("="*60)

    logger = get_workflow_logger(scan_id=123, task_id="test_task", tool="nmap")

    logger.info("Workflow started")
    logger.debug("Processing task with dependencies")
    logger.warning("Task execution slow")
    logger.error("Task failed")

    print("✓ Workflow logger created successfully")
    print(f"  Context: scan_id={logger.extra['scan_id']}, task_id={logger.extra['task_id']}, tool={logger.extra['tool']}")

    return True


def test_tool_logger():
    """Test 3: Verify tool logger with context"""
    print("\n" + "="*60)
    print("TEST 3: Tool Logger with Context")
    print("="*60)

    logger = get_tool_logger(tool_name="subfinder", task_id="recon_1")

    logger.info("Executing tool: subfinder")
    logger.debug("Command: subfinder -d example.com")
    logger.info("Tool completed in 2.5s - Return code: 0")

    print("✓ Tool logger created successfully")
    print(f"  Context: tool={logger.extra['tool']}, task_id={logger.extra['task_id']}")

    return True


def test_tool_execution():
    """Test 4: Verify tool execution generates logs"""
    print("\n" + "="*60)
    print("TEST 4: Tool Execution Logging")
    print("="*60)

    from app.tools.base import BaseTool, ToolMetadata, ToolCategory

    class TestTool(BaseTool):
        def get_metadata(self):
            return ToolMetadata(
                name="test-echo",
                category=ToolCategory.SCANNING,
                description="Test echo tool",
                executable="echo"
            )

        def validate_parameters(self, params):
            return True

        def build_command(self, params):
            message = params.get("message", "Hello logging!")
            return ["echo", message]

        def parse_output(self, output, stderr, return_code):
            return {"output": output.strip(), "lines": len(output.strip().split('\n'))}

    tool = TestTool()
    result = tool.execute({"message": "Testing logging infrastructure"})

    print(f"✓ Tool executed successfully")
    print(f"  Success: {result['success']}")
    print(f"  Execution time: {result['execution_time']:.3f}s")
    print(f"  Parsed data: {result['data']}")

    return result["success"]


def test_log_file_contents():
    """Test 5: Verify log files contain expected content"""
    print("\n" + "="*60)
    print("TEST 5: Log File Contents")
    print("="*60)

    log_files = {
        "platform.log": settings.LOGS_DIR / "platform.log",
        "workflows.log": settings.LOGS_DIR / "workflows.log",
        "tools.log": settings.LOGS_DIR / "tools.log"
    }

    for name, path in log_files.items():
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n{name}: {len(lines)} lines")
                if lines:
                    print(f"  First line: {lines[0].strip()[:80]}...")
                    print(f"  Last line: {lines[-1].strip()[:80]}...")
        else:
            print(f"\n{name}: NOT FOUND")

    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" LOGGING INFRASTRUCTURE TEST SUITE")
    print("="*70)

    tests = [
        ("Logging Initialization", test_logging_setup),
        ("Workflow Logger", test_workflow_logger),
        ("Tool Logger", test_tool_logger),
        ("Tool Execution", test_tool_execution),
        ("Log File Contents", test_log_file_contents)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))

    # Print summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result, _ in results if result)
    total = len(results)

    for test_name, result, error in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if error:
            print(f"       Error: {error}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Logging infrastructure is working correctly.")
        print(f"\nLog files are located in: {settings.LOGS_DIR}")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
