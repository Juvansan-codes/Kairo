import abc
import os
import yaml
import torch
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
import segmentation_models_pytorch as smp
from safetensors.torch import load_file
import time

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

CLASS_NAMES = ("floor", "wall", "door", "window")
CLASS_COLORS = {
    "floor": (240, 240, 235),
    "wall": (40, 40, 45),
    "door": (230, 120, 50),
    "window": (60, 150, 220),
}

class PerceptionModel(abc.ABC):
    @abc.abstractmethod
    def predict(self, image_path: Path) -> dict:
        pass

class ResNetUNetPerception(PerceptionModel):
    def __init__(self, run_dir: Path, device: str = "auto", improve_walls: bool = True):
        self.run_dir = run_dir
        self.improve_walls = improve_walls  # NEW: enable wall fragment improvement
        cfg_path = run_dir / "config.yaml"
        ckpt_path = run_dir / "best.safetensors"
        
        if not cfg_path.exists() or not ckpt_path.exists():
            raise FileNotFoundError("Model config or weights missing. Ensure weights are downloaded.")
            
        with open(cfg_path, "r") as f:
            self.cfg = yaml.safe_load(f)
            
        self.device = self._resolve_device(device)
        self.image_size = tuple(self.cfg["data"]["image_size"]) # (H, W)
        self.letterbox = self.cfg["data"].get("letterbox", False)
        self.normalize = self.cfg["data"]["normalize"]
        
        self.model = smp.Unet(
            encoder_name=self.cfg["model"]["encoder_name"],
            encoder_weights=None,
            in_channels=3,
            classes=len(CLASS_NAMES)
        ).to(self.device)
        
        state = load_file(ckpt_path)
        
        # Depending on how the state dict was saved, we might need to strip "model." prefix
        clean_state = {}
        for k, v in state.items():
            if k.startswith("model."):
                clean_state[k[6:]] = v
            else:
                clean_state[k] = v
                
        self.model.load_state_dict(clean_state, strict=False)
        self.model.eval()

    def _resolve_device(self, name: str) -> torch.device:
        if name != "auto":
            return torch.device(name)
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    def preprocess(self, image_path: Path):
        """Loads PNG/JPG, preserves aspect ratio, letterboxes, and returns tensor + metadata."""
        img = Image.open(image_path).convert("RGB")
        orig_w, orig_h = img.size
        
        H, W = self.image_size
        if self.letterbox:
            scale = min(W / orig_w, H / orig_h)
            inner_w = max(1, int(round(orig_w * scale)))
            inner_h = max(1, int(round(orig_h * scale)))
        else:
            inner_w, inner_h = W, H
            scale = 1.0
            
        img_resized = img.resize((inner_w, inner_h), Image.Resampling.BILINEAR)
        img_np = np.array(img_resized)
        image_t = torch.from_numpy(img_np).permute(2, 0, 1).contiguous().float().div_(255.0)
        
        if self.normalize:
            mean = torch.tensor(IMAGENET_MEAN).view(3, 1, 1)
            std = torch.tensor(IMAGENET_STD).view(3, 1, 1)
            image_t = (image_t - mean) / std
            
        top = 0
        left = 0
        if self.letterbox and (inner_h, inner_w) != (H, W):
            top = (H - inner_h) // 2
            left = (W - inner_w) // 2
            if self.normalize:
                canvas = torch.zeros(3, H, W)
            else:
                canvas = torch.tensor(IMAGENET_MEAN).view(3, 1, 1).expand(3, H, W).clone()
            canvas[:, top:top + inner_h, left:left + inner_w] = image_t
            image_t = canvas

        metadata = {
            "orig_w": orig_w,
            "orig_h": orig_h,
            "processed_w": W,
            "processed_h": H,
            "inner_w": inner_w,
            "inner_h": inner_h,
            "scale": scale,
            "pad_top": top,
            "pad_left": left
        }
        return image_t, metadata, img

    def predict(self, image_path: Path) -> dict:
        t0 = time.time()
        image_t, metadata, orig_img = self.preprocess(image_path)
        
        with torch.no_grad():
            logits = self.model(image_t.unsqueeze(0).to(self.device))
        
        mask = logits.argmax(dim=1).squeeze(0).to("cpu", torch.uint8).numpy()
        
        # Crop mask to inner image
        inner_h, inner_w = metadata["inner_h"], metadata["inner_w"]
        top, left = metadata["pad_top"], metadata["pad_left"]
        
        if (inner_h, inner_w) != mask.shape:
            # Mask out the padding region
            cleaned = np.zeros_like(mask) # Floor ID is 0
            cleaned[top:top + inner_h, left:left + inner_w] = mask[top:top + inner_h, left:left + inner_w]
            mask = cleaned

        # NEW: Improve wall mask if enabled
        if self.improve_walls:
            from app.geometry.fragment_connection import improve_wall_mask
            wall_mask_bool = (mask == 1)
            improved_wall_mask = improve_wall_mask(
                wall_mask_bool,
                close_gaps_px=8,  # Aggressively close gaps
                remove_small_fragments_px2=15  # Remove tiny noise
            )
            # Update the mask
            mask[mask == 1] = 0  # Clear old walls
            mask[improved_wall_mask] = 1  # Set improved walls

        inference_time = time.time() - t0
        
        # Construct the project schema
        semantic_regions = []
        class_counts = {}
        for idx, name in enumerate(CLASS_NAMES):
            count = int((mask == idx).sum())
            class_counts[name] = count
            
            semantic_regions.append({
                "class_id": idx,
                "class_name": name,
                "pixel_count": count
            })
            
        result = {
            "semantic_regions": semantic_regions,
            "walls": [], # Populated by Geometry
            "doors": [], # Populated by Geometry
            "windows": [], # Populated by Geometry
            "metadata": metadata,
            "inference_time": inference_time,
            "class_counts": class_counts,
            "raw_mask": mask # Keep in memory for geometry
        }
        
        return result

    def create_debug_visualization(self, image_path: Path, output_path: Path):
        result = self.predict(image_path)
        mask = result["raw_mask"]
        
        # Render
        img = Image.open(image_path).convert("RGB")
        img_resized = img.resize((self.image_size[1], self.image_size[0]), Image.Resampling.BILINEAR)
        # Apply mask coloring
        mask_rgb = np.zeros((*mask.shape, 3), dtype=np.uint8)
        for idx, name in enumerate(CLASS_NAMES):
            mask_rgb[mask == idx] = CLASS_COLORS[name]
            
        mask_img = Image.fromarray(mask_rgb)
        
        # Blend
        blended = Image.blend(img_resized, mask_img, alpha=0.6)
        blended.save(output_path)
        return result
