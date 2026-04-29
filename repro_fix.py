import yt_dlp
import os

def test_url():
    url = "https://youtu.be/RTZW6Mh48eM?si=OI0DcsodDwBexPpV"
    
    # Simulate the logic in main.py
    browser = 'chrome'
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    app_data = os.environ.get('APPDATA', '')
    
    if not os.path.exists(os.path.join(local_app_data, 'Google', 'Chrome', 'User Data')):
        if os.path.exists(os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data')):
            browser = 'edge'
        elif os.path.exists(os.path.join(app_data, 'Mozilla', 'Firefox', 'Profiles')):
            browser = 'firefox'
            
    print(f"Testing with browser: {browser}")
    
    ydl_opts = {
        'quiet': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
        'cookiesfrombrowser': browser,
        'extract_flat': 'in_playlist'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"SUCCESS: {info.get('title')}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

if __name__ == "__main__":
    test_url()
