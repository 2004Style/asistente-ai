"""
Unit tests for host detection and platform adapters.
"""
from host.detector import detect_system
from host.profile import get_current_profile, HostProfile
from host.registry import get_host_adapter
from host.adapters.base import BaseHostAdapter

def test_host_detection():
    sys_info = detect_system()
    assert "os" in sys_info
    assert "distro" in sys_info
    assert "desktop" in sys_info

def test_host_profile():
    profile = get_current_profile()
    assert isinstance(profile, HostProfile)
    assert len(profile.username) > 0
    assert len(profile.home_dir) > 0

def test_host_adapter_registry():
    adapter = get_host_adapter()
    assert isinstance(adapter, BaseHostAdapter)
    
    # Check basic lists return lists of elements
    windows = adapter.list_windows()
    assert isinstance(windows, list)
    
    apps = adapter.list_apps()
    assert isinstance(apps, list)
    
    workspaces = adapter.list_workspaces()
    assert isinstance(workspaces, list)
