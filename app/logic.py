import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter # 新增 ImageEnhance
from app.utils import get_files

# 定義一個簡單的 Log 介面
def default_logger(msg):
    print(msg)

# -----------------------------------------------------------------------------
# 任務 1: 圖片縮放 (Scaling) + 增強
# -----------------------------------------------------------------------------
def task_scaling(log_callback, input_path, output_path, scale_ratio, recursive, 
                 convert_jpg, lower_ext, delete_original, prefix, postfix, 
                 crop_doubao, sharpen_factor, brightness_factor, author):
    
    log_callback(f"🚀 [Scaling] 開始執行 (比例: {scale_ratio})")
    files = get_files(input_path, recursive)
    log_callback(f"📂 找到 {len(files)} 個檔案")

    out_dir_base = Path(output_path)
    if not out_dir_base.exists():
        out_dir_base.mkdir(parents=True, exist_ok=True)

    for file_path in files:
        try:
            # 計算相對路徑與輸出資料夾
            if Path(input_path).is_dir():
                rel_path = file_path.relative_to(Path(input_path))
            else:
                rel_path = Path(file_path.name)
            
            dest_folder = out_dir_base / rel_path.parent
            dest_folder.mkdir(parents=True, exist_ok=True)

            # 檔名處理
            stem = file_path.stem
            new_stem = f"{prefix}{stem}{postfix}"
            original_ext = file_path.suffix
            final_ext = ".jpg" if convert_jpg else original_ext
            if lower_ext:
                final_ext = final_ext.lower()

            output_file = dest_folder / f"{new_stem}{final_ext}"

            # --- Pillow 圖片處理 ---
            with Image.open(file_path) as img:
                # 轉檔前置處理
                if final_ext.lower() in ['.jpg', '.jpeg']:
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

                # 豆包圖裁切
                if crop_doubao:
                    w, h = img.size
                    safe_w, safe_h = w - 320, h - 110
                    if safe_w > 0 and safe_h > 0:
                        ratio = w / h
                        h_wide = int(safe_w / ratio)
                        w_high = int(safe_h * ratio)
                        
                        crop_w, crop_h = w, h
                        if h_wide <= safe_h:
                            crop_w, crop_h = safe_w, h_wide
                        elif w_high <= safe_w:
                            crop_w, crop_h = w_high, safe_h
                            
                        img = img.crop((0, 0, crop_w, crop_h))
                        log_callback(f"✂️ 裁切: {file_path.name}")

                # 縮放
                if scale_ratio != 1.0:
                    new_w = int(img.width * scale_ratio)
                    new_h = int(img.height * scale_ratio)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # --- 影像增強 ---
                # 1. 銳利度 (ImageEnhance)
                # 1.0 = 原始, 0.0 = 模糊, 2.0 = 銳利
                if sharpen_factor != 1.0:
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(sharpen_factor)
                    
                # 2. 亮度
                # 1.0 = 原始, 0.0 = 全黑
                if brightness_factor != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(brightness_factor)

                # Metadata: Pillow save 不易直接寫入 EXIF Artist，但可保留部分原始 info
                # 若需寫入 EXIF 需要更底層操作 (piexif)，此處暫保留原始 save 行為
                
                save_kwargs = {"quality": 95} if final_ext.lower() in ['.jpg', '.jpeg'] else {}
                img.save(output_file, **save_kwargs)
                log_callback(f"✅ 完成: {output_file.name}")

            # 刪除原始檔
            if delete_original and convert_jpg and original_ext.lower() not in ['.jpg', '.jpeg']:
                os.remove(file_path)
                log_callback(f"🗑️ 刪除原始檔: {file_path.name}")

        except Exception as e:
            log_callback(f"❌ 失敗 {file_path.name}: {str(e)}")

    log_callback("🏁 Scaling 任務結束")

# 其他任務保持不變，為節省篇幅省略 (task_convert_jpg, task_resize_1920...) 
# 請保留原檔 logic.py 中其他的函式，或者如果需要我再貼一次完整版 logic.py
# (為了確保你複製方便，下面我把其他的函式也補上)

