"""
Raster2Seq Perception Adapter for KAIRO

This module provides integration for the Raster2Seq model from Cornell-VAILab.
Raster2Seq is a sequence-to-sequence model that directly predicts structured
polygon sequences for floorplan elements (rooms, walls, doors, windows).

Repository: https://github.com/Cornell-VAILab/Raster2Seq
Paper: "Raster2Seq: Polygon Sequence Generation for Floorplan Reconstruction" (SIGGRAPH'26)
"""

import sys
import time
import argparse
import numpy as np
import torch
import cv2
from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image

# Add Raster2Seq to path
RASTER2SEQ_DIR = Path(__file__).parent.parent.parent / "Raster2Seq"
if RASTER2SEQ_DIR.exists():
    sys.path.insert(0, str(RASTER2SEQ_DIR))

try:
    from models import build_model
    from raster2seq_hub import resolve_checkpoint_path, normalize_checkpoint_name, CHECKPOINTS
    from datasets.transforms import ResizeAndPad
    from detectron2.data import transforms as T
    from engine import generate
    from datasets.discrete_tokenizer import DiscreteTokenizer
    RASTER2SEQ_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    RASTER2SEQ_AVAILABLE = False
    IMPORT_ERROR = str(e)


class Raster2SeqPerception:
    """
    Raster2Seq perception adapter for KAIRO.
    
    Benefits over ResNet34-U-Net:
    - Direct structured output (polygon sequences)
    - State-of-the-art accuracy (99.6% on Structured3D, 88.7% on CubiCasa5K)
    - Handles complex floorplans with many rooms
    - Semantic room labels included
    - No fragmentation issues
    """
    
    def __init__(self, 
                 checkpoint_key: str = "cubicasa5k",
                 device: str = "auto",
                 image_size: int = 256,
                 num_bins: int = 64):
        """
        Initialize Raster2Seq model.
        
        Parameters
        ----------
        checkpoint_key : str
            Checkpoint identifier:
            - "cubicasa5k" (88.7% RoomF1) - recommended for residential
            - "s3d-bw" (99.6% RoomF1) - best overall accuracy
            - "raster2graph" (97.0% RoomF1) - good for technical drawings
        device : str
            Device for inference ("auto", "cuda", "cpu")
        image_size : int
            Input image size (256 or 512 for high-res models)
        num_bins : int
            Number of discrete coordinate bins for tokenization
        """
        if not RASTER2SEQ_AVAILABLE:
            raise ImportError(
                f"Raster2Seq dependencies not available: {IMPORT_ERROR}\n"
                "Please install Raster2Seq requirements and compile extensions.\n"
                "See backend/RASTER2SEQ_INTEGRATION.md for instructions."
            )
        
        self.checkpoint_key = normalize_checkpoint_name(checkpoint_key)
        self.device = self._resolve_device(device)
        self.image_size = image_size
        self.num_bins = num_bins
        
        # Model components (lazy loaded)
        self.model = None
        self.tokenizer = None
        self.transform = None
        
        # Load model on initialization
        self._load_model()
    
    def _resolve_device(self, name: str) -> torch.device:
        """Resolve device name to torch.device."""
        if name != "auto":
            return torch.device(name)
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")
    
    def _get_model_args(self) -> argparse.Namespace:
        """Create argument namespace with Raster2Seq configuration."""
        import argparse
        
        args = argparse.Namespace()
        
        # Model architecture
        args.poly2seq = True
        args.seq_len = 1024
        args.num_bins = self.num_bins
        args.use_anchor = True
        args.pre_decoder_pos_embed = True
        args.learnable_dec_pe = True
        args.dec_qkv_proj = True
        args.dec_attn_concat_src = True
        args.per_token_sem_loss = True
        args.add_cls_token = True
        
        # Backbone
        args.backbone = "resnet50"
        args.lr_backbone = 0
        args.dilation = False
        args.position_embedding = "sine"
        args.position_embedding_scale = 2 * np.pi
        args.num_feature_levels = 4
        
        # Transformer
        args.enc_layers = 6
        args.dec_layers = 6
        args.dim_feedforward = 1024
        args.hidden_dim = 256
        args.dropout = 0.1
        args.nheads = 8
        args.num_queries = 800
        args.num_polys = 20
        args.dec_n_points = 4
        args.enc_n_points = 4
        
        # Input
        args.input_channels = 1
        args.image_size = self.image_size
        args.image_norm = False
        
        # Other
        args.ema4eval = False
        args.disable_sampling_cache = False
        
        return args
    
    def _load_model(self):
        """Load Raster2Seq model and weights."""
        print(f"Loading Raster2Seq checkpoint: {self.checkpoint_key}")
        
        # Get model configuration
        args = self._get_model_args()
        
        # Build model
        self.model, _, _ = build_model(args)
        self.model.to(self.device)
        
        # Load checkpoint
        checkpoint_path = resolve_checkpoint_path(self.checkpoint_key)
        print(f"Loading weights from: {checkpoint_path}")
        
        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        
        # Load model state
        if 'model' in checkpoint:
            state_dict = checkpoint['model']
        elif 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
        
        # Remove 'module.' prefix if present (from DataParallel)
        cleaned_state = {}
        for k, v in state_dict.items():
            if k.startswith('module.'):
                cleaned_state[k[7:]] = v
            else:
                cleaned_state[k] = v
        
        self.model.load_state_dict(cleaned_state, strict=False)
        self.model.eval()
        
        # Initialize tokenizer
        self.tokenizer = DiscreteTokenizer(
            num_bins=self.num_bins,
            coord_vocab_shift=1000
        )
        
        # Initialize transform
        self.transform = ResizeAndPad(target_size=self.image_size)
        
        print(f"✓ Raster2Seq model loaded successfully on {self.device}")
    
    def _preprocess_image(self, image_path: Path) -> torch.Tensor:
        """
        Preprocess image for Raster2Seq input.
        
        Returns
        -------
        torch.Tensor
            Preprocessed image tensor (1, C, H, W)
        """
        # Load image (grayscale for Raster2Seq)
        image = np.array(Image.open(image_path).convert("L"))
        
        # Apply transform
        aug_input = T.AugInput(image)
        _ = self.transform(aug_input)
        image = aug_input.image
        
        # Convert to tensor and normalize
        if len(image.shape) == 2:
            image = np.expand_dims(image, 0)  # Add channel dim
        else:
            image = image.transpose((2, 0, 1))
        
        image_tensor = (1 / 255) * torch.as_tensor(image, dtype=torch.float32)
        image_tensor = image_tensor.unsqueeze(0)  # Add batch dim
        
        return image_tensor.to(self.device)
    
    def predict(self, image_path: Path) -> Dict[str, Any]:
        """
        Run Raster2Seq inference on a floorplan image.
        
        Parameters
        ----------
        image_path : Path
            Path to input floorplan image
            
        Returns
        -------
        dict
            Perception result in KAIRO format with keys:
            - semantic_regions: list of room/opening regions
            - walls: list of wall segments (extracted from room boundaries)
            - doors: list of door openings
            - windows: list of window openings
            - metadata: model information
            - inference_time: float
            - class_counts: dict
            - raw_mask: np.ndarray (synthesized from polygon predictions)
        """
        t0 = time.time()
        
        # Preprocess
        image_tensor = self._preprocess_image(image_path)
        
        # Inference
        with torch.no_grad():
            results = generate(
                model=self.model,
                samples=[{'image': image_tensor.squeeze(0)}],
                target_size=(self.image_size, self.image_size),
                tokenizer=self.tokenizer,
                sampling=False,
                temperature=0.0,
                top_k=0,
                max_seq_len=1024
            )
        
        inference_time = time.time() - t0
        
        # Convert to KAIRO format
        result = self._convert_to_kairo_format(results[0], image_path)
        result['inference_time'] = inference_time
        result['metadata']['inference_device'] = str(self.device)
        result['metadata']['model_checkpoint'] = self.checkpoint_key
        
        return result
    
    def _convert_to_kairo_format(self, raster2seq_output: Dict, image_path: Path) -> Dict[str, Any]:
        """
        Convert Raster2Seq polygon sequence output to KAIRO format.
        
        Raster2Seq Output:
        - pred_polygons: List of (N_points, 2) arrays
        - pred_labels: Room semantic labels
        - pred_scores: Confidence scores
        """
        pred_polygons = raster2seq_output.get('pred_polygons', [])
        pred_labels = raster2seq_output.get('pred_labels', [])
        pred_scores = raster2seq_output.get('pred_scores', [])
        
        # Extract semantic regions (rooms)
        semantic_regions = []
        for i, (poly, label, score) in enumerate(zip(pred_polygons, pred_labels, pred_scores)):
            semantic_regions.append({
                'class_id': int(label) if isinstance(label, (int, np.integer)) else 0,
                'class_name': f'room_{label}',
                'polygon': poly.tolist() if isinstance(poly, np.ndarray) else poly,
                'confidence': float(score) if isinstance(score, (float, np.floating)) else 0.9,
                'area': self._compute_polygon_area(poly)
            })
        
        # Extract walls from room boundaries
        walls = self._extract_walls_from_rooms(pred_polygons, pred_scores)
        
        # TODO: Extract doors/windows if Raster2Seq outputs them separately
        # For now, we'll use empty lists and let MGR pipeline handle opening detection
        doors = []
        windows = []
        
        # Synthesize raw mask for compatibility with existing pipeline
        raw_mask = self._rasterize_polygons(pred_polygons, self.image_size)
        
        # Count classes
        unique, counts = np.unique(raw_mask, return_counts=True)
        class_counts = {
            'floor': int(counts[unique == 0][0]) if 0 in unique else 0,
            'wall': int(counts[unique == 1][0]) if 1 in unique else 0,
            'door': 0,  # Not separately detected
            'window': 0  # Not separately detected
        }
        
        return {
            'semantic_regions': semantic_regions,
            'walls': walls,
            'doors': doors,
            'windows': windows,
            'raw_mask': raw_mask,
            'inference_time': 0.0,  # Will be set by caller
            'class_counts': class_counts,
            'metadata': {
                'model': 'Raster2Seq',
                'num_rooms': len(pred_polygons),
                'num_walls': len(walls),
                'image_size': self.image_size
            }
        }
    
    def _extract_walls_from_rooms(self, room_polygons: List, scores: List) -> List:
        """
        Extract wall segments from room polygon boundaries.
        Each edge of a room polygon becomes a potential wall.
        """
        walls = []
        wall_id = 0
        
        for room_idx, (poly, score) in enumerate(zip(room_polygons, scores)):
            if isinstance(poly, np.ndarray):
                points = poly
            else:
                points = np.array(poly)
            
            # Extract edges as wall segments
            for i in range(len(points)):
                start = points[i]
                end = points[(i + 1) % len(points)]
                
                walls.append({
                    'id': f'wall_{wall_id}',
                    'start': tuple(float(x) for x in start),
                    'end': tuple(float(x) for x in end),
                    'confidence': float(score) if isinstance(score, (float, np.floating)) else 0.9,
                    'source': f'raster2seq_room_{room_idx}',
                    'room_id': room_idx
                })
                wall_id += 1
        
        return walls
    
    def _compute_polygon_area(self, polygon) -> float:
        """Compute area of a polygon using Shoelace formula."""
        if isinstance(polygon, np.ndarray):
            points = polygon
        else:
            points = np.array(polygon)
        
        if len(points) < 3:
            return 0.0
        
        x = points[:, 0]
        y = points[:, 1]
        return float(0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))
    
    def _rasterize_polygons(self, polygons: List, image_size: int) -> np.ndarray:
        """
        Rasterize room polygons into a binary mask.
        
        Parameters
        ----------
        polygons : List
            List of room polygons
        image_size : int
            Output mask size
            
        Returns
        -------
        np.ndarray
            Binary mask (H, W) with 0=background, 1=wall/room interior
        """
        mask = np.zeros((image_size, image_size), dtype=np.uint8)
        
        for poly in polygons:
            if isinstance(poly, np.ndarray):
                points = poly
            else:
                points = np.array(poly)
            
            # Convert to integer coordinates
            points_int = points.astype(np.int32)
            
            # Fill polygon (room interior)
            cv2.fillPoly(mask, [points_int], 1)
        
        return mask


def get_raster2seq_adapter(checkpoint: str = "cubicasa5k", **kwargs) -> Raster2SeqPerception:
    """
    Factory function to create Raster2Seq adapter.
    
    Parameters
    ----------
    checkpoint : str
        Checkpoint identifier ("cubicasa5k", "s3d-bw", "raster2graph")
    **kwargs
        Additional arguments for Raster2SeqPerception
        
    Returns
    -------
    Raster2SeqPerception
        Configured Raster2Seq adapter
        
    Usage
    -----
    In analysis.py:
    
    try:
        from app.perception.raster2seq_adapter import get_raster2seq_adapter
        self.perception = get_raster2seq_adapter()
        print("✓ Using Raster2Seq (primary model)")
    except (ImportError, NotImplementedError):
        from app.perception.adapter import ResNetUNetPerception
        self.perception = ResNetUNetPerception(...)
        print("⚠ Using ResNet34-U-Net fallback")
    """
    return Raster2SeqPerception(checkpoint_key=checkpoint, **kwargs)
