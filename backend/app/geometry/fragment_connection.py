"""
Wall Fragment Connection Module

This module improves the MGR pipeline's ability to handle fragmented wall masks
from perception models that produce disconnected wall components.

Purpose: Bridge small gaps between wall fragments to form more complete closed regions.
"""

import numpy as np
import cv2
from skimage import morphology
from typing import Tuple

def improve_wall_mask(wall_mask: np.ndarray, 
                     close_gaps_px: int = 5,
                     remove_small_fragments_px2: int = 20) -> np.ndarray:
    """
    Improve a fragmented wall mask by closing small gaps and removing tiny fragments.
    
    Parameters
    ----------
    wall_mask : np.ndarray
        Boolean or binary wall mask from perception model
    close_gaps_px : int
        Maximum gap size in pixels to close between wall fragments (default: 5)
    remove_small_fragments_px2 : int
        Minimum wall fragment size in pixels² to keep (default: 20)
        
    Returns
    -------
    np.ndarray
        Improved boolean wall mask with fragments connected
    """
    if wall_mask is None or not isinstance(wall_mask, np.ndarray):
        return wall_mask
        
    # Convert to binary
    binary_mask = wall_mask.astype(bool)
    
    # Morphological closing to connect nearby fragments
    # Use a larger kernel to bridge gaps
    kernel_size = close_gaps_px
    kernel = morphology.disk(kernel_size)
    
    # Close gaps
    closed = morphology.binary_closing(binary_mask, kernel)
    
    # Remove small isolated fragments that are noise
    cleaned = morphology.remove_small_objects(closed, min_size=remove_small_fragments_px2)
    
    # Optional: skeleton thinning followed by dilation to maintain wall thickness
    # This helps create more consistent wall widths
    skeleton = morphology.skeletonize(cleaned)
    
    # Dilate skeleton slightly to restore some thickness
    dilate_kernel = morphology.disk(2)
    restored = morphology.binary_dilation(skeleton, dilate_kernel)
    
    return restored.astype(bool)
