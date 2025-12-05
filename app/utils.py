import sys
import os
import shutil
import subprocess
from pathlib import Path

VALID_IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.heic'}
VALID_VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'}

def get_files(input_path, recursive=False, file_types='image'):
    path = Path(input_path)
    if not path.exists():
        return []
        
    valid_exts = set()
    if file_types in ['image', 'all']:
        valid_exts.update(VALID_IMG_EXTS)
    if file_types in ['video', 'all']:
        valid_exts.update(VALID_VIDEO_EXTS)

    if path.is_file():
        return [path] if path.suffix.lower() in valid_exts else []
    
    files = []
    pattern = "**/*" if recursive else "*"
    
    for p in path.glob(pattern):
        if p.is_file() and p.suffix.lower() in valid_exts:
            files.append(p)
            
    return files

def is_ffmpeg_installed():
    return shutil.which("ffmpeg") is not None

def get_video_duration(file_path):
    try:
        cmd = [
            "ffprobe", "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 0.0