"""
Centralized logging configuration for the Offensive Security Platform
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.core.config import settings


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds workflow/task context to log records"""

    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})

    def process(self, msg, kwargs):
        """Add context to log message"""
        # Merge extra context
        if 'extra' in kwargs:
            kwargs['extra'] = {**self.extra, **kwargs['extra']}
        else:
            kwargs['extra'] = self.extra
        return msg, kwargs


class LoggingConfig:
    """Centralized logging configuration"""

    # Log format with context fields
    DETAILED_FORMAT = (
        '%(asctime)s | %(levelname)-8s | %(name)s | '
        '[scan:%(scan_id)s task:%(task_id)s tool:%(tool)s] | '
        '%(message)s'
    )

    SIMPLE_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'

    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    @staticmethod
    def setup_logging(level: int = logging.INFO):
        """
        Configure application-wide logging

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Create formatters
        detailed_formatter = logging.Formatter(
            LoggingConfig.DETAILED_FORMAT,
            datefmt=LoggingConfig.DATE_FORMAT,
            defaults={
                'scan_id': 'N/A',
                'task_id': 'N/A',
                'tool': 'N/A'
            }
        )

        simple_formatter = logging.Formatter(
            LoggingConfig.SIMPLE_FORMAT,
            datefmt=LoggingConfig.DATE_FORMAT
        )

        # Ensure logs directory exists
        settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Console handler (simple format)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

        # Platform log file (rotating, 10MB max, keep 5 backups)
        platform_log = settings.LOGS_DIR / "platform.log"
        platform_handler = logging.handlers.RotatingFileHandler(
            platform_log,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        platform_handler.setLevel(level)
        platform_handler.setFormatter(simple_formatter)
        root_logger.addHandler(platform_handler)

        # Workflow-specific log file (detailed format with context)
        workflow_log = settings.LOGS_DIR / "workflows.log"
        workflow_handler = logging.handlers.RotatingFileHandler(
            workflow_log,
            maxBytes=20 * 1024 * 1024,  # 20 MB
            backupCount=10,
            encoding='utf-8'
        )
        workflow_handler.setLevel(logging.DEBUG)
        workflow_handler.setFormatter(detailed_formatter)
        workflow_handler.addFilter(lambda record: hasattr(record, 'scan_id'))
        root_logger.addHandler(workflow_handler)

        # Tool execution log file
        tools_log = settings.LOGS_DIR / "tools.log"
        tools_handler = logging.handlers.RotatingFileHandler(
            tools_log,
            maxBytes=20 * 1024 * 1024,  # 20 MB
            backupCount=10,
            encoding='utf-8'
        )
        tools_handler.setLevel(logging.DEBUG)
        tools_handler.setFormatter(detailed_formatter)
        tools_handler.addFilter(lambda record: getattr(record, 'tool', 'N/A') != 'N/A')
        root_logger.addHandler(tools_handler)

        # Log startup message
        logging.info(f"Logging initialized - Level: {logging.getLevelName(level)}")
        logging.info(f"Log directory: {settings.LOGS_DIR}")

    @staticmethod
    def get_logger(name: str, **context) -> ContextLogger:
        """
        Get a logger with optional context

        Args:
            name: Logger name (usually __name__)
            **context: Context fields (scan_id, task_id, tool, etc.)

        Returns:
            ContextLogger with attached context
        """
        logger = logging.getLogger(name)
        return ContextLogger(logger, extra=context)


def get_workflow_logger(
    scan_id: Optional[int] = None,
    task_id: Optional[str] = None,
    tool: Optional[str] = None
) -> ContextLogger:
    """
    Get a logger configured for workflow execution

    Args:
        scan_id: Database scan ID
        task_id: Workflow task ID
        tool: Tool name

    Returns:
        ContextLogger with workflow context
    """
    context = {
        'scan_id': scan_id or 'N/A',
        'task_id': task_id or 'N/A',
        'tool': tool or 'N/A'
    }
    return LoggingConfig.get_logger('workflows.engine', **context)


def get_tool_logger(tool_name: str, task_id: Optional[str] = None) -> ContextLogger:
    """
    Get a logger configured for tool execution

    Args:
        tool_name: Name of the security tool
        task_id: Optional task ID for context

    Returns:
        ContextLogger with tool context
    """
    context = {
        'scan_id': 'N/A',
        'task_id': task_id or 'N/A',
        'tool': tool_name
    }
    return LoggingConfig.get_logger(f'tools.{tool_name}', **context)
