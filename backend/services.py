import google.generativeai as genai
import edge_tts
import os
from dotenv import load_dotenv
from datetime import datetime
import feedparser

load_dotenv()

# 1. Gemini 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def get_hot_topics():
    # 구글 뉴스 대한민국(KR) 주요 뉴스 피드
    rss_url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    hot_topics = []
    # 상위 5개만 가져오기
    for entry in feed.entries[:5]:
        hot_topics.append(entry.title)
        
    return hot_topics

# 2. 대본 작성 함수 (Gemini)
def generate_script(topic: str):
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # [1] 오늘 날짜를 구합니다 (예: "2025년 12월 16일")
    today_date = datetime.now().strftime("%Y년 %m월 %d일")

    # [2] 프롬프트에 날짜를 명시하고, "과거가 아닌 현재 시점"을 강조합니다.
    prompt = f"""
    당신은 인기 있는 유튜브 쇼츠 뉴스 캐스터입니다.
    
    [중요]
    - 오늘 날짜: {today_date}
    - {today_date} 현재 시점에서 가장 최신 근황이나 이슈를 다루세요.
    
    주제: '{topic}'

    위 주제에 대해 50초 내외로 읽을 수 있는 흥미로운 대본을 작성해주세요.
    반말(친구에게 말하듯이)로 작성하고, 이모지를 적절히 섞어주세요.
    불필요한 서론 없이 바로 본론으로 들어가세요.
    """
    response = model.generate_content(prompt)
    return response.text

# 3. 목소리 생성 함수 (Edge-TTS)
async def generate_audio(text: str, filename="output_audio.mp3"):
    # 목소리 종류: ko-KR-SunHiNeural (여자), ko-KR-InJoonNeural (남자)
    VOICE = "ko-KR-InJoonNeural" 
    
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)
    return filename

# 4. [NEW] 주제를 영어 키워드로 바꾸기 (Pexels 검색용)
def get_search_keyword(topic: str):
    model = genai.GenerativeModel("gemini-2.5-flash") # 아까 설정한 모델 사용
    
    prompt = f"""
    Suggest only ONE English keyword to search for a stock video related to: '{topic}'.
    Do not write any explanation, just the word.
    Example: '고양이' -> 'Cat', '비트코인 떡상' -> 'Bitcoin'
    """
    
    response = model.generate_content(prompt)
    keyword = response.text.strip()
    print(f"🔍 검색어 변환: '{topic}' -> '{keyword}'")
    return keyword