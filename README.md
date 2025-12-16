# 🎬 AI Shorts Maker (AI 쇼츠 자동 생성기)

> **키워드 하나만 입력하면, 대본 작성부터 영상 편집까지 1분 만에 끝!** > 생성형 AI(Gemini)와 영상 처리 기술(MoviePy)을 활용한 자동화 프로젝트입니다.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![MoviePy](https://img.shields.io/badge/MoviePy-Video_Editing-FFCC00?style=for-the-badge)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-AI-4285F4?style=for-the-badge&logo=google&logoColor=white)

---

## 📌 프로젝트 소개 (Project Overview)
이 프로젝트는 **YouTube Shorts** 제작 과정을 100% 자동화하기 위해 개발되었습니다.  
사용자가 주제(예: "비트코인", "엔비디아")만 입력하면, AI가 자동으로 다음 과정을 수행합니다.

1.  **시나리오 작성:** Google Gemini API가 흥미로운 숏폼용 대본을 작성.
2.  **리소스 수집:** 주제에 맞는 고화질 무료 영상(Pexels API)을 검색 및 다운로드.
3.  **오디오 생성:** TTS(Text-to-Speech)를 활용하여 자연스러운 내레이션 생성.
4.  **영상 편집:** FFmpeg 기반의 MoviePy를 사용하여 자막 합성, 오디오 싱크 조절, 배경 음악 삽입.
5.  **최적화:** 모바일 환경(9:16)에 맞춘 반응형 자막 및 인코딩 최적화.

---

## 📸 실행 화면 (Preview)
*(여기에 완성된 웹사이트 스크린샷이나, 구동되는 GIF를 넣으면 좋습니다)*
> **1. 주제 입력** -> **2. 로딩(제작)** -> **3. 결과물 재생**

---

## 🛠 기술 스택 (Tech Stack)

### **Backend**
-   **Framework:** FastAPI (비동기 처리 및 빠른 API 응답)
-   **AI Model:** Google Gemini 1.5 Flash (대본 작성 및 검색어 추론)
-   **Video Processing:** MoviePy (영상 자르기, 합치기, 자막 렌더링)
-   **Resource:** Pexels API (배경 영상), gTTS (음성 합성)
-   **Optimization:** `ultrafast` 프리셋 인코딩, 멀티스레딩 적용

### **Frontend**
-   **Framework:** React (Vite 기반)
-   **Styling:** CSS3 (Dark Mode, Responsive Design)
-   **State Management:** React Hooks (`useState`)

---

## ⚙️ 주요 기능 (Key Features)

### 1. 🧠 똑똑한 대본 작성 (AI Scripting)
-   단순 검색이 아닌, Gemini LLM을 통해 "유튜브 쇼츠 감성"의 톡톡 튀는 대본을 생성합니다.
-   문장 단위로 정밀하게 분할하여 영상의 리듬감을 살립니다.

### 2. 🎥 스마트한 영상 소스 관리
-   **4K 필터링 로직:** 렌더링 속도 저하를 막기 위해 4K 영상은 제외하고 FHD/HD 영상만 선별합니다.
-   **백업 키워드 검색:** 특정 키워드(예: 신창섭) 영상이 없을 경우, 'Future', 'Technology' 등 대체 테마로 자동 재검색합니다.

### 3. ⚡ 고성능 렌더링 파이프라인
-   **반응형 자막:** 영상 해상도(720p/1080p)에 따라 폰트 크기와 위치가 자동으로 조절됩니다.
-   **리소스 자동 관리:** 작업이 끝나면 임시 파일(mp3, mp4)을 강제 삭제하여 서버 용량을 확보합니다.
-   **속도 최적화:** CPU 스레드 활용 및 `ultrafast` 인코딩 옵션으로 렌더링 시간을 50% 이상 단축했습니다.

---

## 🚀 설치 및 실행 방법 (Getting Started)

### 1. 환경 변수 설정 (.env)
`backend` 폴더 안에 `.env` 파일을 생성하고 API 키를 입력하세요.
```ini
GOOGLE_API_KEY=your_gemini_api_key
PEXELS_API_KEY=your_pexels_api_key

2. 백엔드 실행 (Backend)
Bash

cd backend
# 가상환경 활성화 (선택)
# 라이브러리 설치
pip install -r requirements.txt

# 서버 시작
uvicorn main:app --reload

3. 프론트엔드 실행 (Frontend)
Bash

cd frontend
# 의존성 설치
npm install

# 개발 서버 시작
npm run dev# shorts_ai
