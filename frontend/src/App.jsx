import { useState } from 'react'
import './App.css'

function App() {
  const [topic, setTopic] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [videoUrl, setVideoUrl] = useState(null)
  
  // [NEW] 트렌드(뉴스 제목) 목록을 저장할 상태 변수
  const [trends, setTrends] = useState([]) 

  // API 주소 (환경변수가 없으면 로컬호스트 사용)
  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  // 1. 영상 생성 요청 함수
  const createShorts = async () => {
    if (!topic) return;
    
    setIsLoading(true);
    setVideoUrl(null); // 이전 영상 초기화

    try {
      // 백엔드로 POST 요청 보내기
      const response = await fetch(`${API_BASE_URL}/create-shorts?topic=${encodeURIComponent(topic)}`, {
        method: 'POST',
      });

      const data = await response.json();

      if (data.status === "success") {
        // 성공 시 영상 URL 설정
        // 백엔드에서 받은 파일 경로를 웹 URL로 변환
        const filename = data.file.split(/[/\\]/).pop(); // 파일명만 추출
        setVideoUrl(`${API_BASE_URL}/results/${filename}`);
      } else {
        alert("영상 제작 실패: " + data.msg);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("서버 연결에 실패했습니다.");
    } finally {
      setIsLoading(false); // 로딩 끝
    }
  };

  // [NEW] 2. 핫한 주제(뉴스) 가져오는 함수
  const fetchTrends = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/trends`);
      const data = await response.json();
      
      if (data.status === "success") {
        setTrends(data.topics); // 가져온 뉴스 제목 5개를 저장
      } else {
        alert("트렌드를 가져오는데 실패했습니다.");
      }
    } catch (error) {
      console.error("Error fetching trends:", error);
      alert("서버 연결 실패! 백엔드가 켜져 있나요?");
    }
  };

  // [NEW] 3. 추천 주제 클릭 시 입력창에 넣기
  const handleTrendClick = (trendTitle) => {
    setTopic(trendTitle); // 입력창 채우기
  };

  return (
    <div className="app-container">
      <h1>🎬 AI Shorts Maker</h1>
      <p className="subtitle">키워드만 입력하면 대본부터 영상까지 1분 컷!</p>
      
      {/* 입력 섹션 */}
      <div className="input-section">
        <input 
          type="text" 
          placeholder="주제를 입력하세요 (예: 비트코인)" 
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={isLoading}
          onKeyDown={(e) => e.key === 'Enter' && createShorts()}
        />
        <button 
          className="create-btn"
          onClick={createShorts} 
          disabled={isLoading || !topic}
        >
          {isLoading ? "제작 중... 🕒" : "영상 만들기 🚀"}
        </button>
      </div>

      {/* [NEW] 트렌드 버튼 섹션 */}
      <div className="trend-section">
        <button className="trend-btn" onClick={fetchTrends}>
          🔥 요즘 뭐 핫해? (실시간 추천받기)
        </button>
        
        {/* 트렌드 목록이 있으면 보여주기 */}
        {trends.length > 0 && (
          <div className="trend-list">
            {trends.map((t, index) => (
              <div key={index} className="trend-chip" onClick={() => handleTrendClick(t)}>
                {t}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 로딩 표시 */}
      {isLoading && (
        <div className="loading-msg">
          <p>AI가 대본 쓰고, 영상 찾고, 편집 중입니다...</p>
          <p>(약 30~60초 소요됩니다)</p>
        </div>
      )}

      {/* 결과 영상 섹션 */}
      {videoUrl && (
        <div className="result-section">
          <h2>✨ 완성된 쇼츠</h2>
          <video controls src={videoUrl} className="video-player" autoPlay></video>
          <div className="download-link">
            <a href={videoUrl} download>⬇️ 영상 다운로드</a>
          </div>
        </div>
      )}
    </div>
  )
}

export default App