#!/usr/bin/env python3
"""
ONE CLICK BUFFER MAKER + CRASHER
Output video is generated INSIDE a specified folder.
"""

import os
import sys
import subprocess
import shutil
import random
import time
import struct

# ============================================================
# CONFIGURATION - EDIT THESE TWO LINES
# ============================================================
INPUT_VIDEO = "1v_0_20260503222753.mp4"      # Your normal video file
OUTPUT_FOLDER = "my_buffered_videos"          # Folder where crash video will go
# ============================================================

OUTPUT_NAME = "buffered_crash.mp4"
OUTPUT_PATH = os.path.join(OUTPUT_FOLDER, OUTPUT_NAME)

# ============================================================
# STEP 1: CREATE THE FOLDER (if doesn't exist)
# ============================================================
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    print(f"[+] Created folder: {OUTPUT_FOLDER}/")
else:
    print(f"[!] Folder already exists: {OUTPUT_FOLDER}/")

# ============================================================
# STEP 2: CHECK INPUT VIDEO EXISTS
# ============================================================
if not os.path.exists(INPUT_VIDEO):
    sys.exit(f"[ERROR] {INPUT_VIDEO} not found in current directory!")

print(f"[+] Input video: {INPUT_VIDEO}")
print(f"[+] Output will be: {OUTPUT_PATH}")

# ============================================================
# STEP 3: FUNCTION TO FIND moov ANYWHERE
# ============================================================
def find_moov(filepath):
    with open(filepath, "rb") as f:
        # Search first 2MB
        f.seek(0)
        data = f.read(2*1024*1024)
        pos = data.find(b"moov")
        if pos != -1:
            return pos
        
        # Search last 2MB
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - 2*1024*1024))
        data = f.read(2*1024*1024)
        pos = data.find(b"moov")
        if pos != -1:
            return max(0, size - 2*1024*1024) + pos
    return -1

# ============================================================
# STEP 4: BUFFER/CRASH VIDEO GENERATOR (SAVES TO FOLDER)
# ============================================================
def generate_buffered_video(input_file, output_file):
    print(f"\n[== STARTING BUFFER PROCESS ==]")
    print(f"[*] Copying {input_file} -> {output_file}")
    shutil.copy2(input_file, output_file)
    
    with open(output_file, "r+b") as f:
        f.seek(0, 2)
        file_size = f.tell()
        
        # Corrupt last 15% with random garbage
        corrupt_start = int(file_size * 0.85)
        print(f"[*] Corrupting bytes {corrupt_start} to {file_size} (last 15%)")
        f.seek(corrupt_start)
        garbage = bytes([random.randint(0, 255) for _ in range(file_size - corrupt_start)])
        f.write(garbage)
        
        # Find and break moov atom
        moov_pos = find_moov(output_file)
        if moov_pos != -1:
            print(f"[+] Found 'moov' at offset {moov_pos}")
            f.seek(moov_pos - 4)
            f.write(b"\xff\xff\xff\xff")
            print("[+] 'moov' atom corrupted")
        else:
            print("[!] No 'moov' found - injecting crash NALU at end")
            f.seek(0, 2)
            crash_nalu = b"\x00\x00\x00\x01\x00\x00\x00\x01" + b"\xff" * 50000
            f.write(crash_nalu)
            print("[+] Crash NALU injected")
        
        # Break file header
        f.seek(4)
        f.write(b"\x00\x00\x00\x00")
    
    print(f"[+] ✓ Buffered video GENERATED in: {output_file}")
    print(f"[+] Folder location: {OUTPUT_FOLDER}/")

# ============================================================
# STEP 5: GET VIDEO DURATION
# ============================================================
def get_duration(video_path):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ], capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            return float(result.stdout.strip())
    except:
        pass
    return 10  # fallback

# ============================================================
# STEP 6: PLAY AND CRASH
# ============================================================
def play_and_crash(video_path):
    # Find available player
    if shutil.which("mpv"):
        player = ["mpv", "--demuxer-max-bytes=1", video_path]
        player_name = "mpv"
    elif shutil.which("termux-media-player"):
        player = ["termux-media-player", "play", video_path]
        player_name = "termux-media-player"
    else:
        print("[ERROR] No player. Install: pkg install mpv")
        return
    
    print(f"\n[*] Playing with: {player_name}")
    subprocess.Popen(player)
    
    duration = get_duration(video_path)
    print(f"[*] Video duration: {duration:.1f} seconds")
    print(f"[*] Playing... will crash in {duration + 1:.1f} seconds")
    time.sleep(duration + 1)
    
    # CRASH TRIGGER
    print("[*] TRIGGERING CRASH...")
    bomb = []
    try:
        while True:
            bomb.append(bytearray(1024 * 1024 * 10))
    except:
        pass
    os.kill(os.getpid(), 9)

# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("   BUFFER MAKER + CRASHER (Folder Version)")
    print("="*50)
    
    # Generate the buffered video inside the folder
    generate_buffered_video(INPUT_VIDEO, OUTPUT_PATH)
    
    # Show where the file is
    print(f"\n[✓] Crash video is here: {OUTPUT_PATH}")
    print(f"[✓] Folder content:")
    os.system(f"ls -la {OUTPUT_FOLDER}/")
    
    # Ask for confirmation
    print("\n[!] WARNING: This will CRASH your Android at video end")
    confirm = input("Type 'CRASH' to continue: ")
    if confirm != "CRASH":
        print("Aborted. Crash video still saved in folder.")
        sys.exit(0)
    
    # Play and crash
    play_and_crash(OUTPUT_PATH)
