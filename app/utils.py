from pathlib import Path

# 支援的圖片格式
VALID_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.heic'}

def get_files(input_path, recursive=False):
    """
    根據路徑搜尋所有符合格式的圖片檔案。
    """
    path = Path(input_path)
    if not path.exists():
        return []
        
    if path.is_file():
        # 如果使用者直接選了一個檔案
        return [path] if path.suffix.lower() in VALID_EXTS else []
    
    files = []
    pattern = "**/*" if recursive else "*"
    
    for p in path.glob(pattern):
        if p.is_file() and p.suffix.lower() in VALID_EXTS:
            files.append(p)
            
    return files