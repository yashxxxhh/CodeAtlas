import requests

BASE_URL = "http://localhost:8000"

def test_health():
    """Test GET /health"""
    url = f"{BASE_URL}/health"
    resp = requests.get(url)
    print("GET /health →", resp.status_code, resp.json())

def test_search():
    """Test GET /search"""
    url = f"{BASE_URL}/search"
    params = {"query": "authentication middleware"}
    resp = requests.get(url, params=params)
    print("GET /search →", resp.status_code, resp.json())

def test_upload():
    """Test POST /repositories/upload"""
    url = f"{BASE_URL}/repositories/upload"
    # Replace with a real zip file path
    file_path = "sample_repo.zip"
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f)}
            resp = requests.post(url, files=files)
            print("POST /repositories/upload →", resp.status_code, resp.json())
    except FileNotFoundError:
        print(f"File {file_path} not found. Place a ZIP file to test upload.")

if __name__ == "__main__":
    test_health()
    test_search()
    test_upload()