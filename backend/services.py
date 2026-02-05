import re
import google.generativeai as genai
import edge_tts
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
import feedparser
import urllib.parse
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def get_hot_topics():
    rss_url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    hot_topics = [entry.title for entry in feed.entries[:5]]
    return hot_topics

def get_search_context(keyword: str):
    encoded_keyword = urllib.parse.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        return f"'{keyword}' 관련 뉴스가 없습니다."

    raw_news_data = ""
    for i, entry in enumerate(feed.entries[:5]):
        title = entry.title
        summary = entry.description if hasattr(entry, 'description') else ""
        clean_summary = re.sub('<[^<]+?>', '', summary) 
        if len(clean_summary) > 300: clean_summary = clean_summary[:300] + "..."
        raw_news_data += f"[{i+1}] {title} : {clean_summary}\n"

    print(f"🕵️ [편집장] '{keyword}' 분석 중...")
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
    당신은 뉴스 편집장입니다. 아래 뉴스들을 분석하여 '단 하나의 메인 토픽'을 선정하세요.
    [검색 키워드]: {keyword}
    [뉴스 목록]
    {raw_news_data}
    [지시사항]
    1. 가장 파급력이 큰 주제 하나만 선정하세요.
    2. 선정된 주제로 상세 리포트를 작성하세요.
    """
    try:
        analysis_response = model.generate_content(prompt, safety_settings=safety_settings)
        return analysis_response.text
    except:
        return "뉴스 분석 실패 (일반적인 내용 작성)"

# [수정] duration 반영
def generate_script(topic: str, context: str, duration: str = "50초"):
    model = genai.GenerativeModel(MODEL_NAME)
    today_date = datetime.now().strftime("%Y년 %m월 %d일")

    prompt = f"""
    당신은 쇼츠 뉴스 크리에이터입니다.
    [정보]
    - 날짜: {today_date}
    - 주제: {topic}
    - 목표 영상 길이: {duration} (이 길이에 맞춰 글자 수를 조절하세요)
    
    [편집장 리포트]
    {context}
    
    [지시사항]
    1. 리포트의 핵심만 다루세요.
    2. 말투: 친구에게 말하듯 빠르고 텐션 높은 반말.
    3. 목표 길이({duration})를 고려하여 대본 분량을 조절하세요.
    4. 괄호나 지문(행동 묘사)은 절대 쓰지 마세요.
    """
    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return response.text
    except:
        return "대본 작성 실패."

# [수정] speed_rate 처리 로직 추가
async def generate_audio(text: str, filename="output_audio.mp3", voice_gender="female", speed_rate="1.2"):
    if voice_gender == "male":
        VOICE = "ko-KR-InJoonNeural"
    else:
        VOICE = "ko-KR-SunHiNeural"
    
    # "1.2" -> "+20%", "0.8" -> "-20%" 변환 로직
    try:
        rate_float = float(speed_rate)
        percentage = int((rate_float - 1.0) * 100)
        if percentage >= 0:
            rate_str = f"+{percentage}%"
        else:
            rate_str = f"{percentage}%"
    except:
        rate_str = "+20%" # 기본값

    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            communicate = edge_tts.Communicate(text, VOICE, rate=rate_str)
            await communicate.save(filename)
            return filename 
        except Exception as e:
            print(f"⚠️ TTS 서버 오류 (시도 {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2)
            else:
                raise e

def get_search_keyword(topic: str):
    model = genai.GenerativeModel(MODEL_NAME) 
    prompt = f"Suggest ONE English keyword for stock video: '{topic}'"
    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return response.text.strip()
    except:
        return "News"