import { useState } from 'react'
import './App.css'

function App() {
  const [topic, setTopic] = useState("")
  const [script, setScript] = useState("") // AI가 써준 대본 저장
  const [step, setStep] = useState(1) // 1:입력, 2:대본수정, 3:완료
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState("") // 로딩 메시지 세분화
  const [videoUrl, setVideoUrl] = useState(null)
  
  const [trends, setTrends] = useState([]) 

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  // [1단계] 대본 생성 요청
  const generateScript = async () => {
    if (!topic) return;
    
    setIsLoading(true);
    setLoadingMsg("AI 편집장이 뉴스를 분석하고 대본을 쓰고 있습니다... 📝");

    try {
      const response = await fetch(`${API_BASE_URL}/generate-script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic })
      });

      const data = await response.json();

      if (data.status === "success") {
        setScript(data.script); // 대본 상태 저장
        setStep(2); // 수정 화면으로 이동
      } else {
        alert("대본 생성 실패: " + data.msg);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("서버 연결 실패");
    } finally {
      setIsLoading(false);
    }
  };

  // [2단계] 영상 제작 요청 (수정된 대본 사용)
  const createVideo = async () => {
    setIsLoading(true);
    setLoadingMsg("AI가 영상을 찾고, 목소리를 입히고 있습니다... 🎬 (약 1분 소요)");

    try {
      const response = await fetch(`${API_BASE_URL}/make-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          topic: topic, 
          final_script: script // 수정된 대본 전송
        })
      });

      const data = await response.json();

      if (data.status === "success") {
        setVideoUrl(`${API_BASE_URL}${data.video_url}`);
        setStep(3); // 결과 화면으로 이동
      } else {
        alert("영상 제작 실패: " + data.msg);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("영상 제작 중 오류 발생");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTrends = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/trends`);
      const data = await response.json();
      if (data.status === "success") setTrends(data.topics);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const handleTrendClick = (trendTitle) => {
    setTopic(trendTitle);
  };

  // 처음으로 돌아가기
  const resetAll = () => {
    setStep(1);
    setTopic("");
    setScript("");
    setVideoUrl(null);
  }

  return (
    <div className="app-container">
      <h1>🎬 AI Shorts Maker</h1>
      
      {/* --- [STEP 1] 주제 입력 화면 --- */}
      {step === 1 && (
        <div className="step-container">
            <p className="subtitle">어떤 주제로 쇼츠를 만들까요?</p>
            <div className="input-section">
                <input 
                    type="text" 
                    placeholder="예: 비트코인 1억 돌파, 아이폰 16 출시" 
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && generateScript()}
                    disabled={isLoading}
                />
                <button 
                    className="create-btn"
                    onClick={generateScript} 
                    disabled={isLoading || !topic}
                >
                    {isLoading ? "분석 중..." : "대본 쓰기 📝"}
                </button>
            </div>

            <div className="trend-section">
                <button className="trend-btn" onClick={fetchTrends}>
                🔥 요즘 핫한 뉴스 추천받기
                </button>
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
        </div>
      )}

      {/* --- [STEP 2] 대본 수정 화면 --- */}
      {step === 2 && (
        <div className="step-container">
            <h2>📝 대본 확인 및 수정</h2>
            <p className="desc">AI가 쓴 대본입니다. 마음에 안 드는 부분은 직접 수정하세요!</p>
            
            <textarea 
                className="script-editor"
                value={script}
                onChange={(e) => setScript(e.target.value)}
                placeholder="여기서 대본을 자유롭게 수정하세요..."
            />
            
            <div className="button-group">
                <button className="secondary-btn" onClick={() => setStep(1)}>
                    ⬅️ 다시 주제 정하기
                </button>
                <button 
                    className="create-btn" 
                    onClick={createVideo}
                    disabled={isLoading}
                >
                    {isLoading ? "제작 중..." : "이대로 영상 만들기 🎬"}
                </button>
            </div>
        </div>
      )}

      {/* --- [STEP 3] 결과 확인 화면 --- */}
      {step === 3 && videoUrl && (
        <div className="step-container">
            <h2>✨ 완성된 쇼츠</h2>
            <div className="video-wrapper">
                <video controls src={videoUrl} className="video-player" autoPlay></video>
            </div>
            <div className="button-group">
                <a href={videoUrl} download className="download-btn">
                    ⬇️ 영상 다운로드
                </a>
                <button className="secondary-btn" onClick={resetAll}>
                    🔄 처음으로
                </button>
            </div>
        </div>
      )}

      {/* 공통 로딩 오버레이 */}
      {isLoading && (
        <div className="loading-overlay">
            <div className="spinner"></div>
            <p>{loadingMsg}</p>
        </div>
      )}
    </div>
  )
}

export default App