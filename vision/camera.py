"""
Handles camera image capture under demand.
"""
import os
import struct
import zlib
import logging

logger = logging.getLogger("CameraCapture")

def create_dummy_camera_png() -> bytes:
    """Generate a valid 100x100 red PNG byte stream in pure Python representing camera fallback."""
    width, height = 100, 100
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0) # scanline filter type 0
        for x in range(width):
            raw_data.extend([239, 68, 68]) # red camera indicator!
            
    def make_chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data))

    png_header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw_data)
    
    return png_header + make_chunk(b'IHDR', ihdr) + make_chunk(b'IDAT', idat) + make_chunk(b'IEND', b'')

def capture_camera() -> bytes:
    """Capture an image frame from the primary webcam or use cached web frame if available."""
    import time
    try:
        # Check if there is a fresh frame uploaded from the HUD web client
        from runtime import daemon
        now = time.time()
        if daemon._latest_web_camera_frame is not None and (now - daemon._latest_web_camera_time < 15.0):
            logger.info("Using recent camera frame uploaded from HUD frontend.")
            return daemon._latest_web_camera_frame
    except Exception as e:
        logger.warning(f"Could not read cached web camera frame: {e}")

    try:
        import cv2
        logger.info("OpenCV available, attempting to capture from webcam index 0")
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                # Encode frame to png bytes
                success, encoded_image = cv2.imencode('.png', frame)
                if success:
                    return encoded_image.tobytes()
        else:
            logger.warning("Failed to open camera index 0.")
    except ImportError:
        logger.warning("cv2 (OpenCV) is not installed. Running in mock camera mode.")
    except Exception as e:
        logger.error(f"Error capturing camera: {e}")

    logger.info("Returning pure python generated mock camera PNG.")
    return create_dummy_camera_png()
