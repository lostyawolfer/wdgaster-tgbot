import asyncio
import random
import re
import aiohttp
from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.methods import SetMessageReaction
from aiogram.types import Message, ReactionTypeEmoji, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.media_group import MediaGroupBuilder
import os
import logging
import subprocess
from data.cache import AUDIO_URL_CACHE

TEMP_DOWNLOAD_DIR = "temp_downloads"
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)

COBALT_API_HOSTS = [
    "co.eepy.today",
    "co.otomir23.me",
    "cobalt.255x.ru",
    "cobalt-api.meowing.de"
]

def get_cobalt_link(text: str) -> str | None:
    pattern = (
        r'https?://(?:www\.)?(?:'
        r'bilibili\.com|bsky\.app|dailymotion\.com|facebook\.com|fb\.watch|'
        r'instagram\.com|loom\.com|ok\.ru|pinterest\.com|newgrounds\.com|'
        r'reddit\.com|redd\.it|rutube\.ru|snapchat\.com|soundcloud\.com|'
        r'streamable\.com|tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com|'
        r'tumblr\.com|twitch\.tv|twitter\.com|x\.com|vimeo\.com|vk\.com|'
        r'xiaohongshu\.com'
        r')/[^\s]+'
    )
    match = re.search(pattern, text)
    return match.group(0) if match else None

async def get_tiktok_oembed_info(video_url: str) -> dict | None:
    api_url = f"https://www.tiktok.com/oembed?url={video_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "title": data.get("title"),
                        "artist": data.get("author_name"),
                        "author_url": data.get("author_url")
                    }
                else:
                    logging.error(f"Error from TikTok oembed API: {response.status} for URL {api_url}")
                    return None
    except Exception as e:
        logging.error(f"An unexpected error occurred with TikTok oembed API: {e}")
        return None

async def get_cobalt_audio_metadata(session: aiohttp.ClientSession, url: str, host: str) -> dict | None:
    payload = {"url": url, "tiktokFullAudio": True, "localProcessing": "forced"}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    api_url = f"https://{host}/"
    logging.info(f"Requesting audio metadata from {api_url} with payload: {payload}")

    try:
        async with session.post(api_url, json=payload, headers=headers, timeout=20) as response:
            if response.status != 200:
                logging.error(f"Cobalt POST for metadata failed. Status: {response.status}, Body: {await response.text()}")
                return None
            
            data = await response.json()
            logging.info(f"Cobalt POST response for metadata: {data}")
            
            if data.get("status") == "local-processing" and "output" in data and "metadata" in data["output"]:
                metadata = data["output"]["metadata"]
                return {
                    "title": metadata.get("title"),
                    "artist": metadata.get("artist")
                }
            return None
    except Exception as e:
        logging.exception(f"An error occurred during Cobalt metadata request for URL {url}")
        return None

async def download_with_cobalt(session: aiohttp.ClientSession, url: str, host: str) -> dict | None:
    payload = {"url": url, "videoQuality": "720"}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    api_url = f"https://{host}/"
    logging.info(f"Requesting video from {api_url} for URL: {url}")

    try:
        async with session.post(api_url, json=payload, headers=headers, timeout=45) as response:
            if response.status != 200:
                logging.error(f"Video request to Cobalt failed: {response.status} - {await response.text()}")
                return None
            
            data = await response.json()
            if data.get("status") in ["stream", "tunnel"]:
                download_url = data.get("url")
                filename = data.get("filename", "video.mp4")
                filepath = os.path.join(TEMP_DOWNLOAD_DIR, f"{random.randint(1000, 9999)}_{filename}")

                async with session.get(download_url, timeout=60) as file_response:
                    if file_response.status == 200:
                        content = await file_response.read()
                        if not content:
                            logging.error(f"Downloaded video file from {download_url} is empty.")
                            return None
                        with open(filepath, "wb") as f:
                            f.write(content)
                        return {"filepath": filepath, "filename": filename}
            else:
                logging.error(f"Host {host} returned unexpected status for video: {data}")
                return None
    except Exception as e:
        logging.exception(f"An unexpected error occurred during video download for URL {url}")
        return None

async def delete_temp_file(filepath: str, delay: int = 30):
    await asyncio.sleep(delay)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"Deleted temporary file: {filepath}")
    except Exception as e:
        logging.error(f"Error deleting temporary file {filepath}: {e}")

async def _embed_metadata_ffmpeg(audio_path: str, metadata: dict, cover_path: str | None) -> str:
    """
    Встраивает метаданные и обложку в аудиофайл с помощью FFmpeg.
    Возвращает путь к новому файлу или путь к оригинальному файлу в случае ошибки.
    """
    output_path = f"{os.path.splitext(audio_path)[0]}_with_meta.mp3"
    
    try:
        command = ['ffmpeg', '-y', '-i', audio_path]

        if cover_path and os.path.exists(cover_path):
             command.extend(['-i', cover_path, '-map', '0:a', '-map', '1:v', '-c:v', 'mjpeg'])
        else:
             command.extend(['-map', '0:a'])

        command.extend(['-c:a', 'copy', '-id3v2_version', '3'])

        metadata_map = {
            "title": "title", "artist": "artist", "album_artist": "album_artist",
            "album": "album", "composer": "composer", "genre": "genre",
            "date": "date", "copyright": "copyright", "track": "track"
        }
        for key, ffmpeg_key in metadata_map.items():
            if metadata.get(key):
                command.extend(['-metadata', f'{ffmpeg_key}={metadata[key]}'])
        
        if cover_path:
            command.extend(['-metadata:s:v', 'title=Album cover', '-metadata:s:v', 'comment=Cover (front)'])

        command.append(output_path)
        
        logging.info(f"Running FFmpeg command: {' '.join(command)}")
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logging.error(f"FFmpeg failed while embedding metadata. Stderr: {stderr.decode(errors='ignore')}")
            return audio_path 
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        return audio_path

    except Exception:
        logging.exception("An exception occurred during FFmpeg metadata embedding.")
        return audio_path

