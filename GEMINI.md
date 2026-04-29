# OmniGrab - Technical Documentation & Agent Mandates

This document provides foundational architecture, coding conventions, and operational mandates for OmniGrab. **All agents must strictly adhere to these guidelines.**

## 📋 Task Management Mandate

**Whenever the user mentions "work", "do task", "pending items", or anything related to current work/tasks:**
1.  Locate the `To-Do.txt` file in the project root.
2.  Identify tasks that start with a number followed by a period (e.g., `1.`), a closing parenthesis (e.g., `1)`), or a dash (e.g., `1-`).
3.  Ignore any lines or sections that do not follow this numbering convention.
4.  Propose the next logical task from this list and wait for user confirmation before starting.

## 🏗️ Project Architecture

OmniGrab is a high-performance media acquisition suite leveraging `yt-dlp`.

### High-Level Flow
1.  **Ingress:** Frontend accepts URLs (manual input or paste).
2.  **Analysis (`/api/info`):** FastAPI invokes `yt-dlp --dump-json` to extract streams, metadata, and thumbnails.
3.  **Selection:** Frontend filters and presents streams (Video, Audio, Video-only) with auto-selection of the highest quality.
4.  **Acquisition (`/api/download`):** Backend spawns an optimized `yt-dlp` process to download and merge streams (FFmpeg-based).
5.  **Egress:** Completed files are streamed to the client; server-side copies are purged post-delivery.
6.  **Persistence:** SQLite tracks successful/failed downloads for session history.

## 🎨 UI/UX Standards

- **Theme:** Adaptive Dark/Light modes via `data-theme` and CSS variables.
- **Glassmorphism:** Use the `.glass` utility class for elevated components (cards, search bars).
- **Icons:** Use **Lucide React exclusively**. Avoid emojis or stock icons.
- **Background:** Mesh gradient radial patterns (defined in `global.css`).
- **Typography:** Inter (Sans-serif) with heavy weights for headings.

## 💻 Backend Conventions

- **Concurrency:** Asynchronous endpoints (`async def`) for non-blocking I/O.
- **Safety:** Strict Pydantic models for request validation.
- **Engine:** `yt-dlp` interaction is isolated; no direct shell execution without sanitization.
- **Storage:** Temporary files live in `backend/temp_downloads/` and are strictly managed.

## 🗃️ Project Structure

- `backend/`: FastAPI source.
  - `main.py`: Primary API surface.
  - `database.py`: SQLite/SQLAlchemy layer.
  - `logger.py`: Centralized logging.
- `frontend/`: React + Vite source.
  - `src/App.tsx`: Core UI orchestrator.
  - `src/App.module.css`: Scoped component styling.
  - `src/global.css`: Global variables and mesh background.
- `To-Do.txt`: Source of truth for active development tasks.

## 🚀 Versioning & Deployment Mandate

**For every code modification turn that involves a commit or push:**
1.  Locate the build version indicator in `frontend/src/App.tsx` (found in the `<footer>` tag).
2.  Increment the version number (e.g., `v1.0.1` -> `v1.0.2`).
3.  Update the "Build" timestamp with the current date and time in `YYYY-MM-DD HH:MM:SS` format.
4.  Ensure the change is built (`npm run build`) before pushing.
