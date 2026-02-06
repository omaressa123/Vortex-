import requests
import json
import os

BASE_URL = "http://localhost:8000"

def test_workflow():
    # 1. Upload File
    print("Testing /upload...")
    files = {'file': open('test_data.csv', 'rb')}
    response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return
    
    upload_data = response.json()
    file_id = upload_data.get('file_id')
    print(f"Upload success! File ID: {file_id}")
    
    # 2. Generate Dashboard (using Heuristic fallback as we don't have API key set in this script, or we rely on app to handle it)
    print("\nTesting /generate-dashboard...")
    payload = {
        "file_id": file_id,
        "template_image": "1.jpeg",
        "api_key": "" # Empty key to trigger fallback
    }
    
    response = requests.post(f"{BASE_URL}/generate-dashboard", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("Generate Dashboard Success!")
        print(json.dumps(result, indent=2))
    else:
        print(f"Generate Dashboard failed: {response.text}")

if __name__ == "__main__":
    test_workflow()
