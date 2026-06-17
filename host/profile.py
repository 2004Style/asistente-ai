"""
Defines the host system profile data structure and runtime characteristics.
"""
import os
import getpass
from pydantic import BaseModel, Field
from host.detector import detect_system

class HostProfile(BaseModel):
    os: str
    distro: str
    desktop: str
    username: str = Field(default_factory=getpass.getuser)
    home_dir: str = Field(default_factory=lambda: os.path.expanduser("~"))

def get_current_profile() -> HostProfile:
    """Helper to detect and construct the current HostProfile."""
    sys_info = detect_system()
    return HostProfile(
        os=sys_info["os"],
        distro=sys_info["distro"],
        desktop=sys_info["desktop"]
    )
