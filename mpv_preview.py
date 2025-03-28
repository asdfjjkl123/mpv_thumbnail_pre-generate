#!/usr/bin/env python3
import sys
import os
import subprocess
import re
import concurrent.futures

def get_video_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        duration = float(result.stdout.strip())
    except Exception as e:
        print("Cannot get video duration:", e)
        duration = None
    return duration

def get_video_dimensions(video_path):
    # Get the dimensions (width x height) of the first video stream, e.g. "1920x1080"
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0", video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    dims = result.stdout.strip()  # e.g. "1920x1080"
    if dims:
        parts = dims.split('x')
        if len(parts) == 2:
            try:
                width = int(parts[0])
                height = int(parts[1])
                return width, height
            except Exception as e:
                print("Failed to parse video dimensions:", e)
    return None, None

def format_time_ffmpeg(seconds):
    # Format seconds into HH:MM:SS.xxx for ffmpeg
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def generate_thumbnails_direct_bgra(video_path, output_dir, thumbnail_count, max_width, max_height):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    duration = get_video_duration(video_path)
    if not duration:
        print("Failed to get video duration")
        return False
    orig_w, orig_h = get_video_dimensions(video_path)
    if not orig_w or not orig_h:
        print("Failed to get video dimensions")
        return False
    # Calculate scale factor so that neither width nor height exceeds max dimensions while preserving aspect ratio
    scale_factor = min(max_width / orig_w, max_height / orig_h, 1)
    new_w = int(orig_w * scale_factor)
    new_h = int(orig_h * scale_factor)
    print(f"Original dimensions: {orig_w}x{orig_h}, Thumbnail dimensions: {new_w}x{new_h}")
    interval = duration / thumbnail_count

    def generate_single_thumbnail(i):
        thumbnail_time = i * interval
        time_str = format_time_ffmpeg(thumbnail_time)
        # Output filename from 000000.bgra onward
        output_filename = os.path.join(output_dir, f"{i:06d}.bgra")
        cmd = [
            "ffmpeg",
            "-ss", time_str,
            "-i", video_path,
            "-vframes", "1",
            "-vf", f"scale={new_w}:{new_h}",
            "-f", "rawvideo",
            "-pix_fmt", "bgra",
            output_filename
        ]
        print("Running command:", " ".join(cmd))
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Failed to generate thumbnail {i:06d} (time {time_str}):", result.stderr.decode())
        return result.returncode

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(generate_single_thumbnail, i) for i in range(thumbnail_count)]
        for _ in concurrent.futures.as_completed(futures):
            pass
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python mpv_preview.py <video_path> <thumbnails_directory>")
        sys.exit(1)
    video_path = sys.argv[1].strip('"')
    cache_directory = sys.argv[2].strip('"')
    
    # Create folder name using video filename (without extension) and file size
    base_filename = os.path.splitext(os.path.basename(video_path))[0]
    base_filename = re.sub(r"[^a-zA-Z0-9_.\-' ]", "", base_filename)
    try:
        filesize = os.path.getsize(video_path)
    except Exception as e:
        filesize = 0
    file_key = f"{base_filename}-{filesize}"
    thumbnail_dir = os.path.join(cache_directory, file_key)
    
    # Make sure the setting is same as mpv_thumbnail_script.conf
    thumbnail_count = 150
    max_width = 200
    max_height = 200

    print("Generating BGRA thumbnails directly...")
    if not generate_thumbnails_direct_bgra(video_path, thumbnail_dir, thumbnail_count, max_width, max_height):
        print("Failed to generate thumbnails")
        sys.exit(1)
    print(f"Thumbnails generated successfully in: {thumbnail_dir}")

if __name__ == "__main__":
    main()
