from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware # 👈 추가
from fastapi.staticfiles import StaticFiles #
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "AI Shorts Maker Ready!"}

# [NEW] 요즘 뭐 핫해? (트렌드 추천 API)
@app.get("/trends")
def read_trends():
    try:
        topics = services.get_hot_topics()
        return {"status": "success", "topics": topics}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.post("/create-shorts")
async def create_shorts(topic: str, db: Session = Depends(get_db)): # 👈 db 주입
    print(f"🚀 프로젝트 시작: {topic}")
    
    # [1] DB에 "작업 시작(PROCESSING)" 기록 남기기
    new_request = models.VideoRequest(
        topic=topic,
        status="PROCESSING"
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request) # ID 발급 받음
    print(f"💾 DB 기록 시작 (ID: {new_request.id})")

    try:
        
        # [STEP 1] 사용자가 입력한 주제로 '최신 정보' 긁어오기 (핵심!)
        print(f"🔍 '{topic}' 관련 최신 정보 검색 중...")
        news_context = services.get_search_context(topic)
        print(f"✅ 정보 수집 완료 (참고 자료 길이: {len(news_context)}자)")

        # [STEP 2] 수집한 정보를 바탕으로 대본 작성
        full_script = services.generate_script(topic, news_context)
        print(f"✅ 대본 생성 완료")

        clean_script = re.sub(r'\([^)]*\)', '', full_script)
        # 2. [ ... ] 제거 (혹시 몰라서 추가)
        clean_script = re.sub(r'\[[^]]*\]', '', clean_script)
        # 3. 양옆 공백 제거
        clean_script = clean_script.strip()

        print(f"🧹 지문 제거 완료: {len(clean_script)}자")
        
        # 2. 문장 자르기
        sentences = re.split(r'(?<=[.?!])\s+', clean_script)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 1]

        # 3. 오디오 생성
        clip_data = [] 
        for i, text in enumerate(sentences):
            audio_filename = f"temp_audio_{i}.mp3"
            await services.generate_audio(text, audio_filename)
            clip_data.append({"text": text, "audio": audio_filename})

        # 4. 배경 영상 준비
        search_keyword = services.get_search_keyword(topic)
        temp_video_path = f"temp_{topic}.mp4"
        
        video_path = video_engine.download_stock_video(search_keyword, 10, temp_video_path)
        
        if not video_path:
            # 실패 시 DB 업데이트
            new_request.status = "FAILED"
            db.commit()
            return {"status": "failed", "msg": "영상 소스 없음"}

        safe_topic = re.sub(r'[\\/*?:"<>|]', "", topic) # 윈도우 금지 문자 제거
        safe_topic = safe_topic.replace(" ", "_")
        
        # 5. 합치기
        output_filename = os.path.join(RESULTS_DIR, f"shorts_{safe_topic}.mp4")
        final_path = video_engine.combine_clips(clip_data, video_path, output_filename)
        
        # 6. 청소
        for item in clip_data: delete_file_force(item['audio'])
        delete_file_force(video_path)

        # --- 기존 로직 끝 ---

        # [2] 성공 시 DB 업데이트 (COMPLETED)
        # 프론트에서 접근 가능한 URL로 저장 (예: /results/shorts_abc.mp4)
        web_url = f"/results/shorts_{topic}.mp4"
        
        new_request.status = "COMPLETED"
        new_request.script = full_script
        new_request.video_url = web_url # 나중에 프론트에서 쓰기 편하게
        db.commit()
        
        print(f"✨ DB 업데이트 완료 (상태: COMPLETED)")
        return {"status": "success", "file": final_path}

    except Exception as e:
        # [3] 에러 발생 시 DB 업데이트 (FAILED)
        print(f"❌ 에러 발생: {e}")
        new_request.status = "FAILED"
        db.commit()
        return {"status": "error", "msg": str(e)}