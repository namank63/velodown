import requests
import sys

# Test cases: (URL, Expected Title Fragment)
TEST_CASES = [
    ("https://youtu.be/RTZW6Mh48eM?si=OI0DcsodDwBexPpV", "Samay Raina"),
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "Rick Astley"), # Standard YouTube
    ("https://vimeo.com/22439234", "The Mountain"), # Vimeo
    ("https://www.instagram.com/reel/DXrA2idCgrT/?igsh=ZXplaG02ZGxlbHZn", "ws_propertiespk"), # Instagram Reel
]

BASE_URL = "http://localhost:8000"

def run_tests():
    print(f"🚀 Starting URL Regression Tests against {BASE_URL}")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for url, expected in TEST_CASES:
        print(f"Testing: {url}")
        try:
            response = requests.post(f"{BASE_URL}/api/info", json={"url": url}, timeout=30)
            if response.status_code == 200:
                title = response.json().get("title", "")
                if expected.lower() in title.lower():
                    print(f"✅ PASS: Found '{expected}' in '{title}'")
                    passed += 1
                else:
                    print(f"❌ FAIL: Title mismatch. Expected '{expected}', got '{title}'")
                    failed += 1
            else:
                print(f"❌ FAIL: API returned {response.status_code}. Detail: {response.text}")
                failed += 1
        except Exception as e:
            print(f"💥 ERROR: {str(e)}")
            failed += 1
        print("-" * 50)

    print(f"\n📊 SUMMARY: {passed} Passed, {failed} Failed")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
