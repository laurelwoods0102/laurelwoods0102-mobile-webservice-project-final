import os
import cv2
import requests
import copy
from datetime import datetime
import pathlib
import shutil
import uuid
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for server/background use
import matplotlib.pyplot as plt
import numpy as np

# [IMPORTANT] Ensure reid.py is in the same directory
from reid import PersonReIDSystem

class ChangeDetection:
    def __init__(self, names):
        self.names = names
        self.result_prev = [0] * len(names) 
        
        # Server Configuration
        # self.HOST = 'http://127.0.0.1:8000' 
        self.HOST = 'https://laurelwoods0102.pythonanywhere.com' 
        self.API_ROOT = f"{self.HOST}/api_root"
        self.USERNAME = 'user1'             
        self.PASSWORD = 'qwert12345'          
        self.TOKEN = self.get_token()
        
        # Temp Dirs for Analysis
        self.TEMP_DOWNLOAD_DIR = "temp_downloads"
        self.TEMP_OUTPUT_DIR = "temp_output"

        # Optimization Lists
        self.white_list = ['cat', 'dog', 'bird']    
        self.black_list = [
            'chair', 'tv', 'handbag', 'suitcase', 'backpack', 'dining table', 'sink', 
            'microwave', 'umbrella', 'bowl', 'refrigerator', 'bottle', 'cup', 'oven', 
            'couch', 'bed', 'potted plant', 'cake', 'remote', 'mouse', 'book', 
            'laptop', 'knife', 'orange', 'apple', 'wine glass'
        ] 
        self.piggy_back_buffer = []         
        
        print(f"[*] System Initialized. Token: {self.TOKEN}")

    def get_token(self):
        try:
            res = requests.post(f"{self.HOST}/api-token-auth/", data={
                'username': self.USERNAME,
                'password': self.PASSWORD
            })
            res.raise_for_status()
            return res.json()['token']
        except Exception as e:
            print(f"[!] Authentication Failed: {e}")
            return None

    def add(self, detected_current, img, details=None):
        if details is None: details = []
        timestamp = datetime.now()
        
        for i, count in enumerate(detected_current):
            obj_name = self.names[i]
            if obj_name in self.black_list: continue

            if self.result_prev[i] == 0 and count >= 1:
                print(f"[+] Change Detected: {obj_name} appeared.")
                
                conf_str = ""
                bbox_str = ""
                desc_str = ""
                
                for d in details:
                    if d['name'] == obj_name:
                        conf_str = d['conf']
                        bbox_str = d['bbox']
                        color = d.get('color', 'Unknown')
                        size = d.get('size', 0)
                        desc_str = f"Color: {color}, Size: {size}% of screen"
                        break

                image_path = self.save_image(img, timestamp)
                
                post_data = {
                    'title': obj_name,
                    'text': f"Detected {obj_name} at {timestamp.strftime('%H:%M:%S')}.\n{desc_str}", 
                    'created_date': timestamp.isoformat(),
                    'published_date': timestamp.isoformat(),
                    'image_path': image_path,
                    'confidence': conf_str,
                    'bbox': bbox_str
                }

                if obj_name in self.white_list:
                    print(f"    -> {obj_name} Buffered.")
                    self.piggy_back_buffer.append(post_data)
                else:
                    print(f"    -> {obj_name} INTRUDER! Sending Alert.")
                    self.send(post_data) 
                    self.flush_buffer()  

        self.result_prev = copy.deepcopy(detected_current)

    def save_image(self, img, timestamp):
        save_dir = f"detected_frames/{timestamp.strftime('%Y%m%d')}"
        pathlib.Path(save_dir).mkdir(parents=True, exist_ok=True)
        filename = f"{timestamp.strftime('%H%M%S_%f')}.png"
        full_path = os.path.join(save_dir, filename)
        img_resized = cv2.resize(img, (640, 480))
        cv2.imwrite(full_path, img_resized)
        return full_path

    def flush_buffer(self):
        if not self.piggy_back_buffer: return
        print(f"    -> Flushing {len(self.piggy_back_buffer)} items...")
        for data in self.piggy_back_buffer: self.send(data)
        self.piggy_back_buffer = []

    def send(self, data):
        if not self.TOKEN: return
        headers = {'Authorization': f'Token {self.TOKEN}'}
        payload = {
            'title': data['title'],
            'text': data['text'],
            'created_date': data['created_date'],
            'published_date': data['published_date'],
            'author': 1,
            'confidence': data.get('confidence', ''),
            'bbox': data.get('bbox', '')
        }
        try:
            with open(data['image_path'], 'rb') as img_file:
                files = {'image': img_file}
                res = requests.post(f"{self.HOST}/api_root/Post/", data=payload, files=files, headers=headers)
            if res.status_code == 201: print(f"    [Success] Uploaded {data['title']}")
            else: print(f"    [Failed] {res.status_code}")
        except Exception as e: print(f"    [Error] {e}")

    # =========================================================
    #  ANALYSIS MODULE (Integrated)
    # =========================================================

    def _download_image_temp(self, url):
        """Helper to download image for analysis."""
        try:
            # Fix localhost alias for container/emulator environments
            if "10.0.2.2" in url: url = url.replace("10.0.2.2", "127.0.0.1")
            
            filename = url.split('/')[-1]
            save_path = os.path.join(self.TEMP_DOWNLOAD_DIR, filename)
            
            response = requests.get(url, stream=True, timeout=5)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                return save_path
        except Exception as e:
            print(f"    [Analysis] Download Error: {e}")
        return None

    def _upload_plot(self, file_path):
        """Helper to upload generated chart."""
        url = f"{self.API_ROOT}/upload_plot/"
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                res = requests.post(url, files=files)
                if res.status_code == 201: return res.json()['url']
        except Exception as e:
            print(f"    [Analysis] Upload Error: {e}")
        return None

    def analysis(self):
        print("\n[*] Starting Analysis Module...")
        
        # 1. Setup & 2. Fetch Data (Keep existing code)
        if os.path.exists(self.TEMP_DOWNLOAD_DIR): shutil.rmtree(self.TEMP_DOWNLOAD_DIR)
        if os.path.exists(self.TEMP_OUTPUT_DIR): shutil.rmtree(self.TEMP_OUTPUT_DIR)
        os.makedirs(self.TEMP_DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(self.TEMP_OUTPUT_DIR, exist_ok=True)

        headers = {'Authorization': f'Token {self.TOKEN}'}
        try:
            res = requests.get(f"{self.API_ROOT}/Post/", headers=headers)
            if res.status_code != 200: return
            posts = res.json()
        except: return

        if not posts: return

        # 3. Process Data (Stats & Prep)
        object_counts = {}
        hour_counts = {h: 0 for h in range(24)}
        person_entries = []

        for p in posts:
            title = p.get('title', 'unknown')
            object_counts[title] = object_counts.get(title, 0) + 1
            
            # Time processing...
            date_str = p.get('created_date', '')
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    hour_counts[dt.hour] += 1
                except: pass

            # Re-ID Prep
            if title == 'person' and PersonReIDSystem:
                img_url = p.get('image', '')
                local_path = self._download_image_temp(img_url)
                if local_path:
                    bbox_str = p.get('bbox', '0,0,0,0')
                    try:
                        bbox = [int(float(x)) for x in bbox_str.split(',')]
                        person_entries.append({'path': local_path, 'bbox': bbox})
                    except: pass

        # 4. Generate General Charts (Pie/Bar)
        general_plot_urls = [] # [CHANGED] Store generic plots separately

        # Pie Chart
        fig1, ax1 = plt.subplots()
        ax1.pie(object_counts.values(), labels=object_counts.keys(), autopct='%1.1f%%')
        ax1.set_title("Object Distribution")
        p1 = os.path.join(self.TEMP_OUTPUT_DIR, "dist.png")
        fig1.savefig(p1)
        plt.close(fig1)
        general_plot_urls.append(self._upload_plot(p1))

        # Bar Chart
        fig2, ax2 = plt.subplots()
        ax2.bar(hour_counts.keys(), hour_counts.values())
        ax2.set_title("Hourly Activity")
        p2 = os.path.join(self.TEMP_OUTPUT_DIR, "time.png")
        fig2.savefig(p2)
        plt.close(fig2)
        general_plot_urls.append(self._upload_plot(p2))

        # 5. Run Re-ID (Structured Grouping)
        people_data_list = [] # [NEW] Structured Data

        if person_entries and PersonReIDSystem:
            print(f"    -> Running Person Re-ID on {len(person_entries)} images...")
            try:
                reid = PersonReIDSystem()
                groups = reid.group_people(person_entries)
                
                for i, group in enumerate(groups):
                    num = len(group)
                    
                    # Generate Collage
                    cols = min(5, num)
                    rows = (num // cols) + 1
                    fig, axs = plt.subplots(rows, cols, figsize=(cols*2, rows*2.5))
                    fig.suptitle(f"Person #{i+1} (Detections: {num})")
                    
                    if num == 1: axs = np.array([axs])
                    axs = axs.flatten()
                    for idx, ax in enumerate(axs):
                        if idx < num: ax.imshow(group[idx]); ax.axis('off')
                        else: ax.axis('off')
                    
                    fname = f"group_{i}.png"
                    pg = os.path.join(self.TEMP_OUTPUT_DIR, fname)
                    fig.savefig(pg)
                    plt.close(fig)
                    
                    u_url = self._upload_plot(pg)
                    
                    # [NEW] Add to Structured List
                    if u_url:
                        people_data_list.append({
                            "id": i + 1,
                            "count": num,
                            "url": u_url
                        })

            except Exception as e:
                print(f"    [!] Re-ID Error: {e}")

        # 6. Submit Report
        print("    -> Uploading Final Report...")
        general_plot_urls = [u for u in general_plot_urls if u]
        
        summary = (f"Analysis Report\n"
                   f"Total Events: {len(posts)}\n"
                   f"Top Object: {max(object_counts, key=object_counts.get) if object_counts else 'None'}")

        # [NEW] Payload structure
        payload = {
            "summary": summary,
            "plot_urls": general_plot_urls,  # Only Pie/Bar
            "people_data": people_data_list  # Structured People Groups
        }
        
        try:
            res = requests.post(f"{self.API_ROOT}/analysis/", json=payload)
            if res.status_code == 200: print("[*] Analysis Complete & Sent.")
            else: print(f"[!] Report Upload Failed: {res.status_code}")
        except Exception as e:
            print(f"[!] Report Connection Error: {e}")

        shutil.rmtree(self.TEMP_DOWNLOAD_DIR, ignore_errors=True)
        shutil.rmtree(self.TEMP_OUTPUT_DIR, ignore_errors=True)