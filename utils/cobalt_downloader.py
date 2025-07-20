import asyncio
import random
import re
import aiohttp
from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.methods import SetMessageReaction
from aiogram.types import Message, ReactionTypeEmoji, FSInputFile
import os

TEMP_DOWNLOAD_DIR = "temp_downloads"
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)

# you can add own cobalt host here
COBALT_API_HOSTS = [
    "co.itsv1eds.ru",
    "co.eepy.today",
    "co.otomir23.me"
]

def get_cobalt_link(text: str) -> str | None:
    """Finds a link supported by Cobalt in a given text."""
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

async def download_with_cobalt(url: str) -> dict | None:
    """
    Downloads a file using a random Cobalt API instance,
    with retries on different hosts if one fails.
    """
    available_hosts = COBALT_API_HOSTS.copy()
    random.shuffle(available_hosts)

    payload = {"url": url, "videoQuality": "720"}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    timeout = aiohttp.ClientTimeout(total=5)

    while available_hosts:
        host = available_hosts.pop()
        api_url = f"https://{host}/"
        print(f"Trying Cobalt API host: {host}")

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Handle both 'stream' and 'tunnel' statuses as success
                        if data.get("status") in ["stream", "tunnel"]:
                            download_url = data.get("url")
                            filename = data.get("filename", download_url.split("/")[-1].split("?")[0])
                            filepath = os.path.join(TEMP_DOWNLOAD_DIR, filename)

                            print(f"Success with host {host}. Downloading from: {download_url}")

                            async with session.get(download_url, timeout=aiohttp.ClientTimeout(total=60)) as file_response:
                                if file_response.status == 200:
                                    with open(filepath, "wb") as f:
                                        f.write(await file_response.read())
                                    return {"filepath": filepath, "filename": filename}
                                else:
                                    print(f"Failed to download file from {download_url}. Status: {file_response.status}")
                                    continue
                        else:
                            print(f"Host {host} returned unexpected status: {data}")
                            continue
                    else:
                        print(f"Error from host {host}: {response.status} - {await response.text()}")
                        continue
        except Exception as e:
            print(f"An unexpected error occurred with host {host}: {e}")
            continue

    print("All Cobalt API hosts failed.")
    return None


async def delete_temp_file(filepath: str):
    """Deletes a temporary file after a delay."""
    await asyncio.sleep(20)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted temporary file: {filepath}")
    except Exception as e:
        print(f"Error deleting temporary file {filepath}: {e}")
        pass

async def do_cobalt_download(msg: Message, bot: Bot, is_youtube_fallback: bool = False):
    """Handles the download process with Cobalt."""
    message_text = msg.text if msg.text else " "
    url = None

    if is_youtube_fallback:
        url_match = re.search(r'https?://[^\s]+', message_text)
        if url_match:
            url = url_match.group(0)
    else:
        url = get_cobalt_link(message_text)

    if not url:
        return

    print(f"Detected link for Cobalt: {url} from {msg.from_user.full_name}")

    try:
        await bot(SetMessageReaction(chat_id=msg.chat.id, message_id=msg.message_id,
                                 reaction=[ReactionTypeEmoji(emoji="👾")]))
        await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.UPLOAD_DOCUMENT)
    except Exception as e:
        print(f"Could not set reaction: {e}")

    download_info = await download_with_cobalt(url)
    if download_info and download_info['filepath']:
        video_file = FSInputFile(download_info['filepath'], filename=download_info['filename'])
        try:
            await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.UPLOAD_VIDEO)
            # Sending as a document, as there is no description to show in a video caption
            await msg.reply_document(video_file)
            asyncio.create_task(delete_temp_file(download_info['filepath']))
        except Exception as e:
            await msg.reply(f"❌ ВНУТРЕННЯЯ\nОШИБКА\nСКАЧИВАНИЯ (COBALT).\n\nОШИБКА:\n{e}")
    else:
        await msg.reply(f"❌ ВНУТРЕННЯЯ\nОШИБКА\nСКАЧИВАНИЯ (COBALT).")
        print(f"Failed to download from Cobalt for {url}")