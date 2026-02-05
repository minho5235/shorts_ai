from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles 
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool
import models
from database import SessionLocal, engine
import services
import video_engine
import os
import re
import time

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

RESULTS_DIR = "results"
if not os.path.exists(RESULTS_DIR): 
    os.makedirs(RESULTS_DIR)
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

# [모델 수정] 사용자 입력값 받기
class ScriptRequest(BaseModel):
    topic: str
    duration: str = "50초" # 사용자 희망 길이

class VideoCreationRequest(BaseModel):
    topic: str
    final_script: str
    voice: str = "female"
    speed: str = "1.2"    # 배속 (문자열로 받음)
    use_subtitles: bool = True
    subtitle_pos: str = "bottom"

def delete_file_force(filepath):
    if not filepath or not os.path.exists(filepath): 
        return
    for i in range(5): 
        try: 
            os.remove(filepath)
            return 
        except: 
            time.sleep(1)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

@app.get("/trends")
def read_trends():
    try: 
        return {"status": "success", "topics": services.get_hot_topics()}
    except Exception as e: 
        return {"status": "error", "msg": str(e)}

@app.post("/generate-script")
async def generate_script_api(request: ScriptRequest):
    try:
        # 길이 정보를 서비스로 전달
        news_context = services.get_search_context(request.topic)
        full_script = services.generate_script(request.topic, news_context, request.duration)
        clean_script = re.sub(r'\([^)]*\)|\[[^]]*\]', '', full_script).strip()
        return {"status": "success", "script": clean_script}
    except Exception as e: 
        return {"status": "error", "msg": str(e)}

@app.post("/make-video")
async def make_video_api(request: VideoCreationRequest, db: Session = Depends(get_db)):
    new_req = models.VideoRequest(topic=request.topic, status="PROCESSING")
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    # [청소용 변수 미리 선언]
    clip_data = []
    vid_path = None
    
    try:
        sentences = re.split(r'(?<=[.?!])\s+', request.final_script)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 1]

        for i, text in enumerate(sentences):
            fname = f"temp_audio_{new_req.id}_{i}.mp3"
            # 배속 정보 전달
            await services.generate_audio(text, fname, request.voice, request.speed)
            clip_data.append({"text": text, "audio": fname})

        search_keyword = services.get_search_keyword(request.topic)
        temp_vid = f"temp_video_{new_req.id}.mp4"
        vid_path = video_engine.download_stock_video(search_keyword, 15, temp_vid)
        
        if not vid_path: 
            raise Exception("영상 소스 없음")

        safe_topic = re.sub(r'[\\/*?:"<>|]', "", request.topic).replace(" ", "_")
        out_name = os.path.join(RESULTS_DIR, f"shorts_{safe_topic}_{new_req.id}.mp4")

        final_path = await run_in_threadpool(
            video_engine.combine_clips,
            clip_data, vid_path, out_name,
            request.use_subtitles, request.subtitle_pos
        )

        web_url = f"/results/{os.path.basename(final_path)}"
        new_req.status = "COMPLETED"
        new_req.script = request.final_script
        new_req.video_url = web_url
        db.commit()
        return {"status": "success", "video_url": web_url}

    except Exception as e:
        new_req.status = "FAILED"
        db.commit()
        print(f"❌ 제작 실패: {e}")
        return {"status": "error", "msg": str(e)}
        
    finally:
        # [핵심] 성공하든 실패하든 파일은 무조건 삭제
        print("🧹 임시 파일 청소 중...")
        for item in clip_data: 
            delete_file_force(item.get('audio'))
        delete_file_force(vid_path)