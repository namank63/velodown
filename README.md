# 🚀 OmniGrab

A modern, fast, and feature-rich web application to download videos from YouTube, Vimeo, and 1000+ other sites. Built with FastAPI, React, and `yt-dlp`.

## ✨ Features

- **Multi-Video Support:** Paste multiple links and download them all at once.
- **Auto-Fetching:** Simply paste a link and the app immediately starts analyzing it—no clicking required.
- **Dark Mode:** Easy on the eyes with a sleek dark theme toggle.
- **Download History:** Keep track of your past downloads with a persistent history log.
- **Mobile Friendly:** Designed to work across devices on your local network or via the internet.
- **Comprehensive Logging:** Detailed logs for both the application and the `yt-dlp` engine.

## 🛠️ Tech Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Frontend:** [React](https://reactjs.org/) (TypeScript)
- **Engine:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Database:** SQLite
- **Build Tool:** Vite

## 🚀 Quick Start

### One-Click Start (Windows)
1. **Double-click `start_app.bat`**: This will build the frontend, start the backend, and open an ngrok tunnel automatically.
2. **Access the app**:
   - Local: `http://localhost:8000`
   - Mobile: Use the URL shown in the ngrok terminal window.

### One-Click Stop (Windows)
1. **Double-click `stop_app.bat`**: This will safely kill all background processes (Python and Ngrok).

### Manual Setup

1. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access the app:**
   Open `http://localhost:5173` (Frontend dev server) or `http://localhost:8000` (Backend API).

## 📱 Mobile Access (ngrok)

To use the app on your mobile device over the internet:

1. **Build the frontend:**
   ```bash
   cd frontend
   npm run build
   ```
2. **Start the backend:**
   ```bash
   cd backend
   python main.py
   ```
3. **Run ngrok:**
   ```bash
   ngrok http 8000
   ```
4. Open the ngrok URL on your mobile phone!

## 📄 License
MIT
