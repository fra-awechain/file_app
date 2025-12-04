import os
import subprocess
import json
import re
from pathlib import Path
from PIL import Image, ImageEnhance, ImageChops
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
# 核心邏輯：計算顏色匹配遮罩
# -----------------------------------------------------------------------------
def get_color_match_mask(img_rgba, target_color_hex, tolerance=0):
    """
    建立一個遮罩，其中與 target_color_hex 匹配的像素為白(255)，其餘為黑(0)。
    tolerance 暫時不實作複雜計算，使用精確匹配。
    """
    try:
        # 將 Hex 轉為 RGB tuple
        c = target_color_hex.lstrip('#')
        rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        
        # 建立純色圖
        target_img = Image.new('RGB', img_rgba.size, rgb)
        
        # 轉換來源圖為 RGB 進行比較 (忽略 Alpha)
        src_rgb = img_rgba.convert('RGB')
        
        # 計算差異
        diff = ImageChops.difference(src_rgb, target_img)
        
        # 轉換為灰階
        diff = diff.convert('L')
        
        # 差異為 0 (全黑) 的地方就是顏色匹配的地方
        # 我們需要反轉它，讓匹配的地方變白 (255)
        # point: x==0 -> 255, else 0
        mask = diff.point(lambda x: 255 if x <= tolerance else 0)
        return mask
    except:
        return Image.new('L', img_rgba.size, 0)

# -----------------------------------------------------------------------------
# 核心邏輯：單張圖片分區填色處理
# -----------------------------------------------------------------------------
import os
import subprocess
import json
import re
from pathlib import Path
from PIL import Image, ImageEnhance, ImageChops
from app.utils import get_files, is_ffmpeg_installed, get_video_duration

# -----------------------------------------------------------------------------
# Helper: 取得媒體資訊 (維持原樣，省略部分以節省篇幅，請保留您原本的代碼)
# -----------------------------------------------------------------------------
def get_media_info(file_path):
    # ... (請保留您原本的 get_media_info 代碼) ...
    return "Media Info Placeholder" 

# -----------------------------------------------------------------------------
# 核心邏輯：計算顏色匹配遮罩 (New)
# -----------------------------------------------------------------------------
def get_color_match_mask(img_rgba, target_color_hex, tolerance=0):
    """
    建立一個遮罩，其中與 target_color_hex 匹配的像素為白(255)，其餘為黑(0)。
    Tolerance 暫時使用簡易距離計算。
    """
    try:
        c = target_color_hex.lstrip('#')
        rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        
        # 建立純色圖
        target_img = Image.new('RGB', img_rgba.size, rgb)
        src_rgb = img_rgba.convert('RGB')
        
        # 計算差異
        diff = ImageChops.difference(src_rgb, target_img)
        diff = diff.convert('L')
        
        # 差異越小越黑(0)。我們需要反轉：差異小 -> 白(255)
        # Tolerance: 0-100% maps to threshold
        threshold = int(tolerance * 2.55) # 簡單估算
        
        # 如果像素值 < threshold，設為 255 (選中)，否則 0
        mask = diff.point(lambda x: 255 if x <= threshold else 0)
        return mask
    except Exception as e:
        print(f"Color Mask Error: {e}")
        return Image.new('L', img_rgba.size, 0)

