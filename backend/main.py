from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles 
from sqlalchemy.orm import Session
from pydantic import BaseModel # 👈 데이터 주고받을 틀 (필수)
from fastapi.concurrency import run_in_threadpool # 👈 서버 멈춤 방지용
import models
from database import SessionLocal, engine
import services
import video_engine
import os
import re
import time
import shutil 

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 결과물 폴더 설정
RESULTS_DIR = "results"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)
    
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")


# --- [NEW] 데이터 모델 정의 (프론트와 약속) ---

# 1단계 요청: "주제만 줄게, 대본 써줘"
class ScriptRequest(BaseModel):
    topic: str

# 2단계 요청: "확정된 대본 줄게, 영상 만들어줘"
class VideoCreationRequest(BaseModel):
    topic: str
    final_script: str # 사용자가 수정한 최종 대본


# --- 헬퍼 함수들 ---

def delete_file_force(filepath):
    if not os.path.exists(filepath): return
    for i in range(5): 
        try:
            os.remove(filepath)
            return 
        except:
            time.sleep(1) 
    print(f"💀 파일 삭제 실패: {filepath}")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.get("/")
def read_root():
    return {"message": "AI Shorts Maker Ready!"}

@app.get("/trends")
def read_trends():
    try:
        topics = services.get_hot_topics()
        return {"status": "success", "topics": topics}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


# 👇 [1단계] 대본 생성 API (영상 제작 X, 텍스트만 반환)
@app.post("/generate-script")
async def generate_script_api(request: ScriptRequest):
    topic = request.topic
    print(f"📝 1단계: 대본 작성 요청 - {topic}")
    
    try:
        # 1. 뉴스 검색 및 편집장 분석
        news_context = services.get_search_context(topic)
        
        # 2. 초안 대본 작성
        full_script = services.generate_script(topic, news_context)
        
        # 3. 괄호 및 지문 제거 (1차 청소) - 사용자가 보기 편하게 미리 지워줌
        clean_script = re.sub(r'\([^)]*\)', '', full_script) # (지문) 제거
        clean_script = re.sub(r'\[[^]]*\]', '', clean_script) # [지문] 제거
        clean_script = clean_script.strip()
        
        print(f"✅ 대본 생성 완료 ({len(clean_script)}자)")
        
        # 4. 프론트엔드로 대본 전송
        return {
            "status": "success", 
            "topic": topic,
            "script": clean_script,       # 이걸 프론트엔드 에디터에 뿌려주세요
            "original_context": news_context # (선택) 참고용으로 보여줘도 됨
        }
        
    except Exception as e:
        print(f"❌ 대본 생성 실패: {e}")
        return {"status": "error", "msg": str(e)}


# 👇 [2단계] 영상 제작 API (사용자가 OK한 대본으로 제작)
@app.post("/make-video")
async def make_video_api(request: VideoCreationRequest, db: Session = Depends(get_db)):
    topic = request.topic
    script = request.final_script # 사용자가 수정한 최종 대본
    
    print(f"🎬 2단계: 영상 제작 시작 - {topic}")

    # 1. DB에 "작업 시작(PROCESSING)" 기록
    new_request = models.VideoRequest(topic=topic, status="PROCESSING")
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    print(f"💾 DB 작업 ID: {new_request.id}")

    try:
        # 2. 문장 자르기 (이미 정제된 대본이므로 바로 자름)
        sentences = re.split(r'(?<=[.?!])\s+', script)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 1]

        # 3. 오디오 생성
        clip_data = []
        for i, text in enumerate(sentences):
            # 파일명 충돌 방지를 위해 ID 포함
            audio_filename = f"temp_audio_{new_request.id}_{i}.mp3" 
            await services.generate_audio(text, audio_filename)
            clip_data.append({"text": text, "audio": audio_filename})

        # 4. 배경 영상 준비
        search_keyword = services.get_search_keyword(topic)
        temp_video_path = f"temp_video_{new_request.id}.mp4" # ID 포함
        
        video_path = video_engine.download_stock_video(search_keyword, 15, temp_video_path)
        
        if not video_path:
            raise Exception("배경 영상을 찾지 못했습니다.")

        # 5. 영상 합치기 (오래 걸리므로 별도 스레드에서 실행!)
        # 안전한 파일명 생성
        safe_topic = re.sub(r'[\\/*?:"<>|]', "", topic).replace(" ", "_")
        output_filename = os.path.join(RESULTS_DIR, f"shorts_{safe_topic}_{new_request.id}.mp4")

        # [핵심] 서버 멈춤 방지를 위해 run_in_threadpool 사용
        final_path = await run_in_threadpool(
            video_engine.combine_clips,
            clip_data,
            video_path,
            output_filename
        )

        # 6. 임시 파일 청소
        for item in clip_data: delete_file_force(item['audio'])
        delete_file_force(video_path)

        # 7. 완료 처리 및 DB 업데이트
        web_url = f"/results/{os.path.basename(final_path)}" # 웹에서 접근 가능한 경로
        
        new_request.status = "COMPLETED"
        new_request.script = script # 최종 사용된 대본 저장
        new_request.video_url = web_url
        db.commit()
        
        print(f"✨ 영상 제작 완료: {web_url}")
        return {"status": "success", "video_url": web_url}

    except Exception as e:
        print(f"❌ 영상 제작 실패: {e}")
        new_request.status = "FAILED"
        db.commit()
        return {"status": "error", "msg": str(e)}