import re
import google.generativeai as genai
import edge_tts
import os
from dotenv import load_dotenv
from datetime import datetime
import feedparser
import urllib.parse

load_dotenv()

# 1. Gemini 설정 (API 키 및 모델)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 사용할 모델명 상수 (전체 적용)
MODEL_NAME = "gemini-2.5-flash"

def get_hot_topics():
    # 구글 뉴스 대한민국(KR) 주요 뉴스 피드
    rss_url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    hot_topics = []
    # 상위 5개만 가져오기
    for entry in feed.entries[:5]:
        hot_topics.append(entry.title)
        
    return hot_topics

# [핵심 수정] 편집장 모드: 10개를 긁어서 '가장 중요한 하나'만 남김
def get_search_context(keyword: str):
    # 1. 검색어 URL 인코딩
    encoded_keyword = urllib.parse.quote(keyword)
    
    # 2. 구글 뉴스 검색 RSS (상위 10개 수집을 위해 URL 호출)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        return f"'{keyword}' 관련 뉴스가 없습니다."

    # 3. 로우 데이터(Raw Data) 준비 - 상위 10개
    raw_news_data = ""
    for i, entry in enumerate(feed.entries[:10]):
        title = entry.title
        summary = entry.description if hasattr(entry, 'description') else ""
        # HTML 태그 제거
        clean_summary = re.sub('<[^<]+?>', '', summary) 
        raw_news_data += f"[{i+1}] {title} : {clean_summary}\n"

    print(f"🕵️ [편집장] '{keyword}' 관련 기사 10건 분석 및 주제 선정 중...")

    # 4. Gemini에게 '편집장' 역할 부여 (그룹핑 -> 선정 -> 리포트 작성)
    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = f"""
    당신은 냉철한 뉴스 편집장입니다. 아래 10개의 뉴스 기사들을 분석하여 대본 작가에게 넘길 '단 하나의 메인 토픽'을 결정해야 합니다.

    [검색 키워드]: {keyword}

    [뉴스 기사 목록 (Raw Data)]
    {raw_news_data}

    [분석 및 선정 절차]
    1. **그룹핑(Grouping):** 기사들을 주제별로 묶으세요. (예: A사건 5건, B행사 2건...)
    2. **가중치 평가:**
       - 가장 많은 언론사가 보도한 내용(빈도수)을 최우선으로 선정하세요.
       - 빈도수가 비슷하다면, 더 논란이 되거나 사회적 파장이 큰 주제를 선택하세요.
       - 홍보성 기사는 과감히 탈락시키세요.
    3. **최종 선정:** 위 기준에 따라 1등으로 선정된 주제만 남기세요.

    [출력 지침]
    - 선정된 1등 주제와 관련된 기사들의 내용을 모두 통합하여, 육하원칙에 맞게 상세히 '팩트 리포트'를 작성하세요.
    - 탈락한 다른 주제들의 내용은 절대 섞지 마세요.
    - 대본 작가가 자극적인 멘트를 뽑을 수 있도록 '논란의 핵심', '대중의 반응', '향후 전망'을 강조하세요.
    """
    
    # AI가 분석한 '편집장의 지시문' 반환
    analysis_response = model.generate_content(prompt)
    filtered_context = analysis_response.text
    
    return filtered_context

# [수정] 대본 작성 함수 (편집장의 리포트를 바탕으로 작성)
def generate_script(topic: str, context: str):
    model = genai.GenerativeModel(MODEL_NAME)
    
    today_date = datetime.now().strftime("%Y년 %m월 %d일")

    prompt = f"""
    당신은 100만 유튜버이자 쇼츠 뉴스 크리에이터입니다.
    
    [정보]
    - 오늘 날짜: {today_date}
    - 주제: {topic}
    
    [편집장의 핵심 분석 리포트]
    {context}
    
    [지시사항]
    1. 위 [편집장의 핵심 분석 리포트]에 선정된 **단 하나의 메인 사건**에만 집중해서 대본을 작성하세요. (여러 소식 나열 금지)
    2. 말투: 친구에게 말하듯 친근하고 텐션 높은 반말 (야, 대박, 있잖아 등 사용).
    3. 길이: 읽었을 때 1분 내외.
    4. 구성:
       - **후킹:** 첫 문장은 시청자가 지나치지 못하게 강력한 질문이나 감탄사로 시작.
       - **본론:** 사건의 핵심 내용을 쉽고 빠르게 요약.
       - **마무리:** 시청자의 의견을 묻거나 댓글을 유도하며 끝냄.
    5. 주의: 괄호 `( )` 나 지문은 절대 쓰지 마세요. 오직 읽을 대사만 출력하세요.
    """
    
    response = model.generate_content(prompt)
    return response.text

# 3. 목소리 생성 함수 (Edge-TTS)
async def generate_audio(text: str, filename="output_audio.mp3"):
    # 목소리 종류: ko-KR-SunHiNeural (여자), ko-KR-InJoonNeural (남자)
    VOICE = "ko-KR-SunHiNeural" 
    communicate = edge_tts.Communicate(text, VOICE, rate="+15%")
    await communicate.save(filename)
    return filename

# 4. 주제 키워드 추출 (Pexels용)
def get_search_keyword(topic: str):
    model = genai.GenerativeModel(MODEL_NAME) 
    
    prompt = f"""
    Suggest only ONE English keyword to search for a stock video related to: '{topic}'.
    Do not write any explanation, just the word.
    Example: '고양이' -> 'Cat', '비트코인 떡상' -> 'Bitcoin'
    """
    
    response = model.generate_content(prompt)
    keyword = response.text.strip()
    print(f"🔍 영상 검색어 변환: '{topic}' -> '{keyword}'")
    return keyword