# -----------------------------------------------------------------------------
# 核心邏輯：單張圖片分區填色處理 (Updated)
# -----------------------------------------------------------------------------
def process_single_image_fill(img, settings_opaque, settings_trans, settings_semi):
    """
    img: PIL Image (Expected RGBA)
    settings_*: dict {
        'target_mode': 'all' | 'specific' | 'non_specific',
        'target_color': str (hex),
        'trans_mode': 'maintain' | 'change',
        'trans_val': int,
        'fill_mode': 'maintain' | 'color' | 'image',
        'fill_color': str,
        'fill_image_path': str,
        'fill_image_scale': float
    }
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    r, g, b, a = img.split()
    
    # 1. 建立基礎 Alpha 區域遮罩
    # 不透明: Alpha = 255
    mask_opaque_alpha = a.point(lambda x: 255 if x == 255 else 0, mode='L')
    # 透明: Alpha = 0
    mask_trans_alpha = a.point(lambda x: 255 if x == 0 else 0, mode='L')
    # 半透明: 0 < Alpha < 255 (其餘部分)
    mask_others = ImageChops.add(mask_opaque_alpha, mask_trans_alpha)
    mask_semi_alpha = ImageChops.invert(mask_others)

    final_img = img.copy()

    def process_region(base_img, region_alpha_mask, settings):
        if not settings: return base_img
        
        # 如果該區域本身就沒有任何像素，直接返回
        if region_alpha_mask.getbbox() is None:
            return base_img

        # --- A. 計算最終作用遮罩 (Final Mask) ---
        target_mode = settings.get('target_mode', 'all')
        final_mask = region_alpha_mask
        
        if target_mode in ['specific', 'non_specific']:
            target_color = settings.get('target_color', '#FFFFFF')
            # 在該區域範圍內，找出符合顏色的像素
            # 注意：這裡只比對顏色(RGB)，Alpha 已經由 region_alpha_mask 決定
            color_mask = get_color_match_mask(base_img, target_color, tolerance=10) # 預設一點容許值
            
            if target_mode == 'specific':
                # 交集: 既在該 Alpha 區間，又是該顏色
                final_mask = ImageChops.multiply(region_alpha_mask, color_mask)
            elif target_mode == 'non_specific':
                # 交集: 既在該 Alpha 區間，又"不是"該顏色
                inv_color_mask = ImageChops.invert(color_mask)
                final_mask = ImageChops.multiply(region_alpha_mask, inv_color_mask)
        
        # 再次檢查是否有需要處理的像素
        if final_mask.getbbox() is None:
            return base_img

        # --- B. 填充內容 (Color / Image) ---
        fill_layer = None
        fill_mode = settings.get('fill_mode', 'maintain')
        width, height = base_img.size
        
        if fill_mode == 'color':
            c_val = settings.get('fill_color', '#FFFFFF')
            # 建立純色層
            fill_layer = Image.new('RGBA', (width, height), c_val)
        
        elif fill_mode == 'image':
            path = settings.get('fill_image_path')
            if path and os.path.exists(path):
                try:
                    tex = Image.open(path).convert('RGBA')
                    scale = settings.get('fill_image_scale', 100) / 100.0
                    if scale <= 0: scale = 0.01
                    new_w = int(tex.width * scale)
                    new_h = int(tex.height * scale)
                    tex = tex.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    
                    # Tiling
                    tiled = Image.new('RGBA', (width, height))
                    for x in range(0, width, new_w):
                        for y in range(0, height, new_h):
                            tiled.paste(tex, (x, y))
                    fill_layer = tiled
                except: pass

        # 應用填充
        if fill_layer:
            # 只有在 final_mask 為白色的地方，才使用 fill_layer，其餘維持 base_img
            base_img = Image.composite(fill_layer, base_img, final_mask)

        # --- C. 透明度處理 ---
        # 注意：透明度改變也只應作用在 final_mask 選中的區域
        trans_mode = settings.get('trans_mode', 'maintain')
        if trans_mode == 'change':
            val = settings.get('trans_val', 255)
            # 這裡 val 是 0(透明) - 100(不透明)，需轉換為 0-255
            # UI Slider 0=Transparent, 100=Opaque -> 邏輯似乎是 0-100
            # 假設 settings 傳入的是 0-100
            target_alpha_val = int((val / 100.0) * 255)
            
            # 建立全圖目標 Alpha 層
            target_alpha_plane = Image.new('L', (width, height), target_alpha_val)
            
            curr_r, curr_g, curr_b, curr_a = base_img.split()
            
            # 僅在 final_mask 範圍內應用新的 Alpha，其餘保持原 Alpha
            new_a = Image.composite(target_alpha_plane, curr_a, final_mask)
            
            base_img = Image.merge('RGBA', (curr_r, curr_g, curr_b, new_a))

        return base_img

    # 依序處理三個區塊
    final_img = process_region(final_img, mask_opaque_alpha, settings_opaque)
    final_img = process_region(final_img, mask_trans_alpha, settings_trans)
    final_img = process_region(final_img, mask_semi_alpha, settings_semi)

    return final_img

# (其餘 task_scaling, task_rename 等函式請保留您原本的，這裡只列出 task_image_fill 的更新)

def task_image_fill(log_callback, progress_callback, current_file_callback, file_progress_callback,
                    input_path, output_path, recursive,
                    settings_opaque, settings_trans, settings_semi,
                    delete_original, output_format):
    
    log_callback("🚀 [Image Fill] 開始填色處理")
    
    # 支援所有 Image 格式 (Pillow 支援的)
    files = get_files(input_path, recursive, file_types='image')
    total = len(files)
    
    if total == 0:
        log_callback("⚠️ 未找到任何圖片")
        return

    out_dir_base = Path(output_path)
    if not out_dir_base.exists():
        out_dir_base.mkdir(parents=True, exist_ok=True)

    # 處理輸出格式
    ext_map = {'jpg': '.jpg', 'jpeg': '.jpg', 'png': '.png', 'webp': '.webp'}
    target_ext = ext_map.get(output_format.lower(), '.png')

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
            
            output_file = dest_folder / f"{file_path.stem}{target_ext}"

            with Image.open(file_path) as img:
                processed_img = process_single_image_fill(img, settings_opaque, settings_trans, settings_semi)
                
                # 儲存設定
                save_fmt = output_format.upper()
                if save_fmt in ['JPG', 'JPEG']:
                    # JPG 不支援透明，轉白底
                    if processed_img.mode == 'RGBA':
                        bg = Image.new("RGB", processed_img.size, (255, 255, 255))
                        bg.paste(processed_img, mask=processed_img.split()[3])
                        processed_img = bg
                    else:
                        processed_img = processed_img.convert("RGB")
                    save_fmt = 'JPEG'

                processed_img.save(output_file, format=save_fmt, quality=95)
                log_callback(f"🎨 [{i+1}/{total}] 完成: {output_file.name}")

            # 刪除原始檔邏輯
            if delete_original:
                # 確保不是同一個檔案才刪 (雖然副檔名可能變了，但路徑檢查一下)
                if file_path.resolve() != output_file.resolve():
                    try:
                        os.remove(file_path)
                        log_callback(f"    🗑️ 已刪除原始檔")
                    except Exception as del_err:
                        log_callback(f"    ⚠️ 刪除失敗: {del_err}")
            
            file_progress_callback(100)

        except Exception as e:
            log_callback(f"❌ 失敗 {file_path.name}: {str(e)}")

    progress_callback(100)
    current_file_callback("全部完成")
    file_progress_callback(100)
    log_callback("🏁 圖片填色處理結束")

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
                if remove_metadata:
                    img.info.clear() 

                if final_ext.lower() in ['.jpg', '.jpeg']:
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img = img.convert('RGBA')
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

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

                w, h = img.size
                new_w, new_h = w, h
                should_resize = False

                if mode == 'ratio':
                    ratio = mode_value_1
                    if ratio != 1.0:
                        new_w = int(w * ratio); new_h = int(h * ratio); should_resize = True
                
                elif mode == 'width':
                    target_w = int(mode_value_1)
                    if target_w > 0:
                        ratio = target_w / w
                        new_w = target_w
                        new_h = int(h * ratio)
                        should_resize = True
                
                elif mode == 'height':
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

                if sharpen_factor != 1.0:
                    img = ImageEnhance.Sharpness(img).enhance(sharpen_factor)
                if brightness_factor != 1.0:
                    img = ImageEnhance.Brightness(img).enhance(brightness_factor)

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
# 任務 2: 影片銳利化
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

            filters = []
            if luma_amount > 0:
                filters.append(f"unsharp=luma_msize_x={luma_m_size}:luma_msize_y={luma_m_size}:luma_amount={luma_amount}")
            
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
            
            if filters or convert_h264 or final_ext != original_ext or remove_metadata or author or description:
                cmd.extend(["-c:v", "libx264", "-crf", "23", "-preset", "medium"])
                if filter_str: cmd.extend(["-vf", filter_str])
            else:
                cmd.extend(["-c:v", "copy"]) 
            
            cmd.extend(["-c:a", "copy"])

            if remove_metadata:
                cmd.extend(["-map_metadata", "-1"]) 
            
            if author:
                cmd.extend(["-metadata", f"artist={author}"])
                cmd.extend(["-metadata", f"author={author}"])
            if description:
                cmd.extend(["-metadata", f"comment={description}"])
                cmd.extend(["-metadata", f"description={description}"])

            cmd.append(str(output_file))

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

# -----------------------------------------------------------------------------
# 任務 5: 圖片填色 (Image Fill)
# -----------------------------------------------------------------------------
def task_image_fill(log_callback, progress_callback, current_file_callback, file_progress_callback,
                    input_path, output_path, recursive,
                    settings_opaque, settings_trans, settings_semi,
                    delete_original, output_format):
    
    log_callback("🚀 [Image Fill] 開始填色處理")
    
    # 支援所有 Image 格式
    files = get_files(input_path, recursive, file_types='image')
    total = len(files)
    
    if total == 0:
        log_callback("⚠️ 未找到任何圖片")
        return

    out_dir_base = Path(output_path)
    if not out_dir_base.exists():
        out_dir_base.mkdir(parents=True, exist_ok=True)

    target_ext = f".{output_format}" # .jpg, .png, .webp

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
            
            # 決定輸出檔名
            output_file = dest_folder / f"{file_path.stem}{target_ext}"

            with Image.open(file_path) as img:
                processed_img = process_single_image_fill(img, settings_opaque, settings_trans, settings_semi)
                
                # 格式處理
                save_fmt = output_format.upper()
                if save_fmt == 'JPG' or save_fmt == 'JPEG':
                    # JPG 不支援透明，需轉 RGB (補白底)
                    bg = Image.new("RGB", processed_img.size, (255, 255, 255))
                    bg.paste(processed_img, mask=processed_img.split()[3] if processed_img.mode=='RGBA' else None)
                    processed_img = bg
                    save_fmt = 'JPEG'

                processed_img.save(output_file, format=save_fmt)
                log_callback(f"🎨 [{i+1}/{total}] 處理: {file_path.name} -> {output_file.name}")

            # 刪除原始檔
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
    log_callback("🏁 圖片填色處理結束")