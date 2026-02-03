import os
import requests
import time

# NCERT Math Config for 2025-26 Session
NCERT_MATH_CONFIG = {
    "Class_01": [("aejm1", 1, 13)],
    "Class_02": [("bejm1", 1, 11)],
    "Class_03": [("cemm1", 1, 14)],
    "Class_04": [("demh1", 1, 13)],
    "Class_05": [("eemh1", 1, 12)],
    "Class_06": [("fegp1", 1, 10)],
    "Class_07": [("gegp1", 1, 8), ("gegp2", 1, 7)], # gegp201 is Ch 9, gegp207 is Ch 15
    "Class_08": [("hegp1", 1, 6), ("hegp2", 1, 7)], # hegp201 is Ch 7, hegp207 is Ch 13
    "Class_09": [("iemh1", 1, 12)],
    "Class_10": [("jemh1", 1, 14)],
    "Class_11": [("kemh1", 1, 14)],
    "Class_12": [("lemh1", 1, 6), ("lemh2", 1, 7)]  # lemh201 is Ch 7, lemh207 is Ch 13
}

# NCERT Science Config for 2025-26 Session
NCERT_SCIENCE_CONFIG = {
    # Class 6: New "Curiosity" Series
    "Class_06": [("fecu1", 1, 12)], 
    "Class_06": [("fecu1", 1, 12)], 


    # Class 7: New "Curiosity" Series
    "Class_07": [("gecu1", 1, 12)], 

    # Class 8: New "Curiosity" Series
    "Class_08": [("hecu1", 1, 13)],

    # Class 9: Rationalised "Science" (Ch 13-15 Removed)
    "Class_09": [("iesc1", 1, 12)], 

    # Class 10: Rationalised "Science" (Ch 14-16 Removed)
    "Class_10": [("jesc1", 1, 13)] 
}

# PRELIM_FILES = ["ps", "qr"]
PRELIM_FILES = ["ps"]
BASE_URL = "https://ncert.nic.in/textbook/pdf/"

def fetch_and_save(file_name, folder):
    save_path = os.path.join(folder, file_name)
    
    # NEW CHECK: Skip only if file exists AND is not empty (0 bytes)
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        # print(f"  ⏭️ Already exists: {file_name}")
        return

    url = f"{BASE_URL}{file_name}"
    try:
        # Added a small delay to avoid "Connection Reset"
        time.sleep(1.0) 
        
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"  ✅ Saved: {file_name}")
        else:
            print(f"  ❌ Not Found: {file_name} (Status {response.status_code})")
    except Exception as e:
        print(f"  ⚠️ Error on {file_name}: {e}")

def download_math():
    print("📐 Starting NCERT Math Sync (2026 Edition)...")
    for class_name, books in NCERT_MATH_CONFIG.items():
        folder = os.path.join("NCERT_Math", class_name)
        os.makedirs(folder, exist_ok=True)
        
        for code, start, end in books:
            # 1. Get the Index/Prelims
            fetch_and_save(f"{code}ps.pdf", folder)
            
            # 2. Get Chapters
            for ch in range(start, end + 1):
                file_name = f"{code}{str(ch).zfill(2)}.pdf"
                fetch_and_save(file_name, folder)

def download_science():
    print("🔬 Starting NCERT Science Sync (2026 Edition)...")
    for class_name, books in NCERT_SCIENCE_CONFIG.items():
        folder = os.path.join("NCERT_Science", class_name)
        os.makedirs(folder, exist_ok=True)
        
        for code, start, end in books:
            # 1. Get the Index/Prelims
            fetch_and_save(f"{code}ps.pdf", folder)
            
            # 2. Get Chapters
            for ch in range(start, end + 1):
                file_name = f"{code}{str(ch).zfill(2)}.pdf"
                fetch_and_save(file_name, folder)

if __name__ == "__main__":
    # Download both Math and Science books
    download_math()
    download_science()