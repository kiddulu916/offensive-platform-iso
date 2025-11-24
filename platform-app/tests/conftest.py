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
