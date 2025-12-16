import { useState } from 'react';
import './App.css'; // 스타일 파일 불러오기

function App() {
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState('주제를 입력하고 버튼을 누르세요!');
  const [isLoading, setIsLoading] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);

  const handleCreateShorts = async () => {
    if (!topic) {
      alert("주제를 입력해주세요!");
      return;
    }

    // 상태 초기화
    setIsLoading(true);
    setVideoUrl(null);
    setStatus("🤖 AI가 대본을 쓰고 영상을 편집하고 있어요... (약 1~2분 소요)");

    try {
      // 백엔드 요청 (FastAPI 포트가 8000인지 확인!)
      const response = await fetch(`http://127.0.0.1:8000/create-shorts?topic=${encodeURIComponent(topic)}`, {
        method: 'POST',
      });

      const data = await response.json();

      if (data.status === "success") {
        setStatus("✨ 영상 제작 완료!");
        // 파일 경로에서 파일명만 추출해서 URL 완성
        // 예: backend/results/shorts_abc.mp4 -> shorts_abc.mp4
        const filename = data.file.split(/[\\/]/).pop();
        setVideoUrl(`http://127.0.0.1:8000/results/${filename}`);
      } else {
        setStatus("❌ 실패: " + data.msg);
      }

    } catch (error) {
      console.error(error);
      setStatus("❌ 에러 발생! 백엔드 서버가 켜져 있나요?");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>🎬 AI Shorts Maker</h1>
      
      <div className="card">
        <input 
          type="text" 
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="주제를 입력하세요 (예: 비트코인, 엔비디아)"
          disabled={isLoading}
        />
        
        <button onClick={handleCreateShorts} disabled={isLoading}>
          {isLoading ? "제작 중..." : "영상 만들기 ✨"}
        </button>
        
        <div className="status-text">{status}</div>

        {/* 로딩 중일 때만 보이는 스피너 */}
        {isLoading && <div className="loader"></div>}
        
        {/* 영상이 완성되면 보이는 비디오 플레이어 */}
        {videoUrl && (
          <video controls autoPlay loop src={videoUrl} className="result-video">
            브라우저가 비디오 태그를 지원하지 않습니다.
          </video>
        )}
      </div>
    </div>
  );
}

export default App;