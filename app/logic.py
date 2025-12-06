import os
import math
import random
import subprocess
import json
import re
from pathlib import Path
from PIL import Image, ImageEnhance, ImageChops, ImageDraw
from app.utils import get_files, is_ffmpeg_installed, get_video_duration

def create_shape_mask(size, shape_type):
    w, h = size; mask = Image.new('L', size, 0); draw = ImageDraw.Draw(mask); cx, cy = w/2, h/2; r = min(w, h)/2
    def get_poly_points(n, rotation=0, sharp=False, inner_factor=0.5):
        points = []; step = (2*math.pi)/n; start = -math.pi/2+math.radians(rotation)
        for i in range(n*2 if sharp else n):
            curr_r = r * (inner_factor if sharp and i%2!=0 else 1)
            angle = start + i * (math.pi/n if sharp else step)
            points.append((cx+curr_r*math.cos(angle), cy+curr_r*math.sin(angle)))
        return points
    if shape_type == '圓形': draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=255)
    elif shape_type == '正方形': d = r*math.sqrt(2); draw.rectangle((cx-d/2, cy-d/2, cx+d/2, cy+d/2), fill=255)
    elif shape_type == '正三角形': draw.polygon(get_poly_points(3), fill=255)
    elif shape_type == '正五邊形': draw.polygon(get_poly_points(5), fill=255)
    elif shape_type == '正六邊形': draw.polygon(get_poly_points(6), fill=255)
    elif '星形' in shape_type: 
        n = 4 if '四角' in shape_type else 5; inner = 0.2 if '尖角' in shape_type else 0.5
        draw.polygon(get_poly_points(n, sharp=True, inner_factor=inner), fill=255)
    elif '隨機雲狀' in shape_type:
        for _ in range(15):
            bx, by = (cx, cy) if '正圓內' in shape_type else (random.uniform(w*0.2,w*0.8), random.uniform(h*0.2,h*0.8))
            dist = random.uniform(0, r*0.8) if '正圓內' in shape_type else 0; ang = random.random()*6.28
            if '正圓內' in shape_type: bx += dist*math.cos(ang); by += dist*math.sin(ang)
            draw.ellipse((bx-r*0.2, by-r*0.2, bx+r*0.2, by+r*0.2), fill=255)
    return mask

