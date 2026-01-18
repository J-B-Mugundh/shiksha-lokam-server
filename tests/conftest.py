"""
Pytest configuration and shared fixtures
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session")
def test_config():
    """Global test configuration"""
    return {
        "api_url": "http://localhost:8000",
        "timeout": 10,
        "verbose": True
    }