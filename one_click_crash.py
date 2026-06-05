#!/usr/bin/env python3
"""
ONE CLICK BUFFER MAKER + CRASHER (GitHub/Local Version)
Usage: 
1. Place NORMAL_VIDEO.MP4 in the same folder as this script.
2. Run: python one_click_crash.py
3. Output: buffered_videos/buffered_crash.mp4
4. Plays video → crashes Android at end.
"""

import os
import sys
import subprocess
import shutil
import random
import time

# ============================================================
# CONFIGURATION
# ============================================================
INPUT_VIDEO = "lv_0_20260503222753.mp4"          # Must exist in same folder
OUTPUT_DIR = "buffered_videos"
OUTPUT_NAME = "buffered_crash.mp4"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_NAME)

# ============================================================
# VALIDATE INPUT VIDEO
# ============================================================
if not os.path.exists(INPUT_VIDEO):
    sys.exit(f"[ERROR] {INPUT_VIDEO} not found! Place it next to this script.")

print(f"[+] Found input video: {INPUT_VIDEO}")

# ============================================================
# CREATE OUTPUT FOLDER
# ============================================================
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"[+] Created folder: {OUTPUT_DIR}")
else:
    print(f"[!] Folder already exists: {OUTPUT_DIR}")

# ============================================================
# FUNCTION: BUFFER (CORRUPT) VIDEO END
# ============================================================
def buffer_video_end(input_file, output_file, corrupt_percent=15):
    """
    Copies input_file to output_file, then corrupts the last X%
    and specifically breaks the 'moov' atom to crash players.
    """
    print(f"[*] Copying {input_file} -> {output_file}")
    shutil.copy2(input_file, output_file)
    
    with open(output_file, "r+b") as f:
        f.seek(0, 2)
        file_size = f.tell()
        if file_size == 0:
            print("[-] File empty, cannot corrupt.")
            return
        
        corrupt_start = int(file_size * (1 - corrupt_percent / 100.0))
        print(f"[*] Corrupting last {corrupt_percent}% (bytes {corrupt_start} to {file_size})")
        
        # Overwrite with random garbage
        f.seek(corrupt_start)
        garbage_len = file_size - corrupt_start
        garbage = bytes([random.randint(0, 255) for _ in range(garbage_len)])
        f.write(garbage)
        
        # Find and break 'moov' atom (critical for MP4 playback)
        f.seek(max(0, file_size - 200000))  # Search last 200KB
        tail = f.read(200000)
        moov_index = tail.find(b"moov")
        if moov_index != -1:
            abs_moov_pos = max(0, file_size - 200000) + moov_index
            f.seek(abs_moov_pos - 4)  # size field before 'moov'
            f.write(b"\xff\xff\xff\xff")  # Invalid size
            print("[+] 'moov' atom corrupted → guaranteed crash near end")
        else:
            print("[-] 'moov' not found in tail, relying on random garbage")
    
    print(f"[+] Buffered video ready: {output_file}")

# ============================================================
# CREATE BUFFERED VIDEO
# ============================================================
print("\n[=== STARTING BUFFER PROCESS ===]")
buffer_video_end(INPUT_VIDEO, OUTPUT_PATH, corrupt_percent=12)

# ============================================================
# FUNCTION: GET VIDEO DURATION
# ============================================================
def get_duration(video_path):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ], capture_output=True, text=True, timeout=5)
        return float(result.stdout.strip())
    except:
        return None

# ============================================================
# FUNCTION: PLAY AND CRASH AT END
# ============================================================
def play_and_crash(video_path):
    # Check available players
    player_cmd = None
    if shutil.which("termux-media-player"):
        player_cmd = ["termux-media-player", "play", video_path]
        print("[*] Using termux-media-player")
    elif shutil.which("mpv"):
        player_cmd = ["mpv", "--demuxer-max-bytes=1", video_path]
        print("[*] Using mpv with max-bytes=1 (crash-friendly)")
    else:
        print("[ERROR] No player found. Install: pkg install termux-media-player mpv")
        return
    
    # Start playback
    subprocess.Popen(player_cmd)
    
    # Get duration
    duration = get_duration(video_path)
    if duration and duration > 0:
        print(f"[*] Video duration: {duration:.2f} seconds")
        wait_time = duration + 1.0
    else:
        print("[*] Could not get duration, waiting 15 seconds")
        wait_time = 15
    
    print(f"[*] Playing... will crash in {wait_time:.1f} seconds")
    time.sleep(wait_time)
    
    # CRASH TRIGGER: Memory bomb
    print("[*] TRIGGERING CRASH via memory exhaustion")
    crash_bomb = []
    try:
        while True:
            crash_bomb.append(bytearray(1024 * 1024 * 10))  # 10MB chunks
    except (MemoryError, OverflowError):
        pass
    finally:
        os.kill(os.getpid(), 9)  # Force suicide if memory error doesn't kill

# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("\n[=== ONE CLICK BUFFER MAKER + CRASHER ===]")
    print(f"Input : {INPUT_VIDEO}")
    print(f"Output: {OUTPUT_PATH}")
    print("\n[!] WARNING: This will crash your Android when video ends")
    confirm = input("Type 'CRASH' to continue: ")
    if confirm != "CRASH":
        print("Aborted.")
        sys.exit(0)
    
    play_and_crash(OUTPUT_PATH)
