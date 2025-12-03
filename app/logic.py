import os
import subprocess
import json
import re
from pathlib import Path
from PIL import Image, ImageEnhance
from app.utils import get_files, is_ffmpeg_installed, get_video_duration

def default_logger(msg):
    print(msg)

# -----------------------------------------------------------------------------
# Helper: 取得媒體資訊
# -----------------------------------------------------------------------------
def get_media_info(file_path):
    path = Path(file_path)
    ext = path.suffix.lower()
    info_str = f"檔案: {path.name}\n"
    
    try:
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp']:
            with Image.open(path) as img:
                info_str += f"格式: {img.format}\n尺寸: {img.size} (WxH)\n模式: {img.mode}\n"
                exif = img._getexif()
                if exif:
                    info_str += "\n[EXIF 資訊]\n"
                    for tag_id, value in exif.items():
                        if tag_id == 315: info_str += f"Artist: {value}\n"
                        elif tag_id == 270: info_str += f"Description: {value}\n"
                        elif tag_id == 36867: info_str += f"DateTaken: {value}\n"
                if img.info:
                    info_str += "\n[Info Dictionary]\n"
                    for k, v in img.info.items():
                        if isinstance(v, (str, int, float)):
                            info_str += f"{k}: {v}\n"

        elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
            if not is_ffmpeg_installed():
                return info_str + "\n(請安裝 FFmpeg 以查看影片詳細資訊)"
            
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if result.returncode == 0:
                data = json.loads(result.stdout)
                fmt = data.get('format', {})
                tags = fmt.get('tags', {})
                
                info_str += f"時長: {fmt.get('duration', 'N/A')} 秒\n"
                info_str += f"Bitrate: {fmt.get('bit_rate', 'N/A')}\n"
                info_str += "\n[Metadata Tags]\n"
                for k, v in tags.items():
                    info_str += f"{k}: {v}\n"
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        info_str += f"\n[Video Stream]\nCodec: {stream.get('codec_name')}\n解析度: {stream.get('width')}x{stream.get('height')}\n"
            else:
                info_str += f"\n讀取失敗: {result.stderr}"

    except Exception as e:
        info_str += f"\n發生錯誤: {str(e)}"
        
    return info_str

