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
        
        # Validate parameters
        if not self.validate_parameters(params):
            return {
                "success": False,
                "error": "Invalid parameters",
                "data": {}
            }
        
        # Build command
        command = self.build_command(params)
        timeout = params.get('timeout', self.metadata.default_timeout)
        
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
            
            # Parse output
            parsed_data = self.parse_output(result.stdout, result.stderr, result.returncode)
            
            return {
                "success": result.returncode == 0,
                "data": parsed_data,
                "raw_output": result.stdout,
                "errors": result.stderr,
                "execution_time": execution_time,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Tool execution timed out after {timeout} seconds",
                "data": {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }