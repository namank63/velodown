import os
import uuid
import shutil
import asyncio
import random
from datetime import datetime
from typing import List, Optional, Annotated
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
from contextlib import asynccontextmanager

from logger import app_logger, yt_logger
from database import add_download, update_download_status, get_history, clear_history, delete_single_history

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Application starting up...")
    yield
    app_logger.info("Application shutting down...")

app = FastAPI(title="OmniGrab API", lifespan=lifespan)

# Enable CORS (primarily for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "temp_downloads")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_available_browsers():
    """Detect which browsers are installed and have user data on Windows."""
    browsers = []
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    app_data = os.environ.get('APPDATA', '')
    
    mapping = {
        'chrome': os.path.join(local_app_data, 'Google', 'Chrome', 'User Data'),
        'edge': os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data'),
        'brave': os.path.join(local_app_data, 'BraveSoftware', 'Brave-Browser', 'User Data'),
        'vivaldi': os.path.join(local_app_data, 'Vivaldi', 'User Data'),
        'firefox': os.path.join(app_data, 'Mozilla', 'Firefox', 'Profiles'),
    }
    
    for b, path in mapping.items():
        if os.path.exists(path):
            browsers.append(b)
    
    # Priority order for trying browsers
    priority = ['chrome', 'edge', 'brave', 'vivaldi', 'firefox']
    return sorted(browsers, key=lambda x: priority.index(x) if x in priority else 99)

def get_ydl_opts(download=False, extra_opts=None, browser=None):
    # Rotating mobile user agents to look like different devices
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.179 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 14; Samsung Galaxy S24 Ultra) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.179 Mobile Safari/537.36'
    ]
    
    opts = {
        'logger': yt_logger,
        'no_warnings': True,
        'quiet': True,
        'user_agent': random.choice(user_agents),
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        # Explicitly tell yt-dlp to use the system's JS runtime (Node.js) for signature challenges
        'javascript_runtime': 'node', 
    }
    
    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE
    elif browser:
        opts['cookiesfrombrowser'] = (browser,)
        
    if extra_opts:
        opts.update(extra_opts)
        
    return opts

class VideoURL(BaseModel):
    url: str

