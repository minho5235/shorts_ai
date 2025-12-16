from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 👈 추가
from fastapi.staticfiles import StaticFiles #
import models
from database import engine
import services
import video_engine
import os
import re
import time
import shutil # 파일 이동 등을 위해 필요할 수 있음

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 모든 곳에서 접속 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👇 [2] 결과물 폴더를 브라우저에 공개 (영상 재생용)
# 이제 http://localhost:8000/results/파일명.mp4 로 접근 가능해짐
RESULTS_DIR = "results"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)
    
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")


# [NEW] 끈질긴 삭제 함수 (최대 5번, 1초 간격으로 시도)
def delete_file_force(filepath):
    if not os.path.exists(filepath):
        return
    
    for i in range(5): # 5번 시도
        try:
            os.remove(filepath)
            print(f"🗑️ 삭제 성공: {filepath}")
            return # 성공하면 종료
        except PermissionError:
            print(f"⚠️ 삭제 실패 (잠김), 1초 뒤 재시도... ({i+1}/5)")
            time.sleep(1) # 1초 대기
        except Exception as e:
            print(f"❌ 삭제 중 에러: {e}")
            return

    print(f"💀 결국 삭제 실패 (수동 삭제 필요): {filepath}")

@app.get("/")
def read_root():
    return {"message": "AI Shorts Maker Ready!"}

@app.post("/create-shorts")
async def create_shorts(topic: str):
    print(f"🚀 프로젝트 시작: {topic}")
    
    # 1. 대본 작성
    full_script = services.generate_script(topic)
    print(f"✅ 대본 생성 완료: {len(full_script)}자")
    
    # 2. 문장 자르기
    sentences = re.split(r'(?<=[.?!])\s+', full_script)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 1]
    print(f"✂️ 총 {len(sentences)}개 문장으로 분할됨")

    # 3. 오디오 생성
    clip_data = [] 
    for i, text in enumerate(sentences):
        audio_filename = f"temp_audio_{i}.mp3"
        await services.generate_audio(text, audio_filename)
        clip_data.append({"text": text, "audio": audio_filename})
        print(f"   Sound [{i+1}/{len(sentences)}] 생성 완료")

    # 4. 배경 영상 준비
    search_keyword = services.get_search_keyword(topic)
    temp_video_path = f"temp_{topic}.mp4" # 임시 파일 이름
    
    video_path = video_engine.download_stock_video(search_keyword, 10, temp_video_path)
    
    if not video_path:
        # 실패 시 오디오라도 지우고 종료
        for item in clip_data: delete_file_force(item['audio'])
        return {"status": "failed", "msg": "영상 소스 없음"}

    # 5. 합치기 & 결과물 폴더에 저장
    # [수정] results 폴더 안에 파일명 생성
    output_filename = os.path.join(RESULTS_DIR, f"shorts_{topic}.mp4")
    
    try:
        final_path = video_engine.combine_clips(clip_data, video_path, output_filename)
    except Exception as e:
        print(f"❌ 영상 합성 중 에러 발생: {e}")
        return {"status": "error", "msg": str(e)}
    
    # 6. 청소 (이제 끈질기게 지웁니다)
    print("🧹 임시 파일 청소 시작...")
    
    # 오디오 파일들 삭제
    for item in clip_data:
        delete_file_force(item['audio'])
            
    # 배경 영상 파일 삭제 (temp_엔비디아.mp4)
    delete_file_force(video_path)

    print(f"✨ 모든 작업 완료! 결과물: {final_path}")
    return {"status": "success", "file": final_path}