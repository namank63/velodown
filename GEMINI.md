# Video Downloader - Technical Documentation

This document provides architectural details, coding conventions, and project structure for AI agents and developers working on the Video Downloader project.

## Project Architecture

The project is a full-stack application for downloading videos from various web platforms using `yt-dlp`.

- **Frontend:** React (TypeScript) with Vite. Uses CSS Modules for styling.
- **Backend:** FastAPI (Python). Orchestrates `yt-dlp` for metadata extraction and media downloading.
- **Database:** SQLite for persistent download history.
- **Logging:** Python's `logging` module with a rotating file handler and custom integration for `yt-dlp`.
- **Media Engine:** `yt-dlp` is used for all media interaction.

## Core Workflows

1.  **Metadata Fetching:** Frontend sends a URL to `/api/info`. Backend uses `yt-dlp` in non-download mode to extract formats and metadata.
2.  **Downloading:** Frontend sends a URL and a specific `format_id` to `/api/download`. Backend creates a unique job ID, downloads the media using `yt-dlp`, and serves the resulting file as a `FileResponse`.
3.  **History:** Every download attempt is recorded in `backend/history.db`.
4.  **Static Serving:** In production, the backend serves the built React frontend (`frontend/dist`) from the root `/` path.

## Coding Conventions

### Frontend
- **Type Safety:** Always define interfaces in `src/types.ts`.
- **Styling:** Use CSS Modules (`*.module.css`) to prevent global namespace pollution.
- **Components:** Functional components with Hooks.
- **Dark Mode:** Driven by `data-theme` attribute on the `<html>` or `<body>` element and CSS variables.

### Backend
- **Type Hinting:** Use Pydantic models for request/response validation.
- **Error Handling:** Use `HTTPException` for API errors.
- **Logging:** Use `app_logger` from `logger.py`. Do not use `print()`.
- **Async:** Use `async def` for API endpoints. Background tasks (like cleanup) should use `BackgroundTasks`.

## Project Structure

- `backend/`: Python FastAPI source code.
  - `main.py`: Main application and API routes.
  - `logger.py`: Logging configuration.
  - `database.py`: SQLite interaction.
  - `history.db`: SQLite database file (gitignored).
  - `logs/`: Application logs (gitignored).
  - `temp_downloads/`: Temporary storage for media before serving (gitignored).
- `frontend/`: React Vite source code.
  - `src/App.tsx`: Main UI logic.
  - `src/types.ts`: TypeScript interfaces.
  - `dist/`: Built production files (gitignored).

## Maintenance Tasks

- **Cleanup:** The backend automatically deletes downloaded files after they are served via a `BackgroundTasks` hook.
- **Log Rotation:** `app.log` is capped at 10MB and keeps 5 backups.
