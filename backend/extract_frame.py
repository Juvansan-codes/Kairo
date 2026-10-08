import cv2
from pathlib import Path

def extract_frames():
    gif_path = Path(r"d:\College Files\Kairo\backend\models\floorplan-to-3d-repo\docs\preview.gif")
    out_dir = Path(r"d:\College Files\Kairo\backend\outputs\test_images")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(gif_path))
    
    frames_to_extract = [0, 30, 60] # Different frames for different floorplans
    
    frame_idx = 0
    saved_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx in frames_to_extract:
            out_path = out_dir / f"F{saved_count+1}_extracted.png"
            cv2.imwrite(str(out_path), frame)
            print(f"Successfully extracted frame {frame_idx} to {out_path}")
            saved_count += 1
            
        frame_idx += 1
        
    cap.release()

if __name__ == "__main__":
    extract_frames()
