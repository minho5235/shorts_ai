import os
import requests
import random
import numpy as np
import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def download_stock_video(query, duration, filename="temp_video.mp4"):
    headers = {"Authorization": PEXELS_API_KEY}
    search_queries = [query, "technology", "business", "city", "future", "abstract"]
    
    for keyword in search_queries:
        print(f"🔍 Pexels 검색: '{keyword}'")
        url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=15"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200: continue
            data = response.json()
            if "videos" in data and len(data["videos"]) > 0:
                best_link = None
                random.shuffle(data["videos"])
                for v in data["videos"]:
                    for f in v["video_files"]:
                        if 720 <= f["width"] <= 1920:
                            best_link = f["link"]
                            break
                    if best_link: break
                
                if not best_link: best_link = data["videos"][0]["video_files"][0]["link"]

                with open(filename, 'wb') as f:
                    f.write(requests.get(best_link).content)
                return filename
        except: continue
    return None

# [수정] position 파라미터 추가 (top, middle, bottom)
def create_text_image(text, font_path, video_w, video_h, position='bottom'):
    img = Image.new('RGBA', (video_w, video_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fontsize = int(video_w * 0.07)
    
    try: font = ImageFont.truetype(font_path, fontsize)
    except: font = ImageFont.load_default()
    
    max_width = video_w * 0.85
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width: current_line.append(word)
        else:
            if current_line: lines.append(' '.join(current_line))
            current_line = [word]
    if current_line: lines.append(' '.join(current_line))
    
    final_text = "\n".join(lines)
    line_spacing = int(fontsize * 0.15)
    stroke_width = max(1, int(fontsize * 0.04))
    
    bbox = draw.multiline_textbbox((0, 0), final_text, font=font, align="center", spacing=line_spacing, stroke_width=stroke_width)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # [좌표 계산 로직]
    x = (video_w - text_w) // 2
    
    if position == 'top':
        y = video_h * 0.1 # 상단 10% 지점
    elif position == 'middle':
        y = (video_h - text_h) // 2 # 정중앙
    else: # bottom
        y = video_h - text_h - (video_h * 0.2) # 하단 20% 지점

    draw.multiline_text((x, y), final_text, font=font, fill="yellow", align="center", spacing=line_spacing, stroke_width=stroke_width, stroke_fill="black")
    return np.array(img)

# [수정] 옵션 받기 (use_subtitles, subtitle_pos)
def combine_clips(data_list, video_path, output_path, use_subtitles=True, subtitle_pos='bottom'):
    font_path = os.path.join(BASE_DIR, "fonts", "NanumGothic-Bold.ttf")
    if not os.path.exists(font_path): font_path = "C:/Windows/Fonts/malgunbd.ttf"

    bg_video = VideoFileClip(video_path)
    if bg_video.h > 1280: bg_video = bg_video.resize(height=1280)

    final_clips = []
    total_duration = 0
    
    for item in data_list:
        text = item['text']
        audio_file = item['audio']
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration
        
        # 자막 켜져있을 때만 이미지 생성
        if use_subtitles:
            txt_img = create_text_image(text, font_path, bg_video.w, bg_video.h, position=subtitle_pos)
            clip = ImageClip(txt_img).set_duration(duration).set_audio(audio_clip)
        else:
            # 자막 없으면 투명 이미지나 빈 클립 (여기서는 간단히 투명 이미지 사용)
            clip = ImageClip(np.array(Image.new('RGBA', (bg_video.w, bg_video.h), (0,0,0,0))))\
                    .set_duration(duration).set_audio(audio_clip)
        
        final_clips.append(clip)
        total_duration += duration

    content_clip = concatenate_videoclips(final_clips, method="compose")
    
    if bg_video.duration < total_duration:
        n_loops = int(total_duration / bg_video.duration) + 2
        bg_video = concatenate_videoclips([bg_video] * n_loops)
    
    bg_video = bg_video.subclip(0, total_duration)
    
    # 세로 크롭
    w, h = bg_video.size
    if w/h > 9/16:
        new_w = h * (9/16)
        bg_video = bg_video.crop(x1=w/2 - new_w/2, width=new_w, height=h)
    
    final_video = CompositeVideoClip([bg_video, content_clip])
    
    print("⏳ 렌더링 시작...")
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24, preset='ultrafast', threads=4)
    
    final_video.close()
    bg_video.close()
    content_clip.close()
    return output_path