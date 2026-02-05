import { useState } from 'react'
import './App.css'

function App() {
  const [topic, setTopic] = useState("")
  const [script, setScript] = useState("")
  const [step, setStep] = useState(1) 
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState("")
  const [videoUrl, setVideoUrl] = useState(null)
  const [trends, setTrends] = useState([]) 

  // --- 사용자 옵션 ---
  const [duration, setDuration] = useState("50초")    // 영상 길이 (STEP 1)
  const [voice, setVoice] = useState("female")        // 목소리
  const [speed, setSpeed] = useState("1.2")           // 배속 (STEP 2)
  const [useSubs, setUseSubs] = useState(true)        // 자막 ON/OFF
  const [subPos, setSubPos] = useState("bottom")      // 자막 위치

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  // 1단계: 대본 생성
  const generateScript = async () => {
    if (!topic) return;
    setIsLoading(true);
    setLoadingMsg("AI 편집장이 대본을 작성 중입니다... (길이: " + duration + ") 📝");

    try {
      const response = await fetch(`${API_BASE_URL}/generate-script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            topic, 
            duration // 길이 정보 전송
        })
      });
      const data = await response.json();
      if (data.status === "success") {
        setScript(data.script);
        setStep(2);
      } else { alert("실패: " + data.msg); }
    } catch (e) { alert("서버 에러"); } 
    finally { setIsLoading(false); }
  };

  // 2단계: 영상 제작
  const createVideo = async () => {
    setIsLoading(true);
    setLoadingMsg("영상을 렌더링 중입니다... (속도: " + speed + "배) 🎬");

    try {
      const response = await fetch(`${API_BASE_URL}/make-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          topic, 
          final_script: script,
          voice, 
          speed, // 배속 정보 전송
          use_subtitles: useSubs, 
          subtitle_pos: subPos
        })
      });
      const data = await response.json();
      if (data.status === "success") {
        setVideoUrl(`${API_BASE_URL}${data.video_url}`);
        setStep(3);
      } else { alert("제작 실패: " + data.msg); }
    } catch (e) { alert("오류 발생"); } 
    finally { setIsLoading(false); }
  };

  const fetchTrends = async () => {
    try {
        const res = await fetch(`${API_BASE_URL}/trends`);
        const data = await res.json();
        if(data.status==="success") setTrends(data.topics);
    } catch(e) {}
  };

  return (
    <div className="app-container">
      <h1>🎬 AI Shorts Maker Pro</h1>
      
      {/* STEP 1: 설정 및 대본 요청 */}
      {step === 1 && (
        <div className="step-container">
            <p className="subtitle">주제와 목표 길이를 설정하세요</p>
            
            <div className="input-group">
                <input 
                    type="text" 
                    placeholder="예: 비트코인 1억 돌파" 
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="main-input"
                />
                {/* 영상 길이 선택 */}
                <select value={duration} onChange={(e)=>setDuration(e.target.value)} className="option-select">
                    <option value="30초">⚡ 30초 (Short)</option>
                    <option value="50초">📺 50초 (Standard)</option>
                    <option value="90초">📜 90초 (Long)</option>
                </select>
            </div>
            
            <button className="create-btn" onClick={generateScript} disabled={isLoading || !topic}>
                대본 생성하기 📝
            </button>

            <div className="trend-section">
                <button className="trend-btn" onClick={fetchTrends}>🔥 트렌드 추천</button>
                <div className="trend-list">
                    {trends.map((t, i) => <div key={i} className="trend-chip" onClick={()=>setTopic(t)}>{t}</div>)}
                </div>
            </div>
        </div>
      )}

      {/* STEP 2: 대본 수정 및 영상 옵션 설정 */}
      {step === 2 && (
        <div className="step-container">
            <h2>⚙️ 영상 스타일 설정</h2>
            
            <div className="options-grid">
                <div className="option-item">
                    <label>🎙️ 목소리</label>
                    <select value={voice} onChange={(e)=>setVoice(e.target.value)}>
                        <option value="female">여성 (선희)</option>
                        <option value="male">남성 (인준)</option>
                    </select>
                </div>
                {/* 배속 설정 */}
                <div className="option-item">
                    <label>⏩ 말하기 속도</label>
                    <select value={speed} onChange={(e)=>setSpeed(e.target.value)}>
                        <option value="1.0">1.0x (보통)</option>
                        <option value="1.2">1.2x (빠름-추천)</option>
                        <option value="1.5">1.5x (매우 빠름)</option>
                    </select>
                </div>
                <div className="option-item">
                    <label>💬 자막</label>
                    <div className="toggle-wrapper">
                        <label><input type="checkbox" checked={useSubs} onChange={(e)=>setUseSubs(e.target.checked)}/> 켜기</label>
                    </div>
                </div>
                {useSubs && (
                    <div className="option-item">
                        <label>📍 자막 위치</label>
                        <select value={subPos} onChange={(e)=>setSubPos(e.target.value)}>
                            <option value="bottom">하단</option>
                            <option value="middle">중앙</option>
                            <option value="top">상단</option>
                        </select>
                    </div>
                )}
            </div>

            <textarea className="script-editor" value={script} onChange={(e)=>setScript(e.target.value)} />

            <div className="button-group">
                <button className="secondary-btn" onClick={()=>setStep(1)}>뒤로</button>
                <button className="create-btn" onClick={createVideo}>영상 만들기 🎬</button>
            </div>
        </div>
      )}

      {/* STEP 3: 결과 */}
      {step === 3 && videoUrl && (
        <div className="step-container">
            <h2>✨ 완성!</h2>
            <video controls src={videoUrl} className="video-player" autoPlay></video>
            <div className="button-group">
                <a href={videoUrl} download className="download-btn">다운로드</a>
                <button className="secondary-btn" onClick={()=>setStep(1)}>처음으로</button>
            </div>
        </div>
      )}

      {isLoading && <div className="loading-overlay"><div className="spinner"></div><p>{loadingMsg}</p></div>}
    </div>
  )
}

export default App