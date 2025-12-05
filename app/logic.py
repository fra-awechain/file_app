import os
import math
import random
import subprocess
import json
import re
from pathlib import Path
from PIL import Image, ImageEnhance, ImageChops, ImageDraw, ImageOps
from app.utils import get_files, is_ffmpeg_installed, get_video_duration

# -----------------------------------------------------------------------------
# Helper: 取得媒體資訊
# -----------------------------------------------------------------------------
def get_media_info(file_path):
    path = Path(file_path); ext = path.suffix.lower(); info_str = f"檔案: {path.name}\n"
    try:
        if ext in ['.jpg','.jpeg','.png','.webp','.tiff','.bmp']:
            with Image.open(path) as img:
                info_str += f"格式: {img.format}\n尺寸: {img.size}\n模式: {img.mode}\n"
                if img.info: info_str += "\n[Info]\n" + "\n".join([f"{k}: {v}" for k,v in img.info.items() if isinstance(v,(str,int,float))])
        elif ext in ['.mp4','.mov','.avi','.mkv'] and is_ffmpeg_installed():
            cmd = ["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",str(path)]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if res.returncode==0:
                d = json.loads(res.stdout); fmt = d.get('format',{})
                info_str += f"時長: {fmt.get('duration','N/A')}s\n"
                for s in d.get('streams',[]): 
                    if s.get('codec_type')=='video': info_str+=f"Res: {s.get('width')}x{s.get('height')}\n"
    except Exception as e: info_str += f"\nError: {e}"
    return info_str

# -----------------------------------------------------------------------------
# 幾何圖形與漸層
# -----------------------------------------------------------------------------
def create_shape_mask(size, shape_type, custom_shape_path=None):
    w, h = size; mask = Image.new('L', size, 0); draw = ImageDraw.Draw(mask); cx, cy = w/2, h/2; r = min(w,h)/2
    def poly(n, rot=0, sharp=False, inner=0.5):
        pts = []; step = (2*math.pi)/n; start = -math.pi/2 + math.radians(rot); tot = n*2 if sharp else n; st = math.pi/n if sharp else step
        for i in range(tot):
            a = start + i*st; cr = r if (not sharp or i%2==0) else r*inner
            pts.append((cx + cr*math.cos(a), cy + cr*math.sin(a)))
        return pts
    if shape_type == '圓形': draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=255)
    elif shape_type == '水平橢圓形': draw.ellipse((0, h*0.1, w, h*0.9), fill=255)
    elif shape_type == '垂直橢圓形': draw.ellipse((w*0.1, 0, w*0.9, h), fill=255)
    elif shape_type == '正三角形': draw.polygon(poly(3), fill=255)
    elif shape_type == '正方形': d = r*math.sqrt(2); draw.rectangle((cx-d/2, cy-d/2, cx+d/2, cy+d/2), fill=255)
    elif shape_type == '正五邊形': draw.polygon(poly(5), fill=255)
    elif shape_type == '正六邊形': draw.polygon(poly(6), fill=255)
    elif '星形' in shape_type:
        n = 4 if '四角' in shape_type else 5; inner = 0.4 if '銳角' in shape_type else 0.6
        draw.polygon(poly(n, sharp=True, inner_r_factor=inner), fill=255)
    elif '隨機雲狀' in shape_type:
        lc = (shape_type == '隨機雲狀(在圓形內)'); nb = 15
        for _ in range(nb):
            if lc: a=random.random()*2*math.pi; d=random.random()*(r*0.6); bx=cx+d*math.cos(a); by=cy+d*math.sin(a); br=random.uniform(r*0.2,r*0.4)
            else: bx=random.uniform(w*0.2,w*0.8); by=random.uniform(h*0.2,h*0.8); br=random.uniform(min(w,h)*0.15,min(w,h)*0.3)
            draw.ellipse((bx-br, by-br, bx+br, by+br), fill=255)
    elif shape_type == '上傳自定義圖片形狀' and custom_shape_path:
        try: mask = Image.open(custom_shape_path).convert('RGBA').resize((w, h), Image.Resampling.LANCZOS).split()[3]
        except: pass
    return mask

