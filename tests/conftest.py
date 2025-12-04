"""Shared test fixtures for OpenCode tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_project_path() -> str:
    """Return a sample project path for testing."""
    return "/test/project"


@pytest.fixture
def sample_session_id() -> str:
    """Return a sample session ID for testing."""
    return "session-abc123"
