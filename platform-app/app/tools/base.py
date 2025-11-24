"""
Base tool interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import subprocess
import time
import json

from app.core.logging_config import get_tool_logger

class ToolCategory(Enum):
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"

@dataclass
class ToolMetadata:
    """Metadata about a security tool"""
    name: str
    category: ToolCategory
    description: str
    executable: str
    requires_root: bool = False
    default_timeout: int = 300
    supports_parallel: bool = True

class BaseTool(ABC):
    """Abstract base class for all security tools"""
    
    def __init__(self):
        self.metadata = self.get_metadata()
    
    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """Return tool metadata"""
        pass
    
    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        pass
    
    @abstractmethod
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """Build the command to execute"""
        pass
    
    @abstractmethod
    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse tool output into structured data"""
        pass
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool and return parsed results"""
        logger = get_tool_logger(self.metadata.name)

        logger.info(f"Executing tool: {self.metadata.name}")
        logger.debug(f"Tool parameters: {params}")

        # Validate parameters
        if not self.validate_parameters(params):
            logger.error("Parameter validation failed")
            return {
                "success": False,
                "error": "Invalid parameters",
                "data": {}
            }

        # Build command
        command = self.build_command(params)
        timeout = params.get('timeout', self.metadata.default_timeout)

        logger.info(f"Command: {' '.join(command)}")
        logger.debug(f"Timeout: {timeout}s")

        # Execute
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            execution_time = time.time() - start_time

            logger.info(f"Tool completed in {execution_time:.2f}s - Return code: {result.returncode}")

            if result.stdout:
                logger.debug(f"STDOUT length: {len(result.stdout)} characters")
            if result.stderr:
                logger.debug(f"STDERR length: {len(result.stderr)} characters")
                # Log first 500 chars of stderr for debugging
                if len(result.stderr) > 0:
                    logger.debug(f"STDERR preview: {result.stderr[:500]}")

            # Parse output
            parsed_data = self.parse_output(result.stdout, result.stderr, result.returncode)
            logger.debug(f"Parsed data keys: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'non-dict'}")

            return {
                "success": result.returncode == 0,
                "data": parsed_data,
                "raw_output": result.stdout,
                "errors": result.stderr,
                "execution_time": execution_time,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution timed out after {timeout} seconds"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "data": {},
                "execution_time": execution_time
            }
        except FileNotFoundError as e:
            execution_time = time.time() - start_time
            error_msg = (
                f"Tool '{self.metadata.executable}' not found. "
                f"Please ensure {self.metadata.name} is installed and available in PATH. "
                f"Command attempted: {' '.join(command)}"
            )
            logger.error(f"Tool not found: {self.metadata.executable}")
            logger.error(f"Full error: {e}")
            logger.error(f"Hint: Install {self.metadata.name} or add it to your system PATH")
            return {
                "success": False,
                "error": error_msg,
                "data": {},
                "execution_time": execution_time,
                "tool_missing": True  # Flag to indicate tool is not installed
            }
        except Exception as e:
            execution_time = time.time() - start_time
            logger.exception(f"Tool execution failed with exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {},
                "execution_time": execution_time
            }