class FormatInfo(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    filesize: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    format_note: Optional[str] = None

class PlaylistEntry(BaseModel):
    url: str
    title: Optional[str] = None

class VideoMetadata(BaseModel):
    title: str
    duration: Optional[float] = None
    thumbnail: Optional[str] = None
    formats: List[FormatInfo]
    url: str
    is_playlist: bool = False
    entries: Optional[List[PlaylistEntry]] = None

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/cookies")
async def upload_cookies(file: UploadFile = File(...)):
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    
    try:
        content = await file.read()
        with open(COOKIES_FILE, "wb") as f:
            f.write(content)
        app_logger.info(f"Cookies updated via API. Path: {COOKIES_FILE}")
        return {"message": "Cookies updated successfully"}
    except Exception as e:
        app_logger.error(f"Error uploading cookies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save cookies: {str(e)}")

@app.get("/api/cookies/status")
async def get_cookies_status():
    exists = os.path.exists(COOKIES_FILE)
    mtime = os.path.getmtime(COOKIES_FILE) if exists else None
    return {
        "exists": exists,
        "last_updated": datetime.fromtimestamp(mtime).isoformat() if mtime else None
    }

@app.post("/api/info", response_model=VideoMetadata)
async def get_video_info(data: VideoURL):
    app_logger.info(f"Fetching info for URL: {data.url}")
    
    # 1. Try with cookies from various browsers sequentially
    browsers = get_available_browsers()
    for browser in browsers:
        try:
            app_logger.info(f"Trying to fetch info using cookies from {browser}...")
            ydl_opts = get_ydl_opts(extra_opts={'extract_flat': 'in_playlist'}, browser=browser)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(data.url, download=False)
                return process_info(info, data.url)
        except Exception as e:
            app_logger.warning(f"Failed with {browser} cookies: {str(e)}")
            continue

    # 2. Try with cookies.txt if it exists
    if os.path.exists(COOKIES_FILE):
        try:
            app_logger.info("Trying to fetch info using cookies.txt...")
            ydl_opts = get_ydl_opts(extra_opts={'extract_flat': 'in_playlist'})
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(data.url, download=False)
                return process_info(info, data.url)
        except Exception as e:
            app_logger.warning(f"Failed with cookies.txt: {str(e)}")

    # 3. Final Fallback: Try without cookies
    app_logger.info("Attempting final fallback without cookies...")
    try:
        ydl_opts_no_cookies = get_ydl_opts(extra_opts={'extract_flat': 'in_playlist'})
        with yt_dlp.YoutubeDL(ydl_opts_no_cookies) as ydl:
            info = ydl.extract_info(data.url, download=False)
            return process_info(info, data.url)
    except Exception as e:
        app_logger.error(f"All extraction attempts failed for {data.url}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def process_info(info, url):
    if not info:
        raise HTTPException(status_code=404, detail="Could not extract video information")

    # Check if it's a playlist
    if 'entries' in info:
        app_logger.info(f"Playlist detected: {info.get('title')} with {len(list(info.get('entries', [])))} entries")
        entries = []
        for entry in info.get('entries', []):
            if entry:
                entries.append(PlaylistEntry(
                    url=entry.get('url') or entry.get('webpage_url') or entry.get('id'),
                    title=entry.get('title')
                ))
        
        return VideoMetadata(
            title=info.get('title') or "Playlist",
            formats=[],
            url=url,
            is_playlist=True,
            entries=entries
        )

    # Efficiently filter and deduplicate formats on the backend
    processed_formats = []
    seen_keys = set()
    
    raw_formats = info.get('formats', [])
    
    for f in raw_formats:
        vcodec = f.get('vcodec', 'none')
        acodec = f.get('acodec', 'none')
        
        if vcodec == 'none' and acodec == 'none':
            continue
        
        res = f.get('resolution') or (f"{f.get('width')}x{f.get('height')}" if f.get('width') else 'audio')
        ext = f.get('ext', 'mp4')
        is_audio_only = vcodec == 'none'
        
        key = (res, ext, is_audio_only)
        
        if key in seen_keys:
            continue
        
        seen_keys.add(key)
        
        processed_formats.append(FormatInfo(
            format_id=f.get('format_id'),
            ext=ext,
            resolution=f.get('resolution'),
            filesize=f.get('filesize') or f.get('filesize_approx'),
            vcodec=vcodec,
            acodec=acodec,
            format_note=f.get('format_note')
        ))
    
    app_logger.info(f"Successfully fetched and optimized info for: {info.get('title')} ({len(processed_formats)} formats)")
    return VideoMetadata(
        title=info.get('title') or "Unknown Title",
        duration=info.get('duration'),
        thumbnail=info.get('thumbnail'),
        formats=processed_formats,
        url=url,
        is_playlist=False
    )

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)
        app_logger.debug(f"Cleaned up file: {path}")
    parent = os.path.dirname(path)
    if os.path.exists(parent) and not os.listdir(parent) and parent != DOWNLOAD_DIR:
        shutil.rmtree(parent)
        app_logger.debug(f"Cleaned up directory: {parent}")

@app.get("/api/download")
async def download_video(
    background_tasks: BackgroundTasks,
    url: str = Query(...),
    format_id: str = Query(...),
    visitor_id: str = Query(...),
    no_audio: bool = Query(False)
):
    job_id = str(uuid.uuid4())
    app_logger.info(f"Starting download job {job_id} for URL: {url} (Format: {format_id}, No Audio: {no_audio}, Visitor: {visitor_id})")
    
    # Record in history
    add_download(job_id, url, visitor_id, format_id=format_id, status='started')
    
    job_dir = os.path.join(DOWNLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    output_template = os.path.join(job_dir, '%(title)s.%(ext)s')
    
    ydl_opts = get_ydl_opts(download=True, extra_opts={
        'format': format_id if no_audio else f"{format_id}+bestaudio/best",
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
    })
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title')
            thumbnail = info.get('thumbnail')
            
            files = os.listdir(job_dir)
            if not files:
                 update_download_status(job_id, 'failed')
                 app_logger.error(f"Download failed for job {job_id}: File not found")
                 raise HTTPException(status_code=500, detail="Download failed: File not found")
            
            actual_filename = os.path.join(job_dir, files[0])
            
            update_download_status(job_id, 'completed', title=title, file_path=actual_filename, thumbnail=thumbnail)
            app_logger.info(f"Download completed for job {job_id}: {actual_filename}")
            
            background_tasks.add_task(cleanup_file, actual_filename)
            
            return FileResponse(
                path=actual_filename,
                filename=os.path.basename(actual_filename),
                media_type='application/octet-stream'
            )
            
    except Exception as e:
        update_download_status(job_id, 'failed')
        app_logger.error(f"Error in download job {job_id}: {str(e)}")
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/history")
async def get_download_history(x_visitor_id: Annotated[Optional[str], Header()] = None):
    if not x_visitor_id:
        return []
    try:
        history = get_history(x_visitor_id)
        return history
    except Exception as e:
        app_logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch history")

@app.delete("/api/history")
async def delete_download_history(x_visitor_id: Annotated[Optional[str], Header()] = None):
    if not x_visitor_id:
        raise HTTPException(status_code=400, detail="Visitor ID required")
    try:
        clear_history(x_visitor_id)
        return {"message": "History cleared"}
    except Exception as e:
        app_logger.error(f"Error clearing history: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not clear history")

@app.delete("/api/history/{job_id}")
async def delete_single_history_item(job_id: str, x_visitor_id: Annotated[Optional[str], Header()] = None):
    if not x_visitor_id:
        raise HTTPException(status_code=400, detail="Visitor ID required")
    try:
        delete_single_history(job_id, x_visitor_id)
        return {"message": "History item deleted"}
    except Exception as e:
        app_logger.error(f"Error deleting history item: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not delete history item")

# Mount frontend static files
# Look for frontend/dist relative to this file's location
frontend_dist = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")

if os.path.exists(frontend_dist):
    app_logger.info(f"Serving frontend from {frontend_dist}")
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    app_logger.warning(f"Frontend dist directory not found at {frontend_dist}. API is running, but UI will not be served.")
    @app.get("/")
    async def root():
        return {"message": "OmniGrab API is running. UI not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
