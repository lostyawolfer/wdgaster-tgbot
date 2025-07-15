# please revise sometime soon bc this entire file was written by
# ai and then copy-pasted

import os
import yt_dlp
import asyncio
import re

TEMP_DOWNLOAD_DIR = "temp_downloads"
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)

def get_youtube_video_id(url: str) -> str | None:
    pattern = (
        r'(?:https?://)?(?:www\.)?'
        r'(?:m\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com)/'
        r'(?:watch\?v=|embed/|v/|e/|.+\?v=|playlist\?list=|live/|shorts/|y/|)'
        r'([^"&?\/\s]{11})'
    )
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

async def download_youtube_video(video_url: str) -> dict | None:
    video_id = get_youtube_video_id(video_url)
    if not video_id:
        print(f"Invalid YouTube URL: {video_url}")
        return None

    output_template = os.path.join(TEMP_DOWNLOAD_DIR, '%(id)s.%(ext)s')

    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720][filesize<20M]+bestaudio[ext=m4a]/best[ext=mp4][height<=720][filesize<20M]/best[filesize<20M]',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'ignore_errors': True,
        'writesinglejson': True, # Ensure this is True to get full info_dict
        'force_single_and_subtitle_files': True,
        'writethumbnail': True,  # <--- ADDED: Tells yt-dlp to download the best available thumbnail
        'embed_thumbnail': False,  # <--- OPTIONAL: Don't embed in video, we want a separate file
    }

    filepath = None
    thumbnail_filepath = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # We call extract_info twice: once to get info without download, then to download.
            # This is safer if you want to inspect info_dict before committing to download.
            # Or you can do it in one go if download=True is enough.
            # For simplicity, let's stick to the one-call for now but return description.
            info_dict = ydl.extract_info(video_url, download=True)

            filepath = ydl.prepare_filename(info_dict)

            if info_dict and 'id' in info_dict:
                # Common thumbnail formats yt-dlp saves are .webp or .jpg
                potential_thumbnail_filepath_webp = os.path.join(TEMP_DOWNLOAD_DIR, f"{info_dict['id']}.webp")
                potential_thumbnail_filepath_jpg = os.path.join(TEMP_DOWNLOAD_DIR, f"{info_dict['id']}.jpg")

                if os.path.exists(potential_thumbnail_filepath_webp):
                    thumbnail_filepath = potential_thumbnail_filepath_webp
                elif os.path.exists(potential_thumbnail_filepath_jpg):
                    thumbnail_filepath = potential_thumbnail_filepath_jpg
                else:
                    # Fallback if specific file isn't found, try to get from info_dict if exists
                    best_thumbnail_url = None
                    if 'thumbnails' in info_dict and info_dict['thumbnails']:
                        # Find the best quality thumbnail URL if not downloaded locally
                        # This would require *another* download or using URLInputFile (more complex)
                        # For simplicity, relying on 'writethumbnail' and local file.
                        pass

            if info_dict and 'title' in info_dict and filepath and os.path.exists(filepath):
                return {
                    "filepath": filepath,
                    "title": info_dict.get('title', 'НЕИЗВЕСТНОЕ НАЗВАНИЕ'),
                    "duration": info_dict.get('duration', 0),
                    "description": info_dict.get('description', '')
                }
            else:
                print(f"yt-dlp failed to download or get info for {video_url}")
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
                return None

    except yt_dlp.DownloadError as e:
        print(f"Download Error for {video_url}: {e}")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during YouTube download for {video_url}: {e}")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return None

async def delete_temp_file(filepath: str):
    await asyncio.sleep(20)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted temporary file: {filepath}")
    except Exception as e:
        print(f"Error deleting temporary file {filepath}: {e}")
        pass