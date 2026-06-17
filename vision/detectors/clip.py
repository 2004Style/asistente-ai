"""
Image-text classifier implementing CLIP, with lazy loading, FP16 precision, and VRAM management.
"""
import logging
import gc
from typing import List, Dict, Any, Optional

logger = logging.getLogger("CLIPClassifier")

class CLIPClassifier:
    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        use_fp16: bool = True,
        device: Optional[str] = None
    ):
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self.model = None
        self.processor = None
        self._initialized = False

        # Detect device
        if device:
            self.device = device
        else:
            self.device = "cpu"
            try:
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
            except ImportError:
                pass

    def _init_model(self):
        if self._initialized:
            return
        try:
            from transformers import CLIPModel, CLIPProcessor
            import torch
            
            logger.info(f"Loading CLIP model '{self.model_name}' on device '{self.device}'")
            
            # Select precision dtype
            dtype = torch.float32
            if self.use_fp16 and "cuda" in self.device:
                dtype = torch.float16
                logger.info("Using FP16 precision for CLIP model loading.")

            self.model = CLIPModel.from_pretrained(self.model_name, torch_dtype=dtype).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self._initialized = True
        except ImportError:
            logger.warning("transformers package is not installed. Running in mock CLIP classifier mode.")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")

    def classify(self, image_data: bytes, candidate_labels: List[str]) -> Dict[str, float]:
        """Perform classification using CLIP or mock fallback."""
        self._init_model()
        if not self._initialized or self.model is None:
            # Deterministic mock scoring based on candidate labels
            scores = {}
            for idx, label in enumerate(candidate_labels):
                scores[label] = round(1.0 / (idx + 1), 4)
            return scores

        try:
            import io
            from PIL import Image
            import torch

            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            inputs = self.processor(text=candidate_labels, images=image, return_tensors="pt", padding=True)
            
            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # If model is FP16, we may need to cast inputs to float16 or model handles it
            # CLIP model expects pixel_values in the same dtype as model weights
            if self.use_fp16 and "cuda" in self.device:
                if "pixel_values" in inputs:
                    inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
                
            probs_list = probs[0].tolist()
            return {label: round(prob, 4) for label, prob in zip(candidate_labels, probs_list)}
        except Exception as e:
            logger.error(f"Error in CLIP classification: {e}")
            return {label: 0.0 for label in candidate_labels}

    def describe(self, image_data: bytes, labels: Optional[List[str]] = None) -> str:
        """Return a natural language description of the image using CLIP classification match."""
        if not labels:
            labels = [
                "a terminal window with code",
                "a Linux desktop environment",
                "a web browser",
                "a video game",
                "a webcam view of a person at a desk",
                "a dark room",
                "a text editor"
            ]
        
        scores = self.classify(image_data, labels)
        if not scores:
            is_camera = len(image_data) > 43 and image_data[43] == 239
            if is_camera:
                return "Una captura de cámara web mostrando a un usuario en su escritorio de trabajo"
            else:
                return "Una captura de pantalla de un escritorio Linux con varias ventanas abiertas"

        # Find label with highest score
        best_label = max(scores, key=scores.get)
        return best_label

    def unload(self):
        """Release GPU memory by unloading the model."""
        if self.model is not None:
            logger.info(f"Unloading CLIP model '{self.model_name}' to free VRAM")
            self.model = None
            self.processor = None
            self._initialized = False
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
