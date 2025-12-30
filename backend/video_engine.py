import os
import requests
import random
import numpy as np

# [필수] Pillow 호환성 패치
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# 1. 영상 다운로드
def download_stock_video(query, duration, filename="temp_video.mp4"):
    headers = {"Authorization": PEXELS_API_KEY}
    
    # 검색어 확장
    search_queries = [query, "technology", "business", "city", "future", "abstract", "nature"]

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
                
                # 720p 이상 화질 우선 선택
                for v in data["videos"]:
                    for f in v["video_files"]:
                        w = f["width"]
                        if 720 <= w <= 1920:
                            best_video_link = f["link"]
                            break 
                    if best_video_link: break
                
                # 없으면 아무거나
                if not best_video_link:
                      for v in data["videos"]:
                        if v["video_files"]:
                            best_video_link = v["video_files"][0]["link"]
                            break

                if best_video_link:
                    print(f"🎬 영상 다운로드 시작... (주제: {keyword})")
                    with open(filename, 'wb') as f:
                        f.write(requests.get(best_video_link).content)
                    print("✅ 다운로드 완료")
                    return filename
                
        except Exception as e:
            print(f"⚠️ 에러 발생: {e}")
            continue
            
    return None

# [핵심 수정] 2. 자막 이미지 생성 (anchor='mm' 사용으로 완벽한 중앙 정렬)
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
    
    # 줄 간격
    line_spacing = int(fontsize * 0.15)
    
    # [좌표 계산 변경]
    # 복잡한 계산 다 버리고, 화면 정중앙(center_x)을 기준으로 잡습니다.
    center_x = video_w / 2
    
    # Y좌표: 화면 아래에서 20% 위로 띄움
    # 텍스트 높이만 계산해서 위치 잡기
    bbox = draw.multiline_textbbox((0, 0), final_text, font=font, align="center", spacing=line_spacing)
    text_h = bbox[3] - bbox[1]
    bottom_margin = video_h * 0.2
    y = video_h - text_h - bottom_margin
    
    stroke_width = max(1, int(fontsize * 0.04))
    
    # [핵심] anchor="ma" (Middle-Ascender)
    # 의미: "내가 지정한 좌표(center_x, y)가 텍스트의 가로 중앙(M)이자 상단(A)이 되게 그려라"
    # 이렇게 하면 글자 길이가 달라져도 무조건 가운데로 옵니다.
    draw.multiline_text(
        (center_x, y), 
        final_text, 
        font=font, 
        fill=(255, 255, 0, 255),      
        align="center", 
        spacing=line_spacing,
        stroke_width=stroke_width,    
        stroke_fill=(0, 0, 0, 255),
        anchor="ma"  # 👈 여기가 바뀐 핵심입니다!
    )
    
    return np.array(img)

# 3. 합치기
def combine_clips(data_list, video_path, output_path):
    # 폰트 경로 확인
    font_path = os.path.join(BASE_DIR, "fonts", "NanumGothic-Bold.ttf")
    # 폰트 없으면 시스템 기본 폰트로 대체 (깨짐 방지용)
    if not os.path.exists(font_path): 
        font_path = "C:/Windows/Fonts/malgunbd.ttf" # 윈도우 맑은고딕

    bg_video = VideoFileClip(video_path)

    if bg_video.h > 1280:
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
    
    if bg_video.duration < total_duration:
        n_loops = int(total_duration / bg_video.duration) + 2
        bg_video = concatenate_videoclips([bg_video] * n_loops)
    
    bg_video = bg_video.subclip(0, total_duration)
        
    w, h = bg_video.size
    target_ratio = 9/16
    if w/h > target_ratio:
        new_w = h * target_ratio
        bg_video = bg_video.crop(x1=w/2 - new_w/2, width=new_w, height=h)
    
    final_video = CompositeVideoClip([bg_video, content_clip])
    
    print("⏳ 렌더링 시작 (자막 위치 교정됨)...")

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