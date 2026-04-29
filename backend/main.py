import os
import uuid
import shutil
import asyncio
from typing import List, Optional, Annotated
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
from contextlib import asynccontextmanager

from logger import app_logger, yt_logger
from database import add_download, update_download_status, get_history, clear_history

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Application starting up...")
    yield
    app_logger.info("Application shutting down...")

app = FastAPI(title="Video Downloader API", lifespan=lifespan)

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
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

class VideoMetadata(BaseModel):
    title: str
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    formats: List[FormatInfo]
    url: str

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/info", response_model=VideoMetadata)
async def get_video_info(data: VideoURL):
    app_logger.info(f"Fetching info for URL: {data.url}")
    ydl_opts = {
        'logger': yt_logger,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                    formats.append(FormatInfo(
                        format_id=f.get('format_id'),
                        ext=f.get('ext'),
                        resolution=f.get('resolution'),
                        filesize=f.get('filesize') or f.get('filesize_approx'),
                        vcodec=f.get('vcodec'),
                        acodec=f.get('acodec'),
                        format_note=f.get('format_note')
                    ))
            
            app_logger.info(f"Successfully fetched info for: {info.get('title')}")
            return VideoMetadata(
                title=info.get('title'),
                duration=info.get('duration'),
                thumbnail=info.get('thumbnail'),
                formats=formats,
                url=data.url
            )
    except Exception as e:
        app_logger.error(f"Error fetching info for {data.url}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

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
    
    ydl_opts = {
        'format': format_id if no_audio else f"{format_id}+bestaudio/best",
        'outtmpl': output_template,
        'logger': yt_logger,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title')
            
            files = os.listdir(job_dir)
            if not files:
                 update_download_status(job_id, 'failed')
                 app_logger.error(f"Download failed for job {job_id}: File not found")
                 raise HTTPException(status_code=500, detail="Download failed: File not found")
            
            actual_filename = os.path.join(job_dir, files[0])
            
            update_download_status(job_id, 'completed', title=title, file_path=actual_filename)
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
        return {"message": "Video Downloader API is running. UI not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
