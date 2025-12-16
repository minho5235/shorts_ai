import os
import requests
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# 1. Pexels 영상 다운로드 (화질 최적화 버전 ⚡)
def download_stock_video(query, duration, filename="temp_video.mp4"):
    headers = {"Authorization": PEXELS_API_KEY}
    
    # 검색어 목록 (실패 시 백업 키워드)
    search_queries = [query]
    fallback_keywords = ["technology", "business", "city", "future", "abstract", "nature"]
    search_queries.extend(fallback_keywords)

    for keyword in search_queries:
        print(f"🔍 Pexels 검색 시도: '{keyword}'")
        # per_page를 좀 늘려서 선택지를 확보
        url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=20"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200: continue
            
            data = response.json()
            if "videos" in data and len(data["videos"]) > 0:
                
                # [핵심 수정] 화질 좋은 것 찾기 (4K는 거르고, HD~FHD만!)
                best_video_link = None
                
                # 랜덤으로 영상을 하나씩 까봅니다.
                random.shuffle(data["videos"]) 
                
                for v in data["videos"]:
                    # 해당 영상의 여러 화질 파일들을 확인
                    for f in v["video_files"]:
                        w = f["width"]
                        h = f["height"]
                        
                        # 조건: 너비가 720 이상이면서 1920 이하여야 함 (4K 컷!)
                        # 그리고 파일 크기가 너무 작지 않은 것
                        if 720 <= w <= 1920:
                            best_video_link = f["link"]
                            print(f"   🎯 딱 좋은 화질 발견! ({w}x{h})")
                            break # 파일 찾음
                    
                    if best_video_link:
                        break # 영상 찾음
                
                # 만약 조건에 맞는 게 없으면? 그냥 아무거나 720p 넘는 걸로 (차선책)
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

# 2. 자막 이미지 생성 (반응형 폰트 크기 적용 📏)
def create_text_image(text, font_path, video_w, video_h):
    img = Image.new('RGBA', (video_w, video_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # [수정] 폰트 크기를 영상 너비에 맞춰서 계산 (너비의 6% 정도)
    # 예: 1080px -> 65px, 720px -> 43px (항상 적절함)
    fontsize = int(video_w * 0.06)
    
    try:
        font = ImageFont.truetype(font_path, fontsize) 
    except:
        font = ImageFont.load_default()
    
    # 줄바꿈 기준도 영상 너비에 맞춤 (좌우 여백 15% 남김)
    max_width = video_w * 0.85
    lines = []
    current_line = ""
    
    # 글자 줄바꿈 계산
    for char in text:
        # 현재 줄 + 다음 글자의 길이를 미리 재봄
        bbox = draw.textbbox((0, 0), current_line + char, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line += char
        else:
            lines.append(current_line)
            current_line = char
    lines.append(current_line)
    
    final_text = "\n".join(lines)
    
    # 전체 텍스트 박스 크기 계산
    bbox = draw.textbbox((0, 0), final_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # 위치: 가로 중앙
    x = (video_w - text_w) / 2
    
    # 위치: 세로 하단 (밑에서 15% 띄움)
    bottom_margin = video_h * 0.15 
    y = video_h - text_h - bottom_margin 
    
    # 테두리 그리기 (폰트 크기에 비례해서 두께 조절)
    shadow_color = (0, 0, 0, 255)
    stroke_width = max(1, int(fontsize * 0.05)) # 글자가 커지면 테두리도 두껍게
    
    # 8방향 테두리 (확실한 가독성)
    offsets = []
    for i in range(1, stroke_width + 1):
        offsets.extend([(i, i), (-i, -i), (i, -i), (-i, i), (i, 0), (-i, 0), (0, i), (0, -i)])
        
    for ox, oy in offsets:
        draw.text((x+ox, y+oy), final_text, font=font, fill=shadow_color, align="center")
    
    # 노란색 본문
    draw.text((x, y), final_text, font=font, fill=(255, 255, 0, 255), align="center")
    
    return np.array(img)

# 3. 합치기 (수정됨: 루프 에러 해결)
def combine_clips(data_list, video_path, output_path):
    font_path = os.path.join(BASE_DIR, "fonts", "NanumGothic-Bold.ttf")
    if not os.path.exists(font_path): font_path = "arial.ttf"

    bg_video = VideoFileClip(video_path)
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
    
    # [핵심 수정] 영상이 짧으면 '물리적으로' 이어 붙여서 늘림 (에러 방지)
    if bg_video.duration < total_duration:
        # 필요한 반복 횟수 계산 (넉넉하게 +2)
        n_loops = int(total_duration / bg_video.duration) + 2
        print(f"🔄 영상이 짧아서 {n_loops}번 반복합니다.")
        bg_video = concatenate_videoclips([bg_video] * n_loops)
    
    # 오디오 길이만큼 자르기
    bg_video = bg_video.subclip(0, total_duration)
        
    w, h = bg_video.size
    if w/h > 9/16:
        new_w = h * (9/16)
        bg_video = bg_video.crop(x1=w/2 - new_w/2, width=new_w, height=h)
    
    final_video = CompositeVideoClip([bg_video, content_clip])
    
    print("⏳ 렌더링 중... (싱크 맞추는 중)")

    # threads=4를 지우면, 컴퓨터가 알아서 적당히 조절합니다.
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