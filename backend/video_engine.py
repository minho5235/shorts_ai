import os
import requests
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
# 👇 [수정] vfx 추가 (영상 반복 루프를 효율적으로 처리하기 위해 필요)
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, vfx
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# 1. Pexels 영상 다운로드 (기존 로직 유지)
def download_stock_video(query, duration, filename="temp_video.mp4"):
    headers = {"Authorization": PEXELS_API_KEY}
    
    search_queries = [query]
    fallback_keywords = ["technology", "business", "city", "future", "abstract", "nature"]
    search_queries.extend(fallback_keywords)

    for keyword in search_queries:
        print(f"🔍 Pexels 검색 시도: '{keyword}'")
        url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=20"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200: continue
            
            data = response.json()
            if "videos" in data and len(data["videos"]) > 0:
                best_video_link = None
                random.shuffle(data["videos"]) 
                
                for v in data["videos"]:
                    for f in v["video_files"]:
                        w = f["width"]
                        h = f["height"]
                        # 720p ~ 1080p 사이 적절한 화질 찾기
                        if 720 <= w <= 1920:
                            best_video_link = f["link"]
                            print(f"   🎯 딱 좋은 화질 발견! ({w}x{h})")
                            break 
                    if best_video_link: break
                
                if not best_video_link:
                      print("   ⚠️ 딱 맞는 화질이 없어서 차선책을 찾습니다.")
                      for v in data["videos"]:
                        for f in v["video_files"]:
                            if f["width"] >= 720:
                                best_video_link = f["link"]
                                break
                        if best_video_link: break

                if not best_video_link:
                    print("   ❌ 쓸만한 화질이 없어서 넘어갑니다.")
                    continue

                print(f"🎬 영상 다운로드 시작... (주제: {keyword})")
                with open(filename, 'wb') as f:
                    f.write(requests.get(best_video_link).content)
                print("✅ 다운로드 완료")
                return filename
                
        except Exception as e:
            print(f"⚠️ 에러 발생: {e}")
            continue
            
    return None

# 2. 자막 이미지 생성 (기존 유지)
def create_text_image(text, font_path, video_w, video_h):
    img = Image.new('RGBA', (video_w, video_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 폰트 크기: 너비의 6%
    fontsize = int(video_w * 0.06)
    
    try:
        font = ImageFont.truetype(font_path, fontsize) 
    except:
        font = ImageFont.load_default()
    
    max_width = video_w * 0.85
    lines = []
    current_line = ""
    
    for char in text:
        bbox = draw.textbbox((0, 0), current_line + char, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line += char
        else:
            lines.append(current_line)
            current_line = char
    lines.append(current_line)
    
    final_text = "\n".join(lines)
    
    bbox = draw.textbbox((0, 0), final_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (video_w - text_w) / 2
    bottom_margin = video_h * 0.15 
    y = video_h - text_h - bottom_margin 
    
    shadow_color = (0, 0, 0, 255)
    stroke_width = max(1, int(fontsize * 0.05))
    
    offsets = []
    for i in range(1, stroke_width + 1):
        offsets.extend([(i, i), (-i, -i), (i, -i), (-i, i), (i, 0), (-i, 0), (0, i), (0, -i)])
        
    for ox, oy in offsets:
        draw.text((x+ox, y+oy), final_text, font=font, fill=shadow_color, align="center")
    
    draw.text((x, y), final_text, font=font, fill=(255, 255, 0, 255), align="center")
    
    return np.array(img)

# 3. 합치기 (🚀 최적화 적용됨)
def combine_clips(data_list, video_path, output_path):
    font_path = os.path.join(BASE_DIR, "fonts", "NanumGothic-Bold.ttf")
    if not os.path.exists(font_path): font_path = "arial.ttf"

    bg_video = VideoFileClip(video_path)

    # [🚨 최적화 핵심 1] 1080p 이상이면 720p로 강제 리사이징 (속도 3배 향상)
    if bg_video.h > 1280:
        print(f"📉 고화질 감지! 해상도 축소 중... ({bg_video.h}p -> 1280p)")
        # 높이를 1280으로 맞추면 너비는 비율에 맞춰 자동 조절됨
        bg_video = bg_video.resize(height=1280)

    final_clips = []
    total_duration = 0
    
    # 텍스트 이미지 생성 (리사이징된 크기에 맞춰서 생성됨 -> 여기서도 속도 이득)
    for item in data_list:
        text = item['text']
        audio_file = item['audio']
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration
        
        txt_img = create_text_image(text, font_path, bg_video.w, bg_video.h)
        txt_clip = ImageClip(txt_img).set_duration(duration).set_audio(audio_clip)
        
        final_clips.append(txt_clip)
        total_duration += duration

    content_clip = concatenate_videoclips(final_clips, method="compose")
    
    # [🚨 최적화 핵심 2] vfx.loop 사용 (메모리 절약)
    if bg_video.duration < total_duration:
        print(f"🔄 배경 영상 루프 적용 (길이 맞춤)")
        bg_video = vfx.loop(bg_video, duration=total_duration)
    else:
        bg_video = bg_video.subclip(0, total_duration)
        
    # 9:16 비율 크롭 (중앙 기준)
    w, h = bg_video.size
    target_ratio = 9/16
    if w/h > target_ratio:
        new_w = h * target_ratio
        bg_video = bg_video.crop(x1=w/2 - new_w/2, width=new_w, height=h)
    
    final_video = CompositeVideoClip([bg_video, content_clip])
    
    print("⏳ 렌더링 시작 (초고속 모드)...")

    # [🚨 최적화 핵심 3] ultrafast 프리셋
    final_video.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac", 
        fps=24, 
        preset='ultrafast',
        threads=4
    )

    final_video.close()
    bg_video.close()
    content_clip.close()
    
    return output_path