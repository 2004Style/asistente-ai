"""
Orchestrates vision tasks with GPU memory management and frame rate throttling.

Designed for RTX 3050 (4-8GB VRAM) or similar systems:
- YOLOv8 stays loaded (lightweight)
- CLIP loads/unloads on demand (lazy loading)
- Frame skipping caps analysis to 3-5 FPS per source
- FP16 precision reduces VRAM by ~50%
"""
import time
import asyncio
import logging
import gc
from typing import Dict, Any, Optional, List
from vision.screen import capture_screenshot
from vision.camera import capture_camera
from vision.detectors.yolov8 import YOLOv8Detector
from vision.detectors.clip import CLIPClassifier

logger = logging.getLogger("VisionManager")

class VisionManager:
    """Vision orchestrator with GPU-optimized frame processing."""

    def __init__(
        self,
        target_fps: float = 4.0,
        use_fp16: bool = True,
        clip_idle_timeout: float = 10.0,
        yolo_model: str = "yolov8n.pt",
        clip_model: str = "openai/clip-vit-base-patch32",
    ):
        # Frame rate control
        self.target_fps = target_fps
        self.min_frame_interval = 1.0 / target_fps if target_fps > 0 else 0.0
        self._last_frame_time: Dict[str, float] = {"screen": 0.0, "camera": 0.0}
        self._frame_count: int = 0
        self._frames_processed: int = 0

        # GPU settings
        self.use_fp16 = use_fp16

        # YOLOv8 - always loaded (lightweight ~6MB for nano)
        self.yolo = YOLOv8Detector(model_name=yolo_model, use_fp16=use_fp16)

        # CLIP - lazy loaded/unloaded
        self._clip: Optional[CLIPClassifier] = None
        self._clip_model_name = clip_model
        self._clip_last_used: float = 0.0
        self._clip_idle_timeout = clip_idle_timeout
        self._clip_unload_task: Optional[asyncio.Task] = None

        # Processing state
        self._running = False

    def _get_clip(self) -> CLIPClassifier:
        """Lazy-load CLIP classifier to GPU only when needed."""
        if self._clip is None:
            logger.info(f"Loading CLIP model '{self._clip_model_name}' (lazy load)...")
            self._clip = CLIPClassifier(
                model_name=self._clip_model_name,
                use_fp16=self.use_fp16
            )
        self._clip_last_used = time.time()
        self._schedule_clip_unload()
        return self._clip

    def _unload_clip(self) -> None:
        """Unload CLIP from GPU to free VRAM."""
        if self._clip is not None:
            logger.info("Unloading CLIP model to free VRAM...")
            if hasattr(self._clip, 'unload'):
                self._clip.unload()
            self._clip = None
            # Force garbage collection for GPU memory
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

    def _schedule_clip_unload(self) -> None:
        """Schedule CLIP unload after idle timeout."""
        if self._clip_unload_task and not self._clip_unload_task.done():
            self._clip_unload_task.cancel()
        try:
            loop = asyncio.get_running_loop()
            self._clip_unload_task = loop.create_task(self._clip_idle_checker())
        except RuntimeError:
            pass

    async def _clip_idle_checker(self) -> None:
        """Check if CLIP has been idle long enough to unload."""
        await asyncio.sleep(self._clip_idle_timeout)
        if self._clip is not None:
            elapsed = time.time() - self._clip_last_used
            if elapsed >= self._clip_idle_timeout:
                self._unload_clip()

    def should_process_frame(self, source: str) -> bool:
        """Frame rate throttle - returns True if enough time has passed since last frame for this source."""
        now = time.time()
        self._frame_count += 1
        last_time = self._last_frame_time.get(source, 0.0)
        if now - last_time >= self.min_frame_interval:
            self._last_frame_time[source] = now
            self._frames_processed += 1
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Return processing statistics."""
        return {
            "total_frames_received": self._frame_count,
            "frames_processed": self._frames_processed,
            "target_fps": self.target_fps,
            "clip_loaded": self._clip is not None,
            "yolo_loaded": self.yolo is not None,
            "use_fp16": self.use_fp16,
        }

    async def get_screenshot(self) -> bytes:
        """Capture the screen."""
        logger.info("Triggering screenshot capture...")
        return await asyncio.to_thread(capture_screenshot)

    async def get_camera_frame(self) -> bytes:
        """Capture from the camera."""
        logger.info("Triggering webcam capture...")
        return await asyncio.to_thread(capture_camera)

    async def detect_objects(self, img_bytes: bytes, source: str = "screen") -> List[Dict[str, Any]]:
        """Run YOLOv8 object detection."""
        if not self.should_process_frame(source):
            return []
        return self.yolo.detect(img_bytes)

    async def classify_scene(self, img_bytes: bytes, labels: Optional[List[str]] = None) -> str:
        """Run CLIP scene classification (lazy loaded)."""
        clip = self._get_clip()
        return clip.describe(img_bytes, labels=labels)

    async def analyze_screen(self, force: bool = False) -> Dict[str, Any]:
        """Capture and analyze screen contents with frame rate throttling."""
        if not force and not self.should_process_frame("screen"):
            return {
                "source": "screen",
                "detected_objects": [],
                "description": "Skipped screen analysis due to frame rate throttling.",
                "skipped": True,
                "reason": "frame_rate_throttle"
            }

        img_bytes = await asyncio.to_thread(capture_screenshot)

        # Save to cache file for preview
        import os
        cache_dir = os.path.join("data", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        img_path = os.path.join(cache_dir, "screen_capture.png")
        try:
            with open(img_path, "wb") as f:
                f.write(img_bytes)
        except Exception as e:
            logger.error(f"Failed to save screen capture to cache: {e}")

        # YOLO detection first (lightweight, always loaded)
        objects = self.yolo.detect(img_bytes)

        # Screen labels for CLIP
        screen_labels = [
            "a terminal window with code",
            "a Linux desktop environment",
            "a web browser",
            "a video game",
            "a text editor",
            "a movie or video playing",
            "a file manager or document list"
        ]
        
        clip = self._get_clip()
        description = clip.describe(img_bytes, labels=screen_labels)
        
        translation_map = {
            "a terminal window with code": "una ventana de terminal con código",
            "a Linux desktop environment": "un entorno de escritorio Linux",
            "a web browser": "un navegador web",
            "a video game": "un videojuego",
            "a text editor": "un editor de texto",
            "a movie or video playing": "una película o video reproduciéndose",
            "a file manager or document list": "un gestor de archivos o lista de documentos"
        }
        
        description_es = ""
        for eng, esp in translation_map.items():
            if eng in description:
                description_es = esp
                break
        if not description_es:
            description_es = description

        return {
            "source": "screen",
            "detected_objects": [obj["label"] for obj in objects],
            "object_count": len(objects),
            "description": description_es,
            "raw_size_bytes": len(img_bytes),
            "frame_number": self._frames_processed,
            "path": img_path,
        }

    async def analyze_camera(self, force: bool = False) -> Dict[str, Any]:
        """Capture and analyze camera frame with frame rate throttling."""
        if not force and not self.should_process_frame("camera"):
            return {
                "source": "camera",
                "detected_objects": [],
                "description": "Skipped camera analysis due to frame rate throttling.",
                "skipped": True,
                "reason": "frame_rate_throttle"
            }

        img_bytes = await asyncio.to_thread(capture_camera)

        # Save to cache file for preview
        import os
        cache_dir = os.path.join("data", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        img_path = os.path.join(cache_dir, "camera_capture.png")
        try:
            with open(img_path, "wb") as f:
                f.write(img_bytes)
        except Exception as e:
            logger.error(f"Failed to save camera capture to cache: {e}")

        objects = self.yolo.detect(img_bytes)

        # Camera labels for CLIP, focusing on handheld objects/states
        camera_labels = [
            "a person holding a mobile phone",
            "a person holding a pen or writing instrument",
            "a person holding a coffee mug, cup, or glass",
            "a person holding keys",
            "a person holding a computer mouse",
            "a person holding a wallet or credit card",
            "a person holding a watch",
            "a person holding a book, notebook, or document",
            "a person holding a remote control",
            "a person holding a tool or pair of scissors",
            "a person showing their open, empty hand",
            "a webcam view of a person at a desk",
            "a person sitting in front of a laptop",
            "a close-up of a hand holding an object"
        ]
        
        clip = self._get_clip()
        description = clip.describe(img_bytes, labels=camera_labels)

        translation_map = {
            "a person holding a mobile phone": "una persona sosteniendo un teléfono móvil",
            "a person holding a pen or writing instrument": "una persona sosteniendo un bolígrafo o lápiz",
            "a person holding a coffee mug, cup, or glass": "una persona sosteniendo una taza de café o vaso",
            "a person holding keys": "una persona sosteniendo llaves",
            "a person holding a computer mouse": "una persona sosteniendo un mouse de computadora",
            "a person holding a wallet or credit card": "una persona sosteniendo una billetera o tarjeta de crédito",
            "a person holding a watch": "una persona sosteniendo un reloj",
            "a person holding a book, notebook, or document": "una persona sosteniendo un libro, cuaderno o documento",
            "a person holding a remote control": "una persona sosteniendo un control remoto",
            "a person holding a tool or pair of scissors": "una persona sosteniendo una herramienta o tijeras",
            "a person showing their open, empty hand": "una persona mostrando la mano abierta y vacía",
            "a webcam view of a person at a desk": "una vista de cámara web de una persona en su escritorio",
            "a person sitting in front of a laptop": "una persona sentada frente a una laptop",
            "a close-up of a hand holding an object": "un primer plano de una mano sosteniendo un objeto"
        }
        
        description_es = ""
        for eng, esp in translation_map.items():
            if eng in description:
                description_es = esp
                break
        if not description_es:
            description_es = description

        return {
            "source": "camera",
            "detected_objects": [obj["label"] for obj in objects],
            "object_count": len(objects),
            "description": description_es,
            "raw_size_bytes": len(img_bytes),
            "frame_number": self._frames_processed,
            "path": img_path,
        }

    async def shutdown(self) -> None:
        """Clean shutdown - free all GPU resources."""
        logger.info("Shutting down VisionManager...")
        self._running = False
        self._unload_clip()
        if hasattr(self.yolo, 'unload'):
            self.yolo.unload()
        logger.info("VisionManager shut down complete.")