def task_convert_jpg(log_callback, input_path, recursive, delete_original):
    log_callback("🚀 [Convert] 開始執行")
    files = get_files(input_path, recursive)
    for file_path in files:
        if file_path.suffix.lower() in ['.jpg', '.jpeg']: continue
        try:
            output_file = file_path.with_suffix('.jpg')
            with Image.open(file_path) as img:
                rgb_im = img.convert('RGB')
                rgb_im.save(output_file, quality=90)
                log_callback(f"✅ 轉換: {file_path.name} -> .jpg")
            if delete_original:
                os.remove(file_path)
        except Exception as e:
            log_callback(f"❌ 錯誤 {file_path.name}: {e}")
    log_callback("🏁 轉換結束")

def task_resize_1920(log_callback, input_path, output_path, recursive):
    log_callback("🚀 [Resize 1920] 開始執行")
    files = get_files(input_path, recursive)
    out_dir_base = Path(output_path)
    for file_path in files:
        try:
            processed = False
            with Image.open(file_path) as img:
                w, h = img.size
                if w > 1920 or h > 1920:
                    aspect_ratio = w / h
                    if w >= h: new_w, new_h = 1920, int(1920 / aspect_ratio)
                    else: new_w, new_h = int(1920 * aspect_ratio), 1920
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    processed = True
                
                if Path(input_path).is_dir(): rel_path = file_path.relative_to(Path(input_path))
                else: rel_path = Path(file_path.name)
                dest = out_dir_base / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest, quality=90)
                msg = f"✅ 縮放: {new_w}x{new_h}" if processed else "ℹ️ 略過"
                log_callback(f"{msg} : {rel_path}")
        except Exception as e:
            log_callback(f"❌ 錯誤 {file_path.name}: {e}")
    log_callback("🏁 Resize 結束")

def task_rename(log_callback, input_path, prefix, postfix, recursive):
    log_callback("🚀 [Rename] 開始執行")
    files = get_files(input_path, recursive)
    count = 0
    for file_path in files:
        try:
            stem = file_path.stem
            if (prefix and prefix in stem) and (postfix and postfix in stem): continue
            new_name = f"{prefix}{stem}{postfix}{file_path.suffix.lower()}"
            new_path = file_path.parent / new_name
            if new_path != file_path:
                file_path.rename(new_path)
                log_callback(f"✏️ 更名: {file_path.name} -> {new_name}")
                count += 1
        except Exception as e:
            log_callback(f"❌ 錯誤 {file_path.name}: {e}")
    log_callback(f"🏁 更名結束，共修改 {count} 個檔案")

def task_multi_res(log_callback, input_path, output_path, recursive, lower_ext, orientation):
    log_callback(f"🚀 [Multi-Res] 開始執行")
    target_sizes = [1024, 512, 256, 128, 64, 32]
    files = get_files(input_path, recursive)
    out_dir_base = Path(output_path)
    for file_path in files:
        try:
            with Image.open(file_path) as img:
                w, h = img.size
                ref_size = w if orientation == 'h' else h
                if Path(input_path).is_dir(): rel_path = file_path.relative_to(Path(input_path))
                else: rel_path = Path(file_path.name)
                parent = (out_dir_base / rel_path).parent
                parent.mkdir(parents=True, exist_ok=True)
                base = file_path.stem
                ext = file_path.suffix.lower() if lower_ext else file_path.suffix
                for size in target_sizes:
                    if ref_size >= size:
                        if orientation == 'h': ratio = size / w; new_w, new_h = size, int(h * ratio)
                        else: ratio = size / h; new_w, new_h = int(w * ratio), size
                        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        resized_img.save(parent / f"{base}-{size}{ext}", quality=90)
                log_callback(f"✅ {file_path.name} 處理完成")
        except Exception as e:
            log_callback(f"❌ 錯誤 {file_path.name}: {e}")
    log_callback("🏁 多尺寸任務結束")