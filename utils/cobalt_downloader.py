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
            
            if data.get("status") in ["local-processing", "picker"] and data.get("output", {}).get("metadata"):
                metadata = data["output"]["metadata"]
                return {
                    "title": metadata.get("title"),
                    "artist": metadata.get("artist")
                }
            return None
    except Exception as e:
        logging.exception(f"An error occurred during Cobalt metadata request for URL {url}")
        return None

async def download_with_cobalt(session: aiohttp.ClientSession, url: str, host: str) -> tuple[dict | list | None, dict | None]:
    payload = {"url": url, "videoQuality": "720"}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    api_url = f"https://{host}/"
    logging.info(f"Requesting from {api_url} for URL: {url}")

    try:
        async with session.post(api_url, json=payload, headers=headers, timeout=45) as response:
            if response.status != 200:
                logging.error(f"Request to Cobalt failed: {response.status} - {await response.text()}")
                return None, None
            
            data = await response.json()
            logging.info(f"Cobalt response: {data}")

            if data.get("status") == "picker":
                downloaded_files = []
                for item in data.get("picker", []):
                    item_url = item.get("url")
                    if item_url:
                        filename = os.path.basename(item_url.split('?')[0])
                        filepath = os.path.join(TEMP_DOWNLOAD_DIR, f"{random.randint(1000, 9999)}_{filename}")
                        async with session.get(item_url, timeout=60) as file_response:
                            if file_response.status == 200:
                                content = await file_response.read()
                                if content:
                                    with open(filepath, "wb") as f:
                                        f.write(content)
                                    downloaded_files.append({"filepath": filepath, "type": item.get("type")})
                return downloaded_files, data
            
            elif data.get("status") in ["stream", "tunnel"]:
                download_url = data.get("url")
                filename = data.get("filename", "video.mp4")
                filepath = os.path.join(TEMP_DOWNLOAD_DIR, f"{random.randint(1000, 9999)}_{filename}")

                async with session.get(download_url, timeout=60) as file_response:
                    if file_response.status == 200:
                        content = await file_response.read()
                        if not content:
                            logging.error(f"Downloaded file from {download_url} is empty.")
                            return None, data
                        with open(filepath, "wb") as f:
                            f.write(content)
                        return {"filepath": filepath, "filename": filename}, data
            else:
                logging.error(f"Host {host} returned unexpected status: {data}")
                return None, data
    except Exception as e:
        logging.exception(f"An unexpected error occurred during download for URL {url}")
        return None, None

async def delete_temp_file(filepath: str, delay: int = 30):
    await asyncio.sleep(delay)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"Deleted temporary file: {filepath}")
    except Exception as e:
        logging.error(f"Error deleting temporary file {filepath}: {e}")

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
    
    is_tiktok_video = not is_youtube_fallback and 'tiktok.com' in url and '/photo/' not in url
    is_tiktok_photo = not is_youtube_fallback and 'tiktok.com' in url and '/photo/' in url
    
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0...'}) as session:
        chosen_host = random.choice(COBALT_API_HOSTS)
        
        try:
            await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.UPLOAD_DOCUMENT)
        except Exception: pass

        download_info, cobalt_response = await download_with_cobalt(session, url, chosen_host)

        if download_info:
            author_name = "АВТОР"
            author_url = "#"
            description = ""
            
            # Отримання метаданих
            if is_tiktok_photo and cobalt_response and cobalt_response.get("audioFilename"):
                # Для галерей найнадійніше брати з назви аудіофайлу
                match = re.search(r'tiktok_([^_]+)_', cobalt_response["audioFilename"])
                if match:
                    username = match.group(1)
                    author_name = username
                    author_url = f"https://www.tiktok.com/@{username}"
            elif is_tiktok_video:
                # Для відео oEmbed працює добре
                metadata = await get_tiktok_oembed_info(url)
                if metadata:
                    author_name = metadata.get("artist", author_name)
                    author_url = metadata.get("author_url", author_url)
                    description = metadata.get("title", description)

            caption = f'<a href="{author_url}">{author_name.upper()}</a>'
            if description:
                caption += f'\n\n<blockquote expandable>{description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</blockquote>'

            # Логіка для галерей
            if isinstance(download_info, list):
                media_group = MediaGroupBuilder()
                
                if download_info:
                    first_item = download_info.pop(0)
                    media_group.add_photo(media=FSInputFile(first_item['filepath']), caption=caption, parse_mode='HTML')
                    asyncio.create_task(delete_temp_file(first_item['filepath'], delay=600))
                
                for item in download_info:
                    if item.get("type") == "photo":
                        media_group.add_photo(media=FSInputFile(item['filepath']))
                        asyncio.create_task(delete_temp_file(item['filepath'], delay=600))
                
                try:
                    if media_group.build():
                        await msg.reply_media_group(media=media_group.build())
                except Exception as e:
                    logging.exception("Error sending media group.")
                    await msg.reply(f"❌ ВНУТРЕННЯЯ ОШИБКА: {e}")

            # Логіка для одного файлу (відео)
            elif isinstance(download_info, dict) and download_info.get('filepath'):
                video_file = FSInputFile(download_info['filepath'], filename=download_info['filename'])
                
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