def create_gradient_image(size, start_hex, end_hex, angle):
    w, h = size; diag = int(math.sqrt(w**2+h**2))
    base = Image.new('RGBA', (diag, diag), start_hex); top = Image.new('RGBA', (diag, diag), end_hex)
    mask = Image.new('L', (diag, diag)); draw = ImageDraw.Draw(mask)
    for y in range(diag): draw.line([(0, y), (diag, y)], fill=int(255 * (y/diag)))
    return Image.composite(top, base, mask.rotate(angle)).crop(((diag-w)//2, (diag-h)//2, (diag-w)//2+w, (diag-h)//2+h))

def get_color_match_mask(img_rgba, target_color_hex, tolerance=40):
    try:
        c = target_color_hex.lstrip('#'); tr, tg, tb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        r, g, b, a = img_rgba.split()
        diff = ImageChops.add(ImageChops.difference(r, Image.new('L',r.size,tr)), ImageChops.add(ImageChops.difference(g, Image.new('L',g.size,tg)), ImageChops.difference(b, Image.new('L',b.size,tb))))
        return diff.point(lambda x: 255 if x <= tolerance*3 else 0)
    except: return Image.new('L', img_rgba.size, 0)

def process_single_image_fill(img, opaque_sets, trans_sets, semi_sets, bg_sets, crop_sets):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    w, h = img.size; r, g, b, a = img.split()
    mask_op = a.point(lambda x: 255 if x >= 250 else 0, 'L'); mask_tr = a.point(lambda x: 255 if x <= 10 else 0, 'L')
    mask_se = ImageChops.invert(ImageChops.add(mask_op, mask_tr))
    final = img.copy()

    def proc(base, mask, s):
        if not s or not mask.getbbox(): return base
        tm = s.get('target_mode'); fm = mask
        if tm in ['specific', 'non_specific']:
            cm = get_color_match_mask(base, s.get('target_color','#FFF'), 30)
            fm = ImageChops.multiply(mask, cm) if tm=='specific' else ImageChops.multiply(mask, ImageChops.invert(cm))
        if not fm.getbbox(): return base
        fl = None; fmod = s.get('fill_mode')
        if fmod=='color': fl = Image.new('RGBA', (w,h), s.get('fill_color'))
        elif fmod=='gradient': fl = create_gradient_image((w,h), s.get('fill_gradient',{}).get('start'), s.get('fill_gradient',{}).get('end'), s.get('fill_gradient',{}).get('angle',0))
        elif fmod=='image' and os.path.exists(s.get('fill_image_path','')): fl = Image.open(s.get('fill_image_path')).convert('RGBA').resize((w,h))
        if fl: base = Image.composite(fl, base, fm)
        if s.get('trans_mode')=='change':
            ta = Image.new('L', (w,h), int(255*(1-s.get('trans_val',0)/100.0)))
            base.putalpha(Image.composite(ta, base.split()[3], fm))
        return base

    final = proc(final, mask_op, opaque_sets); final = proc(final, mask_tr, trans_sets); final = proc(final, mask_se, semi_sets)

    if bg_sets and bg_sets.get('enabled'):
        bg = None; bt = bg_sets.get('material_type')
        if bt=='color': bg = Image.new('RGBA', (w,h), bg_sets.get('color'))
        elif bt=='gradient': bg = create_gradient_image((w,h), bg_sets.get('gradient',{}).get('start'), bg_sets.get('gradient',{}).get('end'), bg_sets.get('gradient',{}).get('angle',0))
        elif bt=='image' and os.path.exists(bg_sets.get('image_path','')):
            bi = Image.open(bg_sets.get('image_path')).convert('RGBA').resize((w,h)); bg = Image.new('RGBA',(w,h)); bg.paste(bi)
        if bg:
            if bg_sets.get('mode')=='overlay': bg.paste(final, (0,0), final); final = bg
            elif bg_sets.get('mode')=='cutout':
                ct = bg_sets.get('cutout_target'); cm = None
                if ct=='opaque': cm = img.split()[3].point(lambda x: 255 if x>200 else 0)
                elif ct=='transparent': cm = img.split()[3].point(lambda x: 255 if x<10 else 0)
                elif ct=='color': cm = get_color_match_mask(img, bg_sets.get('cutout_color'), 30)
                if cm: fbg = Image.new('RGBA',(w,h)); fbg.paste(bg, (0,0), ImageChops.invert(cm)); final = fbg

    if crop_sets:
        if crop_sets.get('shape')!='無': final.putalpha(ImageChops.multiply(final.split()[3], create_shape_mask((w,h), crop_sets.get('shape'))))
        if crop_sets.get('trim'): final = final.crop(final.getbbox())
    return final

def task_image_fill(log_callback, progress_callback, current_file_callback, file_progress_callback, input_path, output_path, recursive, settings_opaque, settings_trans, settings_semi, bg_settings, crop_settings, delete_original, output_format):
    log_callback("🚀 [Smart Fill] 開始"); files = get_files(input_path, recursive, file_types='image'); total = len(files)
    out_base = Path(output_path); out_base.mkdir(parents=True, exist_ok=True); ext_map = {'png':'.png','jpg':'.jpg','webp':'.webp'}; tgt_ext = ext_map.get(output_format.lower(), '.png')
    for i, fp in enumerate(files):
        try:
            progress_callback(int((i/total)*100)); current_file_callback(fp.name); file_progress_callback(0)
            dest = out_base / (fp.relative_to(Path(input_path)).parent if Path(input_path).is_dir() else fp.parent.name); dest.mkdir(parents=True, exist_ok=True); out_file = dest / f"{fp.stem}{tgt_ext}"
            with Image.open(fp) as img:
                res = process_single_image_fill(img, settings_opaque, settings_trans, settings_semi, bg_settings, crop_settings)
                fmt = output_format.upper()
                if fmt == 'JPG': bg = Image.new("RGB", res.size, (255,255,255)); bg.paste(res, mask=res.split()[3]); res = bg; fmt = 'JPEG'
                res.save(out_file, format=fmt, quality=95); log_callback(f"🎨 完成: {fp.name}")
            if delete_original and fp.resolve()!=out_file.resolve(): os.remove(fp)
            file_progress_callback(100)
        except Exception as e: log_callback(f"❌ {fp.name}: {e}")
    progress_callback(100); current_file_callback("Done"); file_progress_callback(100); log_callback("🏁 結束")

def task_scaling(log_callback, progress_callback, current_file_callback, file_progress_callback, input_path, output_path, mode, mode_value_1, recursive, convert_jpg, lower_ext, delete_original, prefix, postfix, crop_doubao, sharpen_factor, brightness_factor, remove_metadata, author, description):
    log_callback(f"🚀 [Scaling] 開始"); files = get_files(input_path, recursive, file_types='image'); total = len(files); out_base = Path(output_path); out_base.mkdir(parents=True, exist_ok=True)
    for i, fp in enumerate(files):
        progress_callback(int((i/total)*100)); current_file_callback(fp.name); file_progress_callback(0)
        try:
            dest = out_base / (fp.relative_to(Path(input_path)).parent if Path(input_path).is_dir() else fp.parent.name); dest.mkdir(parents=True, exist_ok=True)
            new_name = f"{prefix}{fp.stem}{postfix}{'.jpg' if convert_jpg else fp.suffix}"; (new_name := new_name.lower()) if lower_ext else None
            with Image.open(fp) as img:
                if remove_metadata: img.info.clear()
                if convert_jpg and img.mode in ('RGBA','LA','P'): img = img.convert('RGB')
                if crop_doubao: w,h=img.size; sw,sh=w-320,h-110; img=img.crop((0,0,(sw,int(sw/r)) if int(sw/(r:=w/h))<=sh else (int(sh*r),sh)))
                w, h = img.size; nw, nh = w, h
                if mode=='ratio' and mode_value_1!=1: nw,nh = int(w*mode_value_1), int(h*mode_value_1)
                elif mode=='width' and mode_value_1>0: r=mode_value_1/w; nw,nh = int(mode_value_1), int(h*r)
                elif mode=='height' and mode_value_1>0: r=mode_value_1/h; nh,nw = int(mode_value_1), int(w*r)
                if (nw,nh)!=(w,h): img = img.resize((nw,nh), Image.Resampling.LANCZOS)
                if sharpen_factor!=1: img = ImageEnhance.Sharpness(img).enhance(sharpen_factor)
                if brightness_factor!=1: img = ImageEnhance.Brightness(img).enhance(brightness_factor)
                
                save_k = {'quality':95} if new_name.lower().endswith('.jpg') else {}
                if new_name.lower().endswith('.png'):
                    from PIL.PngImagePlugin import PngInfo; meta=PngInfo()
                    if author: meta.add_text("Artist",author); meta.add_text("Author",author)
                    if description: meta.add_text("Description",description)
                    save_k['pnginfo'] = meta
                img.save(dest/new_name, **save_k)
            if delete_original and fp.resolve()!=dest/new_name: os.remove(fp)
            file_progress_callback(100)
        except Exception as e: log_callback(f"❌ {fp.name}: {e}")
    progress_callback(100); log_callback("🏁 結束")

def task_video_sharpen(log_callback, progress_callback, current_file_callback, file_progress_callback, input_path, output_path, recursive, lower_ext, delete_original, prefix, postfix, luma_m_size, luma_amount, scale_mode, scale_value, convert_h264, remove_metadata, author, description):
    if not is_ffmpeg_installed(): log_callback("❌ 錯誤：找不到 FFmpeg"); return
    log_callback(f"🚀 [Video] 開始"); files = get_files(input_path, recursive, file_types='video'); total_dur = sum([max(get_video_duration(f), 1.0) for f in files]); out_base = Path(output_path); out_base.mkdir(parents=True, exist_ok=True); acc_dur = 0.0
    for i, fp in enumerate(files):
        try:
            current_file_callback(fp.name); rel = fp.relative_to(Path(input_path)) if Path(input_path).is_dir() else fp.name; dest = out_base / rel.parent; dest.mkdir(parents=True, exist_ok=True)
            new_stem = f"{prefix}{fp.stem}{postfix}"; final_ext = ".mp4" if convert_h264 else fp.suffix; (final_ext := final_ext.lower()) if lower_ext else None; out_file = dest / f"{new_stem}{final_ext}"
            filters = []
            if luma_amount > 0: filters.append(f"unsharp={luma_m_size}:{luma_m_size}:{luma_amount}")
            if scale_mode == 'ratio' and scale_value != 1: filters.append(f"scale=iw*{scale_value}:-2")
            elif scale_mode in ['hd1080', 'hd720']: px = 1080 if scale_mode=='hd1080' else 720; filters.append(f"scale='if(lt(iw,ih),{px},-2)':'if(lt(iw,ih),-2,{px})'")
            cmd = ["ffmpeg", "-y", "-i", str(fp)]; (cmd.extend(["-vf", ",".join(filters)]) if filters else None)
            cmd.extend(["-c:v", "libx264", "-crf", "23"] if (filters or convert_h264) else ["-c:v", "copy"])
            cmd.extend(["-c:a", "copy"]); (cmd.extend(["-map_metadata", "-1"]) if remove_metadata else None); (cmd.extend(["-metadata", f"artist={author}"]) if author else None); cmd.append(str(out_file))
            process = subprocess.Popen(cmd, stderr=subprocess.PIPE); process.wait()
            if process.returncode == 0 and delete_original and fp.resolve() != out_file.resolve(): os.remove(fp)
            acc_dur += max(get_video_duration(fp), 1); progress_callback(int((acc_dur/total_dur)*100))
        except Exception as e: log_callback(f"❌ {fp.name}: {e}")
    log_callback("🏁 結束")

def task_rename_replace(log_callback, progress_callback, current_file_callback, file_progress_callback, input_path, recursive, do_prefix, old_prefix, new_prefix, do_suffix, old_suffix, new_suffix):
    log_callback("🚀 [Rename] 開始"); files = get_files(input_path, recursive, file_types='all'); total = len(files)
    for i, fp in enumerate(files):
        progress_callback(int((i/total)*100)); current_file_callback(fp.name)
        try:
            stem = fp.stem; new_stem = stem
            if do_prefix and (not old_prefix or new_stem.startswith(old_prefix)): new_stem = new_prefix + (new_stem[len(old_prefix):] if old_prefix else new_stem)
            if do_suffix and old_suffix in new_stem and new_stem.endswith(old_suffix): new_stem = new_stem[:-len(old_suffix)] + new_suffix
            if new_stem != stem: fp.rename(fp.parent / f"{new_stem}{fp.suffix}"); log_callback(f"✏️ {fp.name} -> {new_stem}{fp.suffix}")
        except Exception as e: log_callback(f"❌ {fp.name}: {e}")
    progress_callback(100); log_callback("🏁 結束")

def task_multi_res(log_callback, progress_callback, current_file_callback, file_progress_callback, input_path, output_path, recursive, lower_ext, orientation):
    log_callback("🚀 [Icon] 開始"); sizes = [1024, 512, 256, 128, 64, 32]; files = get_files(input_path, recursive, file_types='image'); out_base = Path(output_path)
    for i, fp in enumerate(files):
        progress_callback(int((i/len(files))*100)); current_file_callback(fp.name)
        try:
            with Image.open(fp) as img:
                w, h = img.size; ref = w if orientation == 'h' else h
                dest = out_base / (fp.relative_to(Path(input_path)).parent if Path(input_path).is_dir() else fp.parent.name); dest.mkdir(parents=True, exist_ok=True)
                for s in sizes:
                    if ref >= s:
                        nw, nh = (s, int(h * (s/w))) if orientation == 'h' else (int(w * (s/h)), s)
                        img.resize((nw, nh), Image.Resampling.LANCZOS).save(dest / f"{fp.stem}-{s}{fp.suffix}", quality=90)
        except: pass
    progress_callback(100); log_callback("🏁 結束")