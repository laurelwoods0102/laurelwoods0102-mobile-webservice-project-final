import requests
import os
import shutil
import matplotlib.pyplot as plt
import uuid
import numpy as np
from datetime import datetime
from reid import PersonReIDSystem

# --- CONFIGURATION ---
# [CRITICAL] If running in a separate container, 127.0.0.1 WILL FAIL.
# Use your computer's actual LAN IP (e.g., 192.168.1.X) or Docker service name.
# SERVER_BASE = "http://127.0.0.1:8000" 
SERVER_BASE = "https://laurelwoods0102.pythonanywhere.com" 
API_ROOT = f"{SERVER_BASE}/api_root"
AUTH_TOKEN = "bf46b8f9337d1d27b4ef2511514c798be1a954b8" 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DOWNLOAD_DIR = os.path.join(BASE_DIR, "temp_downloads")
TEMP_OUTPUT_DIR = os.path.join(BASE_DIR, "temp_output")

def download_image(url, save_dir):
    try:
        # If the server URL in DB is 10.0.2.2 (Emulator), map it to SERVER_BASE
        if "10.0.2.2:8000" in url:
            url = url.replace("http://10.0.2.2:8000", SERVER_BASE)
        elif "127.0.0.1:8000" in url:
            url = url.replace("http://127.0.0.1:8000", SERVER_BASE)
            
        filename = url.split('/')[-1]
        save_path = os.path.join(save_dir, filename)
        
        response = requests.get(url, stream=True, timeout=1000)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            return save_path
        else:
            print(f"[Analysis] Download failed (Status {response.status_code}): {url}")
    except Exception as e:
        print(f"[Analysis] Download Error: {e}")
    return None

def upload_plot(file_path):
    url = f"{API_ROOT}/upload_plot/"
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            # Uploading requires no token per your views.py (AllowAny)
            res = requests.post(url, files=files)
            if res.status_code == 201:
                return res.json()['url']
            else:
                print(f"[Analysis] Upload failed: {res.text}")
    except Exception as e:
        print(f"[Analysis] Upload Error: {e}")
    return None

def run_analysis():
    print("[Analysis] Starting...")
    
    # 1. Cleanup & Setup
    if os.path.exists(TEMP_DOWNLOAD_DIR): shutil.rmtree(TEMP_DOWNLOAD_DIR)
    if os.path.exists(TEMP_OUTPUT_DIR): shutil.rmtree(TEMP_OUTPUT_DIR)
    os.makedirs(TEMP_DOWNLOAD_DIR)
    os.makedirs(TEMP_OUTPUT_DIR)

    # 2. Fetch Data
    headers = {"Authorization": f"Token {AUTH_TOKEN}"}
    try:
        resp = requests.get(f"{API_ROOT}/Post/", headers=headers, timeout=5)
        if resp.status_code != 200: 
            print("[Analysis] Failed to fetch posts.")
            return
        posts = resp.json()
    except Exception as e:
        print(f"[Analysis] Connection Error: {e}")
        return

    if not posts: return

    # 3. Analyze Data
    object_counts = {}
    hour_counts = {h: 0 for h in range(24)}
    person_entries = []

    print(f"[Analysis] Processing {len(posts)} posts...")
    for p in posts:
        # Stats
        title = p.get('title', 'unknown')
        object_counts[title] = object_counts.get(title, 0) + 1
        
        # Time
        date_str = p.get('created_date', '')
        if date_str:
            try:
                # Handle ISO string safely
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                hour_counts[dt.hour] += 1
            except: pass

        # Re-ID Prep: Only download 'person' images
        if title == 'person':
            img_url = p.get('image', '')
            local_path = download_image(img_url, TEMP_DOWNLOAD_DIR)
            
            bbox_str = p.get('bbox', '0,0,0,0')
            try:
                bbox = [int(float(x)) for x in bbox_str.split(',')]
            except: 
                bbox = [0,0,0,0]

            if local_path:
                person_entries.append({'path': local_path, 'bbox': bbox})

    # 4. Generate & Upload Plots
    final_plot_urls = []

    # -- Pie Chart --
    fig1, ax1 = plt.subplots()
    ax1.pie(object_counts.values(), labels=object_counts.keys(), autopct='%1.1f%%')
    ax1.set_title("Object Distribution")
    p1 = os.path.join(TEMP_OUTPUT_DIR, "dist.png")
    fig1.savefig(p1)
    plt.close(fig1)
    final_plot_urls.append(upload_plot(p1))

    # -- Bar Chart --
    fig2, ax2 = plt.subplots()
    ax2.bar(hour_counts.keys(), hour_counts.values())
    ax2.set_title("Hourly Activity")
    p2 = os.path.join(TEMP_OUTPUT_DIR, "time.png")
    fig2.savefig(p2)
    plt.close(fig2)
    final_plot_urls.append(upload_plot(p2))

    # -- Person Re-ID --
    if person_entries:
        print(f"[Analysis] Running Re-ID on {len(person_entries)} people...")
        try:
            reid = PersonReIDSystem()
            groups = reid.group_people(person_entries)
            
            for i, group in enumerate(groups):
                num = len(group)
                # Create Collage
                cols = min(5, num)
                rows = (num // cols) + 1
                fig, axs = plt.subplots(rows, cols, figsize=(cols*2, rows*2.5))
                fig.suptitle(f"Person #{i+1} (Detections: {num})")
                
                if num == 1: axs = np.array([axs])
                axs = axs.flatten()
                
                for idx, ax in enumerate(axs):
                    if idx < num:
                        ax.imshow(group[idx])
                        ax.axis('off')
                    else:
                        ax.axis('off')
                
                fname = f"person_group_{i}.png"
                path_g = os.path.join(TEMP_OUTPUT_DIR, fname)
                fig.savefig(path_g)
                plt.close(fig)
                
                # Upload and append to list
                u_url = upload_plot(path_g)
                if u_url: final_plot_urls.append(u_url)
                
        except Exception as e:
            print(f"[Analysis] Re-ID Failed: {e}")

    # 5. Submit Final Report
    final_plot_urls = [u for u in final_plot_urls if u] # Remove None
    
    summary = (f"Analysis Report\n"
               f"Total Events: {len(posts)}\n"
               f"Unique People: {len(groups) if person_entries else 0}\n"
               f"Most Common: {max(object_counts, key=object_counts.get) if object_counts else 'None'}")
    
    payload = {
        "summary": summary,
        "plot_urls": final_plot_urls
    }
    
    try:
        res = requests.post(f"{API_ROOT}/analysis/", json=payload)
        if res.status_code == 200:
            print("[Analysis] SUCCESS: Report uploaded.")
        else:
            print(f"[Analysis] FAILED to save report: {res.text}")
    except Exception as e:
        print(f"[Analysis] Final POST Error: {e}")

if __name__ == "__main__":
    run_analysis()