async def do_cobalt_download(msg: Message, bot: Bot, is_youtube_fallback: bool = False):
    url = get_cobalt_link(msg.text or "")
    if is_youtube_fallback and not url:
        url_match = re.search(r'https?://[^\s]+', msg.text or "")
        if url_match:
            url = url_match.group(0)

    if not url: return

    original_url = url
    if 'tiktok.com/' in url:
        try:
            async with aiohttp.ClientSession() as temp_session:
                async with temp_session.head(url, allow_redirects=True, timeout=10) as response:
                    url = str(response.url).split('?')[0]
        except Exception as e:
            logging.warning(f"Failed to resolve/clean TikTok URL: {e}.")
    
    is_tiktok_video = not is_youtube_fallback and 'tiktok.com' in url
    is_soundcloud_audio = 'soundcloud.com' in url
    
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0...'}) as session:
        chosen_host = random.choice(COBALT_API_HOSTS)

        if is_soundcloud_audio:
            try:
                await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.UPLOAD_DOCUMENT)
                
                payload = {"url": url, "localProcessing": "forced", "audioFormat": "mp3"}
                headers = {"Accept": "application/json", "Content-Type": "application/json"}
                api_url = f"https://{chosen_host}/"
                
                async with session.post(api_url, json=payload, headers=headers, timeout=45) as response:
                    if response.status != 200:
                        await msg.reply(f"❌ Ошибка от Cobalt: {response.status}")
                        return
                    data = await response.json()
                    logging.info(f"COBALT API RESPONSE: {data}")


                if data.get("status") != "local-processing":
                    await msg.reply(f"❌ Cobalt вернул непредвиденный статус: {data.get('status')}")
                    return

                audio_url = data["tunnel"][0]
                metadata = data.get("output", {}).get("metadata", {})
                filename = data.get("output", {}).get("filename", "audio.mp3")
                filepath = os.path.join(TEMP_DOWNLOAD_DIR, f"{random.randint(1000, 9999)}_{filename}")
                
                async with session.get(audio_url, timeout=120) as file_response:
                    with open(filepath, "wb") as f:
                        f.write(await file_response.read())

                cover_path = None
                if data.get("audio", {}).get("cover") and len(data["tunnel"]) > 1:
                    cover_url = data["tunnel"][1]
                    cover_path = f"{os.path.splitext(filepath)[0]}.jpg"
                    async with session.get(cover_url, timeout=30) as cover_response:
                        with open(cover_path, "wb") as f:
                            f.write(await cover_response.read())
                
                final_audio_path = await _embed_metadata_ffmpeg(filepath, metadata, cover_path)

                audio_file = FSInputFile(final_audio_path, filename=filename)
                await msg.reply_audio(
                    audio=audio_file,
                    title=metadata.get("title"),
                    performer=metadata.get("artist")
                )
                
                await delete_temp_file(filepath, delay=5)
                if cover_path: await delete_temp_file(cover_path, delay=5)
                if final_audio_path != filepath: await delete_temp_file(final_audio_path, delay=5)

            except Exception as e:
                logging.exception("Ошибка при обработке ссылки SoundCloud.")
                await msg.reply(f"❌ ВНУТРЕННЯЯ ОШИБКА: {e}")
            return

        metadata_oembed = await get_tiktok_oembed_info(url) if is_tiktok_video else None
        
        try:
            await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.UPLOAD_DOCUMENT)
        except Exception: pass

        download_info = await download_with_cobalt(session, url, chosen_host)

        if download_info and download_info.get('filepath'):
            video_file = FSInputFile(download_info['filepath'], filename=download_info['filename'])
            
            author_name = metadata_oembed.get("artist") if metadata_oembed else "АВТОР"
            author_url = metadata_oembed.get("author_url") if metadata_oembed else "#"
            description = metadata_oembed.get("title") if metadata_oembed else ""
            
            caption = f'<a href="{author_url}">{author_name.upper()}</a>'
            if description:
                caption += f'\n\n<blockquote expandable>{description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</blockquote>'
            
            try:
                sent_message = await msg.reply_document(video_file, caption=caption, parse_mode='HTML')
                if is_tiktok_video:
                    AUDIO_URL_CACHE[sent_message.message_id] = {
                        "filepath": download_info['filepath'],
                        "original_url": original_url,
                        "host": chosen_host
                    }
                    button = InlineKeyboardButton(text="🎧ИЗВЛЕЧЬ ЗВУК", callback_data=f"extract_audio:{sent_message.message_id}")
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
                    await bot.edit_message_reply_markup(chat_id=sent_message.chat.id, message_id=sent_message.message_id, reply_markup=keyboard)
                
                asyncio.create_task(delete_temp_file(download_info['filepath'], delay=600))
            except Exception as e:
                logging.exception("Error sending document.")
                await msg.reply(f"❌ ВНУТРЕННЯЯ ОШИБКА: {e}")
        else:
            await msg.reply("❌ ВНУТРЕННЯЯ ОШИБКА СКАЧИВАНИЯ (COBALT).")