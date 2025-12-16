module.exports = {
  apps: [
    {
      name: "ai-backend",
      script: "uvicorn",
      args: "main:app --host 0.0.0.0 --port 8000",
      cwd: "./backend",
      
      interpreter: "C:\\Users\\504\\miniconda3\\envs\\ai-shorts\\python.exe", 
      
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONIOENCODING: "utf-8"  // 👈 [추가] "이모티콘도 깨지지 말고 출력해!" 라는 뜻
      }
    },
    {
      name: "ai-frontend",
      script: "cmd.exe",
      args: "/c npm run dev",
      cwd: "./frontend"
    }
  ]
};