# -----------------------------------------------------------------------------
# 任務 1: 圖片處理 (Scaling + Meta + Enhance)
# -----------------------------------------------------------------------------
def task_scaling(log_callback, progress_callback, current_file_callback, file_progress_callback,
                 input_path, output_path, mode, mode_value_1, mode_value_2,
                 recursive, convert_jpg, lower_ext, delete_original, 
                 prefix, postfix, crop_doubao, sharpen_factor, brightness_factor, 
                 remove_metadata, author, description):
    
    log_callback(f"🚀 [Image Process] 開始 (模式: {mode})")
    files = get_files(input_path, recursive, file_types='image')
    total = len(files)
    log_callback(f"📂 找到 {total} 張圖片")

    out_dir_base = Path(output_path)
    if not out_dir_base.exists():
        out_dir_base.mkdir(parents=True, exist_ok=True)

    for i, file_path in enumerate(files):
        try:
            pct = int(((i) / total) * 100)
            progress_callback(pct)
            current_file_callback(file_path.name)
            file_progress_callback(0)

            if Path(input_path).is_dir():
                rel_path = file_path.relative_to(Path(input_path))
            else:
                rel_path = Path(file_path.name)
            
            dest_folder = out_dir_base / rel_path.parent
            dest_folder.mkdir(parents=True, exist_ok=True)

            stem = file_path.stem
            new_stem = f"{prefix}{stem}{postfix}"
            original_ext = file_path.suffix
            final_ext = ".jpg" if convert_jpg else original_ext
            if lower_ext:
                final_ext = final_ext.lower()

            output_file = dest_folder / f"{new_stem}{final_ext}"

            with Image.open(file_path) as img:
                # 1. 移除 Meta (如果勾選)
                if remove_metadata:
                    img.info.clear() 

                # 2. 轉檔前置
                if final_ext.lower() in ['.jpg', '.jpeg']:
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img = img.convert('RGBA')
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

                # 3. 裁切
                if crop_doubao:
                    w, h = img.size
                    safe_w, safe_h = w - 320, h - 110
                    if safe_w > 0 and safe_h > 0:
                        ratio = w / h
                        h_wide = int(safe_w / ratio)
                        w_high = int(safe_h * ratio)
                        crop_w, crop_h = (safe_w, h_wide) if h_wide <= safe_h else (w_high, safe_h)
                        img = img.crop((0, 0, crop_w, crop_h))
                        log_callback(f"✂️ [{i+1}/{total}] 裁切: {file_path.name}")

                # 4. 縮放
                w, h = img.size
                new_w, new_h = w, h
                should_resize = False

                if mode == 'ratio':
                    ratio = mode_value_1
                    if ratio != 1.0:
                        new_w = int(w * ratio); new_h = int(h * ratio); should_resize = True
                
                elif mode == 'width':
                    # 強制指定寬度
                    target_w = int(mode_value_1)
                    if target_w > 0:
                        ratio = target_w / w
                        new_w = target_w
                        new_h = int(h * ratio)
                        should_resize = True
                
                elif mode == 'height':
                    # 強制指定高度
                    target_h = int(mode_value_1)
                    if target_h > 0:
                        ratio = target_h / h
                        new_h = target_h
                        new_w = int(w * ratio)
                        should_resize = True

                if should_resize:
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    log_callback(f"📏 [{i+1}/{total}] 縮放: {w}x{h} -> {new_w}x{new_h}")
                else:
                    log_callback(f"➡️ [{i+1}/{total}] 處理: {file_path.name}")

                # 5. 影像增強
                if sharpen_factor != 1.0:
                    img = ImageEnhance.Sharpness(img).enhance(sharpen_factor)
                if brightness_factor != 1.0:
                    img = ImageEnhance.Brightness(img).enhance(brightness_factor)

                # 6. 儲存與寫入新 Meta
                save_kwargs = {}
                if final_ext.lower() in ['.jpg', '.jpeg']:
                    save_kwargs["quality"] = 95
                elif final_ext.lower() == '.png':
                    from PIL.PngImagePlugin import PngInfo
                    metadata = PngInfo()
                    if author: metadata.add_text("Artist", author)
                    if description: metadata.add_text("Description", description)
                    save_kwargs["pnginfo"] = metadata

                img.save(output_file, **save_kwargs)

            # 修正後的刪除邏輯：只要勾選刪除且來源與目標不同，即刪除
            if delete_original:
                if file_path.absolute() != output_file.absolute():
                    try:
                        os.remove(file_path)
                        log_callback(f"    🗑️ 刪除原始檔")
                    except Exception as del_err:
                        log_callback(f"    ⚠️ 刪除失敗: {str(del_err)}")
            
            file_progress_callback(100)

        except Exception as e:
            log_callback(f"❌ 失敗 {file_path.name}: {str(e)}")

    progress_callback(100)
    current_file_callback("全部完成")
    file_progress_callback(100)
    log_callback("🏁 圖片處理結束")

