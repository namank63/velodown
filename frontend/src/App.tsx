import React, { useState, useEffect, useRef } from 'react';
import { 
  Moon, 
  Sun, 
  Download, 
  X, 
  Loader2, 
  Music, 
  Copy, 
  Trash2, 
  Video, 
  Link as LinkIcon, 
  History as HistoryIcon,
  Search,
  CheckCircle2,
  AlertCircle,
  FileVideo,
  ExternalLink,
  ShieldCheck,
  Upload
} from 'lucide-react';
import styles from './App.module.css';
import type { VideoMetadata, DownloadHistoryEntry, VideoItem } from './types';

const API_BASE_URL = import.meta.env.DEV ? 'http://localhost:8000' : '';

// Helper to get or create a persistent visitor ID
const getVisitorId = () => {
  let id = localStorage.getItem('visitorId');
  if (!id) {
    id = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('visitorId', id);
  }
  return id;
};

const visitorId = getVisitorId();

const CookieManager = () => {
  const [status, setStatus] = useState<{exists: boolean, last_updated: string | null} | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/cookies/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (e) {
      console.error('Failed to fetch cookie status', e);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE_URL}/api/cookies`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        alert('Cookies updated successfully!');
        fetchStatus();
      } else {
        const err = await res.json();
        alert(`Upload failed: ${err.detail}`);
      }
    } catch (e) {
      alert('Upload failed due to a network error');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className={`${styles.cookieManager} glass`}>
      <div className={styles.cookieHeader}>
        <ShieldCheck size={18} className={status?.exists ? styles.successIcon : styles.warningIcon} />
        <span>Authentication Cookies: <strong>{status?.exists ? 'Active' : 'Missing'}</strong></span>
      </div>
      <div className={styles.cookieActions}>
        <input 
          type="file" 
          accept=".txt" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleUpload} 
        />
        <button 
          className={styles.uploadButton} 
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? <Loader2 className={styles.spin} size={14} /> : <Upload size={14} />}
          <span>{status?.exists ? 'Update cookies.txt' : 'Upload cookies.txt'}</span>
        </button>
      </div>
      {status?.last_updated && (
        <div className={styles.lastUpdated}>
          Last updated: {new Date(status.last_updated).toLocaleString()}
        </div>
      )}
    </div>
  );
};

function App() {
  const [urlInput, setUrlInput] = useState('');
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [history, setHistory] = useState<DownloadHistoryEntry[]>([]);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const fetchingRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history`, {
        headers: { 'X-Visitor-Id': visitorId }
      });
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  const addVideo = (url: string) => {
    if (!url || fetchingRef.current.has(url)) return;
    
    // Check if already in list
    if (videos.some(v => v.url === url)) return;

    const id = Math.random().toString(36).substr(2, 9);
    const newVideo: VideoItem = {
      id,
      url,
      loading: true,
      error: null,
      metadata: null,
      selectedFormatId: null,
      downloading: false,
      activeTab: 'video'
    };

    setVideos(prev => [newVideo, ...prev]);
    fetchInfo(url, id);
  };

  const fetchInfo = async (url: string, id: string) => {
    fetchingRef.current.add(url);
    try {
      const response = await fetch(`${API_BASE_URL}/api/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to fetch video info');
      }
      
      const data: VideoMetadata = await response.json();
      
      // Auto-select best format using helper
      const bestFormatId = getBestFormatId(data.formats, 'video');

      setVideos(prev => prev.map(v => v.id === id ? {
        ...v,
        loading: false,
        metadata: data,
        selectedFormatId: bestFormatId
      } : v));
    } catch (err: any) {
      setVideos(prev => prev.map(v => v.id === id ? {
        ...v,
        loading: false,
        error: err.message
      } : v));
    } finally {
      fetchingRef.current.delete(url);
    }
  };

  const handleDownload = (video: VideoItem) => {
    if (!video.selectedFormatId || !video.metadata) return;
    
    const noAudio = video.activeTab === 'video_only';
    const downloadUrl = `${API_BASE_URL}/api/download?url=${encodeURIComponent(video.url)}&format_id=${video.selectedFormatId}&visitor_id=${visitorId}${noAudio ? '&no_audio=true' : ''}`;
    
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', '');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setVideos(prev => prev.map(v => v.id === video.id ? { ...v, downloading: true } : v));
    
    setTimeout(() => {
      setVideos(prev => prev.map(v => v.id === video.id ? { ...v, downloading: false } : v));
      fetchHistory();
    }, 3000);
  };

  const handleDownloadAll = () => {
    videos.forEach(video => {
      if (video.metadata && !video.loading && !video.error) {
        handleDownload(video);
      }
    });
  };

  const removeVideo = (id: string) => {
    setVideos(prev => prev.filter(v => v.id !== id));
  };

  const onPaste = (e: React.ClipboardEvent) => {
    const pastedText = e.clipboardData.getData('text');
    if (pastedText.startsWith('http')) {
      addVideo(pastedText);
      setUrlInput('');
    }
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const deleteHistoryItem = async (id: string) => {
    if (!window.confirm('Remove this item from history?')) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/history/${id}`, { 
        method: 'DELETE',
        headers: { 'X-Visitor-Id': visitorId }
      });
      if (response.ok) {
        setHistory(prev => prev.filter(item => item.id !== id));
      }
    } catch (err) {
      console.error('Failed to delete history item', err);
    }
  };

  const clearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear your entire download history?')) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/history`, { 
        method: 'DELETE',
        headers: { 'X-Visitor-Id': visitorId }
      });
      if (response.ok) {
        setHistory([]);
      }
    } catch (err) {
      console.error('Failed to clear history', err);
    }
  };

  const copyAllHistoryLinks = () => {
    const links = history.map(item => item.url).join('\n');
    navigator.clipboard.writeText(links);
    alert('All history links copied to clipboard!');
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setUrlInput(value);
    
    // Auto-fetch if it looks like a full URL
    if (value.startsWith('http://') || value.startsWith('https://')) {
      if (value.length > 12) { 
        addVideo(value);
        setUrlInput('');
      }
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return [h, m, s].map(v => v.toString().padStart(2, '0')).filter((v, i) => v !== '00' || i > 0).join(':');
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp + 'Z');
    return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getBestFormatId = (formats: any[], tab: string) => {
    return formats
      .filter(f => {
        if (tab === 'audio') return f.vcodec === 'none';
        return f.vcodec !== 'none';
      })
      .sort((a, b) => {
        const resA = parseInt(a.resolution?.split('x')[0] || '0');
        const resB = parseInt(b.resolution?.split('x')[0] || '0');
        if (resB !== resA) return resB - resA;
        return (b.filesize || 0) - (a.filesize || 0);
      })[0]?.format_id || null;
  };

  const setTab = (videoId: string, tab: VideoItem['activeTab']) => {
    setVideos(prev => prev.map(v => {
      if (v.id === videoId && v.metadata) {
        return { 
          ...v, 
          activeTab: tab, 
          selectedFormatId: getBestFormatId(v.metadata.formats, tab) 
        };
      }
      return v.id === videoId ? { ...v, activeTab: tab, selectedFormatId: null } : v;
    }));
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <button className={styles.themeToggle} onClick={toggleTheme}>
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          <span>{theme === 'light' ? 'Dark Mode' : 'Light Mode'}</span>
        </button>
        <h1>OmniGrab</h1>
        <p>Seamlessly download media from across the web</p>
      </header>

      <div className={`${styles.searchSection} glass`}>
        <Search className={styles.searchIcon} size={20} />
        <input
          type="text"
          className={styles.input}
          placeholder="Paste link from YouTube, Vimeo, or Twitter..."
          value={urlInput}
          onChange={handleInputChange}
          onPaste={onPaste}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              addVideo(urlInput);
              setUrlInput('');
            }
          }}
        />
      </div>

      <CookieManager />

      {videos.length > 1 && (
        <button className={`${styles.button} ${styles.downloadAll}`} onClick={handleDownloadAll}>
          <Download size={20} />
          Download All ({videos.length})
        </button>
      )}

      <div className={styles.videoList}>
        {videos.map(video => (
          <div key={video.id} className={`${styles.results} glass`}>
            <div className={styles.videoHeader}>
              <div className={styles.urlContainer}>
                <LinkIcon size={14} className={styles.linkIcon} />
                <div className={styles.videoUrl}>{video.url}</div>
                <button className={styles.copyButton} onClick={() => copyToClipboard(video.url)}>
                  <Copy size={12} />
                </button>
              </div>
              <button className={styles.removeButton} onClick={() => removeVideo(video.id)}>
                <X size={20} />
              </button>
            </div>

            {video.loading && (
              <div className={styles.loading}>
                <Loader2 className={styles.spinner} size={24} />
                <span>Analyzing metadata...</span>
              </div>
            )}
            
            {video.error && (
              <div className={styles.error}>
                <AlertCircle size={20} />
                <span>{video.error}</span>
              </div>
            )}

            {video.metadata && (
              <>
                {video.metadata.is_playlist ? (
                  <div className={styles.playlistContainer}>
                    <div className={styles.playlistInfo}>
                      <HistoryIcon size={32} className={styles.playlistIcon} />
                      <div className={styles.playlistDetails}>
                        <h2>Playlist: {video.metadata.title}</h2>
                        <p>{video.metadata.entries?.length || 0} videos found in this playlist</p>
                      </div>
                      <button 
                        className={styles.addPlaylistBtn}
                        onClick={() => {
                          video.metadata?.entries?.forEach(entry => addVideo(entry.url));
                          removeVideo(video.id);
                        }}
                      >
                        <Download size={18} />
                        Add All to Queue
                      </button>
                    </div>
                    <div className={styles.playlistEntries}>
                      {video.metadata.entries?.slice(0, 5).map((entry, i) => (
                        <div key={i} className={styles.playlistEntry}>
                          <span>{i + 1}. {entry.title || 'Unknown Title'}</span>
                        </div>
                      ))}
                      {(video.metadata.entries?.length || 0) > 5 && (
                        <div className={styles.playlistMore}>
                          And {video.metadata.entries!.length - 5} more videos...
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <>
                    <div className={styles.videoInfo}>
                      {video.metadata.thumbnail && (
                        <div className={styles.thumbnailWrapper}>
                          <img src={video.metadata.thumbnail} alt="Thumbnail" className={styles.thumbnail} />
                          {video.metadata.duration && (
                            <span className={styles.durationBadge}>{formatDuration(video.metadata.duration)}</span>
                          )}
                        </div>
                      )}
                      <div className={styles.details}>
                        <h2>{video.metadata.title}</h2>
                        <div className={styles.actionRow}>
                           <button 
                            className={styles.downloadBtn} 
                            onClick={() => handleDownload(video)}
                            disabled={video.downloading || !video.selectedFormatId}
                          >
                            {video.downloading ? (
                              <>
                                <Loader2 className={styles.spinner} size={20} />
                                <span>Processing...</span>
                              </>
                            ) : (
                              <>
                                <Download size={20} />
                                <span>Download High Quality</span>
                              </>
                            )}
                          </button>
                        </div>
                        {video.downloading && (
                          <div className={styles.processingText}>
                            <CheckCircle2 size={14} />
                            The server is merging high-quality streams.
                          </div>
                        )}
                      </div>
                    </div>

                    <div className={styles.tabs}>
                      <button 
                        className={`${styles.tab} ${video.activeTab === 'video' ? styles.tabActive : ''}`}
                        onClick={() => setTab(video.id, 'video')}
                      >
                        <Video size={16} />
                        Video
                      </button>
                      <button 
                        className={`${styles.tab} ${video.activeTab === 'audio' ? styles.tabActive : ''}`}
                        onClick={() => setTab(video.id, 'audio')}
                      >
                        <Music size={16} />
                        Audio
                      </button>
                      <button 
                        className={`${styles.tab} ${video.activeTab === 'video_only' ? styles.tabActive : ''}`}
                        onClick={() => setTab(video.id, 'video_only')}
                      >
                        <FileVideo size={16} />
                        No Audio
                      </button>
                    </div>

                    <div className={styles.formatGrid}>
                      {video.metadata.formats
                        .filter(f => {
                          if (video.activeTab === 'audio') return f.vcodec === 'none';
                          return f.vcodec !== 'none';
                        })
                        .sort((a, b) => {
                          const resA = parseInt(a.resolution?.split('x')[0] || '0');
                          const resB = parseInt(b.resolution?.split('x')[0] || '0');
                          if (resB !== resA) return resB - resA;
                          return (b.filesize || 0) - (a.filesize || 0);
                        })
                        .map((f) => (
                        <div 
                          key={f.format_id} 
                          className={`${styles.formatCard} ${video.selectedFormatId === f.format_id ? styles.formatCardActive : ''}`}
                          onClick={() => setVideos(prev => prev.map(v => v.id === video.id ? { ...v, selectedFormatId: f.format_id } : v))}
                        >
                          <span className={styles.ext}>{f.ext.toUpperCase()}</span>
                          <span className={styles.res}>
                            {f.vcodec === 'none' ? 'High Fidelity Audio' : (f.resolution || 'Video')}
                          </span>
                          <span className={styles.size}>{formatSize(f.filesize)}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      {history.length > 0 && (
        <div className={styles.historySection}>
          <div className={styles.historyHeader}>
            <div className={styles.historyTitleRow}>
              <HistoryIcon size={20} />
              <h3>Recent Downloads</h3>
            </div>
            <div className={styles.historyActions}>
              <button className={styles.copyAllButton} onClick={copyAllHistoryLinks}>
                <Copy size={14} />
                <span>Copy All Links</span>
              </button>
              <button className={styles.clearButton} onClick={clearHistory}>
                <Trash2 size={14} />
                <span>Clear All</span>
              </button>
            </div>
          </div>
          <div className={styles.historyList}>
            {history.map((item) => (
              <div key={item.id} className={`${styles.historyItem} glass`}>
                {item.thumbnail && (
                  <img src={item.thumbnail} alt="" className={styles.historyThumbnail} />
                )}
                <div className={styles.historyMain}>
                  <div className={styles.historyTitle}>{item.title || 'Unknown Title'}</div>
                  <div className={styles.historyUrlRow}>
                    <span className={styles.historyUrl}>{item.url}</span>
                    <a href={item.url} target="_blank" rel="noreferrer" className={styles.externalLink}>
                      <ExternalLink size={12} />
                    </a>
                  </div>
                </div>
                <div className={styles.historyMeta}>
                  <span className={`${styles.status} ${styles[`status_${item.status}`]}`}>
                    {item.status}
                  </span>
                  <span className={styles.historyTime}>{formatTime(item.timestamp)}</span>
                  <button className={styles.historyDelete} onClick={() => deleteHistoryItem(item.id)}>
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <footer className={styles.footer}>
        v1.0.3 • Build: 2026-04-29 18:45:10
      </footer>
    </div>
  );
}

export default App;
