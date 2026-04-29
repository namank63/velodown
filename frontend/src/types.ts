export interface FormatInfo {
    format_id: string;
    ext: string;
    resolution?: string;
    filesize?: number;
    vcodec?: string;
    acodec?: string;
    format_note?: string;
}

export interface VideoMetadata {
    title: string;
    duration?: number;
    thumbnail?: string;
    formats: FormatInfo[];
    url: string;
}

export interface DownloadHistoryEntry {
    id: string;
    url: string;
    title?: string;
    format_id?: string;
    status: 'started' | 'completed' | 'failed';
    timestamp: string;
    file_path?: string;
}

export interface VideoItem {
    id: string;
    url: string;
    loading: boolean;
    error: string | null;
    metadata: VideoMetadata | null;
    selectedFormatId: string | null;
    downloading: boolean;
    activeTab: 'video' | 'audio' | 'video_only';
}