# -----------------------------------------------------------------------------
# 任務 2: 影片銳利化 (含解析度適應、Meta移除)
# -----------------------------------------------------------------------------
def task_video_sharpen(log_callback, progress_callback, current_file_callback, file_progress_callback,
                       input_path, output_path, recursive, 
                       lower_ext, delete_original, prefix, postfix,
                       luma_m_size, luma_amount, 
                       scale_mode, scale_value, 
                       convert_h264, remove_metadata, author, description):
    
    if not is_ffmpeg_installed():
        log_callback("❌ 錯誤：找不到 FFmpeg")
        return

    log_callback(f"🚀 [Video Sharpen] 開始")
    files = get_files(input_path, recursive, file_types='video')
    total_count = len(files)
    
    if total_count == 0:
        log_callback("⚠️ 未找到任何影片檔")
        return

    log_callback(f"📂 找到 {total_count} 個影片檔，正在計算總時長...")
    
    total_batch_duration = 0.0
    file_durations = {}
    for f in files:
        dur = get_video_duration(f)
        if dur <= 0: dur = 1.0
        file_durations[str(f)] = dur
        total_batch_duration += dur
        
    log_callback(f"⏱️ 任務總時長: {total_batch_duration:.2f} 秒")

    out_dir_base = Path(output_path)
    if not out_dir_base.exists():
        out_dir_base.mkdir(parents=True, exist_ok=True)

    time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d+)")
    accumulated_duration = 0.0

    for i, file_path in enumerate(files):
        try:
            current_file_callback(file_path.name)
            file_progress_callback(0)
            
            current_total_pct = int((accumulated_duration / total_batch_duration) * 100)
            progress_callback(current_total_pct)
            
            log_callback(f"🎥 [{i+1}/{total_count}] 轉檔中: {file_path.name} ...")

            if Path(input_path).is_dir():
                rel_path = file_path.relative_to(Path(input_path))
            else:
                rel_path = Path(file_path.name)
            dest_folder = out_dir_base / rel_path.parent
            dest_folder.mkdir(parents=True, exist_ok=True)

            stem = file_path.stem
            new_stem = f"{prefix}{stem}{postfix}"
            original_ext = file_path.suffix
            
            if convert_h264: final_ext = ".mp4"
            else: final_ext = original_ext
            if lower_ext: final_ext = final_ext.lower()

            output_file = dest_folder / f"{new_stem}{final_ext}"

            # --- FFmpeg Filters ---
            filters = []
            
            # 1. 銳利化
            if luma_amount > 0:
                filters.append(f"unsharp=luma_msize_x={luma_m_size}:luma_msize_y={luma_m_size}:luma_amount={luma_amount}")
            
            # 2. 縮放邏輯
            if scale_mode == 'ratio':
                if scale_value != 1.0:
                    filters.append(f"scale=iw*{scale_value}:-2")
            elif scale_mode in ['hd1080', 'hd720', 'hd480']:
                target_px = 1080
                if scale_mode == 'hd720': target_px = 720
                elif scale_mode == 'hd480': target_px = 480
                
                scale_filter = f"scale='if(lt(iw,ih),{target_px},-2)':'if(lt(iw,ih),-2,{target_px})'"
                filters.append(scale_filter)

            filter_str = ",".join(filters)

            cmd = ["ffmpeg", "-y", "-i", str(file_path)]
            
            # --- 編碼設定 ---
            if filters or convert_h264 or final_ext != original_ext or remove_metadata or author or description:
                cmd.extend(["-c:v", "libx264", "-crf", "23", "-preset", "medium"])
                if filter_str: cmd.extend(["-vf", filter_str])
            else:
                cmd.extend(["-c:v", "copy"]) 
            
            cmd.extend(["-c:a", "copy"])

            # --- Metadata 處理 ---
            if remove_metadata:
                cmd.extend(["-map_metadata", "-1"]) 
            
            if author:
                cmd.extend(["-metadata", f"artist={author}"])
                cmd.extend(["-metadata", f"author={author}"])
            if description:
                cmd.extend(["-metadata", f"comment={description}"])
                cmd.extend(["-metadata", f"description={description}"])

            cmd.append(str(output_file))

            # 執行
            process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
            current_file_duration = file_durations.get(str(file_path), 1.0)

            for line in process.stderr:
                match = time_pattern.search(line)
                if match:
                    h, m, s = map(float, match.groups())
                    processed_sec = h * 3600 + m * 60 + s
                    
                    file_pct = int((processed_sec / current_file_duration) * 100)
                    file_progress_callback(min(file_pct, 99))
                    
                    total_processed = accumulated_duration + processed_sec
                    total_pct = int((total_processed / total_batch_duration) * 100)
                    progress_callback(min(total_pct, 99))
            
            process.wait()

            if process.returncode == 0:
                file_progress_callback(100)
                log_callback(f"    ✅ 完成")
                if delete_original:
                    if file_path.absolute() != output_file.absolute():
                        try:
                            os.remove(file_path)
                            log_callback(f"    🗑️ 刪除原始檔")
                        except: pass
            else:
                log_callback(f"    ❌ 失敗 (Code: {process.returncode})")

            accumulated_duration += current_file_duration

        except Exception as e:
            log_callback(f"❌ 程式錯誤 {file_path.name}: {str(e)}")

    progress_callback(100)
    current_file_callback("全部完成")
    file_progress_callback(100)
    log_callback("🏁 影片處理結束")

