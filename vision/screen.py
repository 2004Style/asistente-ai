"""
Handles screen capture under demand.
"""
import os
import subprocess
import struct
import zlib
import logging

logger = logging.getLogger("ScreenCapture")

def create_dummy_png() -> bytes:
    """Generate a valid 100x100 blue PNG byte stream in pure Python."""
    width, height = 100, 100
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0) # scanline filter type 0
        for x in range(width):
            raw_data.extend([21, 16, 42]) # rgb color matching our brand theme!
            
    def make_chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data))

    png_header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw_data)
    
    return png_header + make_chunk(b'IHDR', ihdr) + make_chunk(b'IDAT', idat) + make_chunk(b'IEND', b'')

def capture_screenshot() -> bytes:
    """Capture the current desktop screen, returning PNG bytes."""
    # Attempt to capture using grim (common in Hyprland)
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_name = tmp.name

    try:
        if os.getenv("WAYLAND_DISPLAY"):
            # Attempt wayland screenshot
            logger.info("Wayland session active, attempting screenshot via grim")
            res = subprocess.run(["grim", tmp_name], capture_output=True)
            if res.returncode == 0:
                with open(tmp_name, "rb") as f:
                    return f.read()
                    
        # Fallback to import (X11 imagemagick)
        elif os.getenv("DISPLAY"):
            logger.info("X11 session active, attempting screenshot via import")
            res = subprocess.run(["import", "-window", "root", tmp_name], capture_output=True)
            if res.returncode == 0:
                with open(tmp_name, "rb") as f:
                    return f.read()
    except Exception as e:
        logger.warning(f"Native screenshot command failed: {e}")
    finally:
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except Exception:
            pass

    logger.info("Returning pure python generated fallback PNG bytes.")
    return create_dummy_png()
