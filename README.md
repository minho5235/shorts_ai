# 🎬 AI Shorts Maker (News-to-Video Automation)

> **최신 뉴스 트렌드 분석부터 대본 작성, 영상 편집까지 100% 자동화한 AI 숏폼 생성 서비스**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18.0+-61DAFB?logo=react)
![Gemini API](https://img.shields.io/badge/AI-Google%20Gemini-8E75B2)
![MoviePy](https://img.shields.io/badge/Video-MoviePy-yellow)

---

## 📖 프로젝트 소개 (Project Overview)

**AI Shorts Maker**는 사용자가 주제를 입력하거나 실시간 트렌드를 선택하면, AI가 자동으로 1분 내외의 **숏폼(Shorts) 뉴스 영상**을 제작해주는 웹 애플리케이션입니다.

유튜브 크리에이터들이 뉴스 소싱, 대본 작성, 영상 편집에 많은 시간을 쏟는 문제에 착안하여, **Google News RSS**와 **LLM(Gemini)**, **TTS**, **영상 처리 라이브러리**를 결합해 콘텐츠 제작 시간을 획기적으로 단축(약 5분 이내)하는 것을 목표로 개발했습니다.

### 🎯 주요 기능
1.  **실시간 트렌드 분석**: Google News RSS를 크롤링하여 현재 가장 핫한 키워드 추출
2.  **AI 편집장 & 작가 모드**: 
    * **편집장(Editor)**: 수집된 뉴스 기사 10건을 분석하여 가장 중요한 '메인 토픽' 선정 및 팩트 체크
    * **작가(Writer)**: 선정된 팩트를 바탕으로 시청 지속 시간을 늘리는 '후킹(Hooking)' 멘트가 포함된 대본 작성
3.  **대본 커스터마이징**: AI가 작성한 대본을 사용자가 직접 수정/검수 가능 (Human-in-the-loop)
4.  **원클릭 영상 렌더링**:
    * 주제에 맞는 무료 스톡 영상(Pexels API) 자동 매칭
    * TTS(Edge-TTS)를 활용한 자연스러운 음성 생성
    * **MoviePy**를 활용한 자막 합성 및 영상 인코딩

---

## 🛠 기술 스택 (Tech Stack)

### Backend
* **Framework**: FastAPI (비동기 처리에 최적화된 고성능 프레임워크)
* **Language**: Python
* **AI/LLM**: Google Gemini-2.5-flash (빠른 응답 속도와 경제성 고려)
* **Media Processing**: 
    * `MoviePy`: 영상 병합 및 렌더링
    * `Pillow (PIL)`: 자막 이미지 동적 생성 및 위치 계산
    * `edge-tts`: MS Edge의 무료 TTS 엔진 활용
* **Database**: MySQL (SQLAlchemy ORM 사용)

### Frontend
* **Library**: React (Vite)
* **State Management**: useState (간결한 상태 관리)
* **Communication**: Fetch API (RESTful 통신)

---

## 🏗 시스템 아키텍처 (System Architecture)

```mermaid
graph TD
    User[사용자 Client] -->|주제 입력/선택| API[FastAPI Server]
    API -->|RSS 크롤링| GNews[Google News]
    API -->|기사 분석 및 대본 생성| Gemini[Gemini LLM]
    API -->|대본 반환| User
    
    User -->|대본 확정 및 제작 요청| API
    API -->|영상 검색| Pexels[Pexels API]
    API -->|음성 생성| TTS[Edge TTS]
    API -->|렌더링 (MoviePy)| VideoEngine[Video Processing Logic]
    VideoEngine -->|결과물 저장| Storage[Local Storage / DB]
    API -->|다운로드 URL| User


기술적 도전 및 해결 (Technical Challenges)
1. 비동기 서버의 Blocking 문제 해결
문제: FastAPI는 비동기(Async) 프레임워크지만, MoviePy를 이용한 영상 렌더링은 CPU를 많이 사용하는 동기(Sync) 작업이라 서버 전체가 멈추는 현상(Blocking) 발생.

해결: fastapi.concurrency.run_in_threadpool을 도입하여 렌더링 작업을 별도 스레드 풀에서 실행함으로써, 영상 제작 중에도 다른 API 요청(트렌드 조회 등)을 처리할 수 있도록 개선했습니다.

2. 가독성 높은 동적 자막 구현
문제: 영상 해상도나 텍스트 길이에 따라 자막이 잘리거나 위치가 어긋나는 문제.

해결: Pillow의 ImageDraw 기능을 활용해 텍스트의 Bounding Box를 계산하고, anchor="ma" (Middle-Ascender) 속성을 사용하여 텍스트 길이가 달라도 항상 화면 중앙 하단에 정렬되도록 알고리즘을 구현했습니다. 또한 폰트 크기를 영상 너비의 7%로 반응형으로 설정했습니다.

3. LLM 환각(Hallucination) 최소화 - '페르소나' 기법
문제: 단순히 "대본 써줘"라고 요청하면 AI가 없는 사실을 지어내는 현상 발생.

해결: 프롬프트 엔지니어링을 '뉴스 수집(Raw Data)' -> '편집장(분석 및 팩트 선정)' -> '작가(대본화)'의 3단계로 분리했습니다. 편집장 단계에서 10개의 뉴스 기사를 교차 검증하게 하여 신뢰도를 높였습니다.


📂 폴더 구조 (Directory Structure)
Bash

📦 AI-Shorts-Maker
├── 📂 frontend          # React UI 애플리케이션
│   ├── src/App.jsx      # 메인 UI 및 상태 관리 로직
│   └── ...
├── 📂 backend           # FastAPI 서버 애플리케이션
│   ├── main.py          # API 엔트리포인트 & 비동기 스레드 관리
│   ├── services.py      # 외부 서비스 연동 (Gemini, RSS, TTS)
│   ├── video_engine.py  # 영상 처리 엔진 (MoviePy, Pillow 자막 처리)
│   ├── models.py        # 데이터베이스 스키마 정의
│   ├── database.py      # DB 세션 설정
│   └── results/         # 생성된 영상 결과물 저장소
└── README.md
