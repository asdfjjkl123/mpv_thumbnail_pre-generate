# mpv_thumbnail_pre-generate
A python script to generating thumbnail for mpv without open mpv

The generated thumbnails are use for mpv_thumbnail_script
https://github.com/TheAMM/mpv_thumbnail_script

The original script start generating thumbnails when video is loaded in mpv. Using the pre-generate python script can generate the thumbnails without opening the video.

Moreover, the original lua script generate thumbnails in a minute and the python script generate in sceonds (cpu work load 100%).

# Using py script

```ini
python mpv_preview.py <video_path> <thumbnails_directory>
```
The default <thumbnails_directory> in mpv_thumbnail_script.conf is `%TEMP%\mpv_thumbs_cache` for windows.

The script need ffmpeg, ffprobe in the path.

Make sure the py script thumbnail setting (line 113-115) is same as mpv_thumbnail_script.conf


For example using batch:

```ini
@echo off
:path
set PATH=%PATH%;your\ffmpeg_and_ffprobe\location

:start
if "%~1"=="" goto :end

python mpv_preview.py "%~dpnx1" "%TEMP%\mpv_thumbs_cache"

shift /1
goto :start

:end
@echo.
echo finish
pause
```
