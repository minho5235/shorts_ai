import google.generativeai as genai
import edge_tts
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Gemini 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 2. 대본 작성 함수 (Gemini)
def generate_script(topic: str):
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # 프롬프트: 쇼츠 스타일에 맞게 짧고 굵게 써달라고 시킴
    prompt = f"""
    당신은 인기 있는 유튜브 쇼츠 뉴스 캐스터입니다.
    주제: '{topic}'

    최신 정보를 바탕으로 위 주제에 대해 50초 내외로 읽을 수 있는 흥미로운 대본을 작성해주세요.
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