import os
import requests
import random
import numpy as np

# [필수] Pillow 호환성 패치
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, vfx
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# 1. 영상 다운로드 (화질 최적화 유지)
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

# [수정됨] 2. 자막 이미지 생성 (그림자 제거, 깔끔한 외곽선 스타일)
def create_text_image(text, font_path, video_w, video_h):
    img = Image.new('RGBA', (video_w, video_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 폰트 크기: 영상 너비의 7%
    fontsize = int(video_w * 0.07)
    
    try:
        font = ImageFont.truetype(font_path, fontsize) 
    except:
        font = ImageFont.load_default()
    
    max_width = video_w * 0.85
    
    # 줄바꿈 로직
    words = text.split(' ') 
    lines = []
    current_line_words = []
    
    for word in words:
        test_line = ' '.join(current_line_words + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line_words.append(word)
        else:
            if current_line_words:
                lines.append(' '.join(current_line_words))
            current_line_words = [word]
            
    if current_line_words:
        lines.append(' '.join(current_line_words))
        
    final_text = "\n".join(lines)
    
    # 줄 간격 (깔끔하게 떨어지도록 15% 정도)
    line_spacing = int(fontsize * 0.15)
    
    # 전체 텍스트 박스 크기 계산
    bbox = draw.multiline_textbbox((0, 0), final_text, font=font, align="center", spacing=line_spacing)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (video_w - text_w) / 2
    bottom_margin = video_h * 0.2 
    y = video_h - text_h - bottom_margin 
    
    # [스타일 핵심] 
    # 그림자(offsets 루프) 다 없애고, 딱 'stroke_width' 하나만 사용해서 깔끔하게 처리
    # 두께는 폰트 크기의 4% (너무 두껍지 않게)
    stroke_width = max(1, int(fontsize * 0.04))
    
    draw.multiline_text(
        (x, y), 
        final_text, 
        font=font, 
        fill=(255, 255, 0, 255),      # 글자색: 노랑
        align="center", 
        spacing=line_spacing,
        stroke_width=stroke_width,    # 테두리 두께
        stroke_fill=(0, 0, 0, 255)    # 테두리 색: 검정
    )
    
    return np.array(img)

# 3. 합치기 (물리적 반복 + 리사이징 유지)
def combine_clips(data_list, video_path, output_path):
    font_path = os.path.join(BASE_DIR, "fonts", "NanumGothic-Bold.ttf")
    if not os.path.exists(font_path): font_path = "arial.ttf"

    bg_video = VideoFileClip(video_path)

    # 1. 1080p -> 720p 다이어트
    if bg_video.h > 1280:
        print(f"📉 고화질 감지! 해상도 축소 중... ({bg_video.h}p -> 1280p)")
        bg_video = bg_video.resize(height=1280)

    final_clips = []
    total_duration = 0
    
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
    
    # 2. 물리적 반복 (에러 방지)
    if bg_video.duration < total_duration:
        print(f"🔄 영상 길이 연장 (물리적 복사)")
        n_loops = int(total_duration / bg_video.duration) + 2
        bg_video = concatenate_videoclips([bg_video] * n_loops)
    
    bg_video = bg_video.subclip(0, total_duration)
        
    w, h = bg_video.size
    target_ratio = 9/16
    if w/h > target_ratio:
        new_w = h * target_ratio
        bg_video = bg_video.crop(x1=w/2 - new_w/2, width=new_w, height=h)
    
    final_video = CompositeVideoClip([bg_video, content_clip])
    
    print("⏳ 렌더링 시작 (깔끔한 스타일)...")

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