# -----------------------------------------------------------------------------
# 任務 3: 修改檔名前後綴
# -----------------------------------------------------------------------------
def task_rename_replace(log_callback, progress_callback, current_file_callback, file_progress_callback,
                        input_path, recursive, 
                        do_prefix, old_prefix, new_prefix,
                        do_suffix, old_suffix, new_suffix):
    
    log_callback("🚀 [Rename] 開始修改前後綴")
    files = get_files(input_path, recursive, file_types='all')
    total = len(files)
    count = 0
    
    for i, file_path in enumerate(files):
        pct = int(((i) / total) * 100)
        progress_callback(pct)
        current_file_callback(file_path.name)
        file_progress_callback(50) 
        
        try:
            parent = file_path.parent
            stem = file_path.stem
            suffix = file_path.suffix
            new_stem = stem
            
            if do_prefix and old_prefix in new_stem:
                if new_stem.startswith(old_prefix):
                    new_stem = new_prefix + new_stem[len(old_prefix):]
            
            if do_suffix and old_suffix in new_stem:
                if new_stem.endswith(old_suffix):
                    new_stem = new_stem[:-len(old_suffix)] + new_suffix
            
            if new_stem != stem:
                new_filename = f"{new_stem}{suffix}"
                new_path = parent / new_filename
                if not new_path.exists():
                    file_path.rename(new_path)
                    log_callback(f"✏️ [{i+1}/{total}] 更名: {file_path.name} -> {new_filename}")
                    count += 1
                else:
                    log_callback(f"⚠️ [{i+1}/{total}] 跳過: {new_filename}")
            file_progress_callback(100)
            
        except Exception as e:
            log_callback(f"❌ 錯誤 {file_path.name}: {e}")
            
    progress_callback(100)
    current_file_callback("全部完成")
    file_progress_callback(100)
    log_callback(f"🏁 更名結束，共修改 {count} 個檔案")

# -----------------------------------------------------------------------------
# 任務 4: 多尺寸生成
# -----------------------------------------------------------------------------
def task_multi_res(log_callback, progress_callback, current_file_callback, file_progress_callback,
                   input_path, output_path, recursive, lower_ext, orientation):
    log_callback(f"🚀 [Multi-Res] 開始生成多尺寸")
    target_sizes = [1024, 512, 256, 128, 64, 32]
    files = get_files(input_path, recursive, file_types='image')
    total = len(files)
    out_dir_base = Path(output_path)
    
    for i, file_path in enumerate(files):
        pct = int(((i) / total) * 100)
        progress_callback(pct)
        current_file_callback(file_path.name)
        file_progress_callback(0)
        
        try:
            log_callback(f"[{i+1}/{total}] 生成多尺寸: {file_path.name}")
            with Image.open(file_path) as img:
                w, h = img.size
                ref_size = w if orientation == 'h' else h
                
                if Path(input_path).is_dir(): rel_path = file_path.relative_to(Path(input_path))
                else: rel_path = Path(file_path.name)
                
                parent = (out_dir_base / rel_path).parent
                parent.mkdir(parents=True, exist_ok=True)
                
                base = file_path.stem
                ext = file_path.suffix.lower() if lower_ext else file_path.suffix
                
                for idx, size in enumerate(target_sizes):
                    if ref_size >= size:
                        if orientation == 'h': ratio = size / w; new_w, new_h = size, int(h * ratio)
                        else: ratio = size / h; new_w, new_h = int(w * ratio), size
                        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        resized_img.save(parent / f"{base}-{size}{ext}", quality=90)
                    file_prog = int(((idx + 1) / 6) * 100)
                    file_progress_callback(file_prog)
        except Exception as e:
            log_callback(f"❌ 錯誤 {file_path.name}: {e}")
            
    progress_callback(100)
    current_file_callback("全部完成")
    file_progress_callback(100)
    log_callback("🏁 多尺寸任務結束")