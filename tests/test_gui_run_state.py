"""
Tests for gui/viewmodels/run_state.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from gui.viewmodels.run_state import RunState


def test_run_state_default_values():
    """Test default values."""
    state = RunState()
    
    assert state.status == "idle"
    assert state.phase == ""
    assert state.total_urls == 0
    assert state.processed == 0
    assert state.errors == 0
    assert state.candidates == 0
    assert state.elapsed_seconds == 0.0
    assert state.output_dir == ""
    assert state.stopped_early is False


def test_run_state_reset():
    """Test reset method."""
    state = RunState()
    state.status = "running"
    state.phase = "fetch"
    state.total_urls = 100
    state.processed = 50
    state.elapsed_seconds = 30.0
    state.output_dir = "outputs/test"
    state.stopped_early = True
    
    state.reset()
    
    assert state.status == "idle"
    assert state.phase == ""
    assert state.total_urls == 0
    assert state.processed == 0
    assert state.elapsed_seconds == 0.0
    assert state.output_dir == ""
    assert state.stopped_early is False


def test_run_state_is_running():
    """Test is_running method."""
    state = RunState()
    assert state.is_running() is False
    
    state.status = "running"
    assert state.is_running() is True


def test_run_state_is_idle():
    """Test is_idle method."""
    state = RunState()
    assert state.is_idle() is True
    
    state.status = "running"
    assert state.is_idle() is False


def test_run_state_progress_percent():
    """Test progress_percent calculation."""
    state = RunState()
    assert state.progress_percent() == 0.0
    
    state.total_urls = 100
    state.processed = 50
    assert state.progress_percent() == 50.0
    
    state.processed = 100
    assert state.progress_percent() == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