def create_gradient_image(size, c1, c2, direction, angle_deg=0):
    w, h = size; base = Image.new('RGBA', (w, h), c1); top = Image.new('RGBA', (w, h), c2); mask = Image.new('L', (w, h)); draw = ImageDraw.Draw(mask)
    if direction == '水平': 
        for x in range(w): draw.line([(x, 0), (x, h)], fill=int(255 * x / w) if w else 0)
    elif direction == '垂直': 
        for y in range(h): draw.line([(0, y), (w, y)], fill=int(255 * y / h) if h else 0)
    elif direction == '角度':
        d = int(math.sqrt(w**2 + h**2)); gs = Image.new('L', (d, d)); gd = ImageDraw.Draw(gs)
        for x in range(d): gd.line([(x, 0), (x, d)], fill=int(255 * x / d))
        mask = gs.rotate(-angle_deg, resample=Image.Resampling.BICUBIC).crop(((d-w)//2, (d-h)//2, (d-w)//2+w, (d-h)//2+h))
    return Image.composite(top, base, mask)

def get_color_match_mask(img_rgba, target_color_hex, tolerance=40): # Tolerance 提高到 40
    try:
        c = target_color_hex.lstrip('#')
        tr, tg, tb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        
        # 使用 Pixel Access 來做精確且寬容的匹配 (比 ImageChops 更可控)
        # 注意：這比 C 語言層級的 ImageChops 慢，但在 Python 中要處理 "距離" 這是比較直觀的方法
        # 若要效能，可回退到 ImageChops.difference 但需接受誤差
        
        # 效能優化版：使用 ImageChops 但分通道計算
        r, g, b, a = img_rgba.split()
        target_r = Image.new('L', img_rgba.size, tr)
        target_g = Image.new('L', img_rgba.size, tg)
        target_b = Image.new('L', img_rgba.size, tb)
        
        diff_r = ImageChops.difference(r, target_r)
        diff_g = ImageChops.difference(g, target_g)
        diff_b = ImageChops.difference(b, target_b)
        
        # 疊加差異
        diff = ImageChops.add(diff_r, diff_g)
        diff = ImageChops.add(diff, diff_b)
        
        # diff 越小越接近，將小於 tolerance 的部分設為 255 (白)
        # ImageChops.difference 的結果已經是絕對值
        # 總差異閾值：RGB 三通道差異總和。Tolerance 40 代表平均每通道容許約 13 的差異
        threshold = tolerance * 3 
        
        return diff.point(lambda x: 255 if x <= threshold else 0)
        
    except Exception as e:
        print(f"Mask Error: {e}")
        return Image.new('L', img_rgba.size, 0)

# -----------------------------------------------------------------------------
# 核心邏輯
# -----------------------------------------------------------------------------
def process_single_image_fill(img, settings_opaque, settings_trans, settings_semi, bg_settings=None, crop_settings=None):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    width, height = img.size
    
    r, g, b, a = img.split()
    # 嚴格區分 Alpha 區域
    mask_opaque_alpha = a.point(lambda x: 255 if x >= 250 else 0, mode='L') 
    mask_trans_alpha = a.point(lambda x: 255 if x <= 10 else 0, mode='L')
    mask_others = ImageChops.add(mask_opaque_alpha, mask_trans_alpha)
    mask_semi_alpha = ImageChops.invert(mask_others)

    final_img = img.copy()

    def process_region(base_img, region_alpha_mask, settings):
        if not settings or region_alpha_mask.getbbox() is None: return base_img
        
        # 注意這裡：target_mode 來自 UI 傳入的字串
        target_mode = settings.get('target_mode', 'all')
        final_mask = region_alpha_mask
        
        # 指定色值處理
        if target_mode in ['specific', 'non_specific']:
            t_color = settings.get('target_color', '#FFFFFF')
            # 這裡傳入的是 base_img (尚未被修改的原始圖層)
            color_match_mask = get_color_match_mask(base_img, t_color, tolerance=40)
            
            if target_mode == 'specific':
                # 交集：必須是 (指定區域 AND 顏色匹配)
                final_mask = ImageChops.multiply(region_alpha_mask, color_match_mask)
            else:
                # 差集：必須是 (指定區域 AND NOT 顏色匹配)
                inv_color = ImageChops.invert(color_match_mask)
                final_mask = ImageChops.multiply(region_alpha_mask, inv_color)
        
        if final_mask.getbbox() is None: return base_img

        fill_mode = settings.get('fill_mode', 'maintain')
        fill_layer = None
        
        if fill_mode == 'color':
            fill_layer = Image.new('RGBA', (width, height), settings.get('fill_color', '#FFFFFF'))
        elif fill_mode == 'gradient':
            gs = settings.get('fill_gradient', {})
            fill_layer = create_gradient_image((width, height), gs.get('start','#000'), gs.get('end','#FFF'), gs.get('dir','水平'), gs.get('angle',0))
        elif fill_mode == 'image':
            path = settings.get('fill_image_path')
            if path and os.path.exists(path):
                try:
                    tex = Image.open(path).convert('RGBA')
                    tf = settings.get('fill_image_transform', {})
                    s = tf.get('scale', 100)/100.0; ang = tf.get('angle', 0); dx, dy = tf.get('dx', 0), tf.get('dy', 0)
                    nw, nh = max(1, int(tex.width*s)), max(1, int(tex.height*s))
                    tex = tex.resize((nw, nh), Image.Resampling.LANCZOS).rotate(-ang, expand=True, resample=Image.Resampling.BICUBIC)
                    tiled = Image.new('RGBA', (width, height))
                    for x in range(int(dx), width, nw):
                        for y in range(int(dy), height, nh): tiled.paste(tex, (x, y), tex)
                    fill_layer = tiled
                except: pass

        if fill_layer:
            base_img = Image.composite(fill_layer, base_img, final_mask)

        if settings.get('trans_mode') == 'change':
            val = settings.get('trans_val', 255)
            ta = Image.new('L', (width, height), int((val/100)*255))
            curr_r, curr_g, curr_b, curr_a = base_img.split()
            new_a = Image.composite(ta, curr_a, final_mask)
            base_img = Image.merge('RGBA', (curr_r, curr_g, curr_b, new_a))

        return base_img

    # 依序處理
    final_img = process_region(final_img, mask_opaque_alpha, settings_opaque)
    final_img = process_region(final_img, mask_trans_alpha, settings_trans)
    final_img = process_region(final_img, mask_semi_alpha, settings_semi)

    # Crop & BG Logic (同前)
    if crop_settings:
        s = crop_settings.get('shape', '無')
        if s and s != '無':
            sm = create_shape_mask((width, height), s, crop_settings.get('custom_path'))
            final_img.putalpha(ImageChops.multiply(final_img.split()[3], sm))

    if crop_settings and crop_settings.get('trim_enabled'):
        tm = crop_settings.get('trim_mode', 'alpha')
        bbox = None
        if tm == 'alpha': bbox = final_img.getbbox()
        elif tm == 'color':
            bbox = get_color_match_mask(final_img, crop_settings.get('trim_color', '#FFFFFF'), 20).getbbox()
        if bbox: final_img = final_img.crop(bbox); width, height = final_img.size

    if bg_settings and bg_settings.get('enabled'):
        bl = None; bt = bg_settings.get('type', 'color')
        if bt == 'color': bl = Image.new('RGBA', (width, height), bg_settings.get('color', '#FFFFFF'))
        elif bt == 'gradient': bl = create_gradient_image((width, height), bg_settings.get('grad_start','#000'), bg_settings.get('grad_end','#FFF'), bg_settings.get('grad_dir','水平'), bg_settings.get('grad_angle',0))
        elif bt == 'image':
            p = bg_settings.get('image_path')
            if p and os.path.exists(p):
                bi = Image.open(p).convert('RGBA')
                tf = bg_settings.get('image_transform', {})
                s=tf.get('scale',100)/100.0; ang=tf.get('angle',0); dx,dy=tf.get('dx',0),tf.get('dy',0)
                nw, nh = max(1, int(bi.width*s)), max(1, int(bi.height*s))
                bi = bi.resize((nw, nh), Image.Resampling.LANCZOS).rotate(-ang, expand=True)
                bl = Image.new('RGBA', (width, height), (0,0,0,0))
                bl.paste(bi, ((width-bi.width)//2+int(dx), (height-bi.height)//2+int(dy)))

        if bl:
            cm = bg_settings.get('mode', 'overlay')
            if cm == 'overlay': bl.paste(final_img, (0, 0), final_img); final_img = bl
            elif cm == 'background_cutout':
                mk = final_img.split()[3]; tr = Image.new('RGBA', (width, height), (0,0,0,0))
                final_img = Image.composite(tr, bl, mk)

    return final_img

def task_image_fill(log_callback, progress_callback, current_file_callback, file_progress_callback,
                    input_path, output_path, recursive,
                    settings_opaque, settings_trans, settings_semi,
                    bg_settings, crop_settings,
                    delete_original, output_format):
    log_callback("🚀 [Image Fill] 開始")
    files = get_files(input_path, recursive, file_types='image')
    total = len(files)
    if total == 0: log_callback("⚠️ 無圖片"); return

    out_base = Path(output_path)
    if not out_base.exists(): out_base.mkdir(parents=True, exist_ok=True)
    ext_map = {'jpg':'.jpg','jpeg':'.jpg','png':'.png','webp':'.webp'}
    tgt_ext = ext_map.get(output_format.lower(), '.png')

    for i, fp in enumerate(files):
        try:
            progress_callback(int((i/total)*100)); current_file_callback(fp.name); file_progress_callback(0)
            rel = fp.relative_to(Path(input_path)) if Path(input_path).is_dir() else Path(fp.name)
            dest = out_base / rel.parent; dest.mkdir(parents=True, exist_ok=True)
            out_file = dest / f"{fp.stem}{tgt_ext}"

            with Image.open(fp) as img:
                res = process_single_image_fill(img, settings_opaque, settings_trans, settings_semi, bg_settings, crop_settings)
                fmt = output_format.upper()
                if fmt in ['JPG','JPEG']:
                    if res.mode == 'RGBA':
                        bg = Image.new("RGB", res.size, (255,255,255))
                        bg.paste(res, mask=res.split()[3])
                        res = bg
                    else: res = res.convert("RGB")
                    fmt = 'JPEG'
                res.save(out_file, format=fmt, quality=95)
                log_callback(f"🎨 完成: {out_file.name}")
            
            if delete_original and fp.resolve() != out_file.resolve(): os.remove(fp)
            file_progress_callback(100)
        except Exception as e: log_callback(f"❌ 失敗 {fp.name}: {e}")
            
    progress_callback(100); current_file_callback("Done"); file_progress_callback(100); log_callback("🏁 結束")

def task_scaling(*args, **kwargs): pass 
def task_video_sharpen(*args, **kwargs): pass 
def task_rename_replace(*args, **kwargs): pass 
def task_multi_res(*args, **kwargs): pass