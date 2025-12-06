import sys
import os
import shutil
import subprocess
from pathlib import Path

# 支援的圖片格式 (加入 HEIC/HEIF)
VALID_IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.heic', '.heif'}
# 支援的影片格式
VALID_VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'}

def get_files(input_path, recursive=False, file_types='image'):
    path = Path(input_path)
    if not path.exists():
        return []
        
    valid_exts = set()
    if file_types == 'image':
        valid_exts.update(VALID_IMG_EXTS)
    elif file_types == 'video':
        valid_exts.update(VALID_VIDEO_EXTS)
    # 若 file_types == 'all'，我們保持 valid_exts 為空，但在下方邏輯做特殊處理

    # 如果輸入是單一檔案
    if path.is_file():
        # 如果是 'all'，直接接受；否則檢查副檔名
        if file_types == 'all':
            return [path]
        return [path] if path.suffix.lower() in valid_exts else []
    
    # 如果輸入是資料夾
    files = []
    pattern = "**/*" if recursive else "*"
    
    for p in path.glob(pattern):
        if p.is_file():
            # 關鍵修正：如果是 'all'，不檢查副檔名，全部加入
            if file_types == 'all':
                # 排除隱藏檔 (.DS_Store 等)
                if not p.name.startswith('.'):
                    files.append(p)
            else:
                if p.suffix.lower() in valid_exts:
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