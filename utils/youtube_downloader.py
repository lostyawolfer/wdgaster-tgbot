import os
import yt_dlp
import asyncio
import re

from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.methods import SetMessageReaction
from aiogram.types import Message, ReactionTypeEmoji, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from data.cache import YT_AUDIO_CACHE

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
        'writesinglejson': True,
        'force_single_and_subtitle_files': True,
        'writethumbnail': True,
        'embed_thumbnail': False,
    }

    filepath = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            filepath = ydl.prepare_filename(info_dict)

            if info_dict and 'title' in info_dict and filepath and os.path.exists(filepath):
                return {
                    "filepath": filepath,
                    "title": info_dict.get('title', 'НЕИЗВЕСТНОЕ НАЗВАНИЕ'),
                    "duration": info_dict.get('duration', 0),
                    "description": info_dict.get('description', ''),
                    "uploader": info_dict.get('uploader', 'Unknown Artist')
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

async def delete_temp_file(filepath: str, delay: int = 20):
    await asyncio.sleep(delay)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted temporary file: {filepath}")
    except Exception as e:
        print(f"Error deleting temporary file {filepath}: {e}")
        pass

async def do_youtube(msg: Message, bot: Bot) -> bool:
    message_text = msg.text if msg.text else " "
    video_id = get_youtube_video_id(message_text)

    if not video_id:
        return True

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Detected YouTube link: {video_url} from {msg.from_user.full_name}")

    try:
        await bot(SetMessageReaction(chat_id=msg.chat.id, message_id=msg.message_id,
                                     reaction=[ReactionTypeEmoji(emoji="👾")]))
        await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.RECORD_VIDEO)
    except Exception as e:
        print(f"Could not set reaction: {e}")


    video_info = await download_youtube_video(video_url)
    if video_info and video_info['filepath']:
        video_file = FSInputFile(video_info['filepath'])
        caption_parts = [f"<b><u>{video_info['title']}</u></b>"]
        if video_info['description']:
            description_escaped = video_info['description'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if len(description_escaped) > 1024:
                description_escaped = description_escaped[:1021] + "..."
            caption_parts.append(f"<blockquote expandable>{description_escaped}</blockquote>")

        final_caption = "\n".join(caption_parts)
        if len(final_caption) > 1024:
            final_caption = final_caption[:1011] + "...</blockquote>"

        try:
            await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.UPLOAD_VIDEO)
            sent_message = await msg.reply_video(
                video_file,
                caption=final_caption,
                parse_mode='HTML',
                duration=video_info.get('duration')
            )

            # --- Start of changes ---
            YT_AUDIO_CACHE[sent_message.message_id] = {
                "filepath": video_info['filepath'],
                "title": video_info['title'],
                "artist": video_info['uploader']
            }
            button = InlineKeyboardButton(text="🎧ИЗВЛЕЧЬ ЗВУК", callback_data=f"extract_youtube_audio:{sent_message.message_id}")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
            await bot.edit_message_reply_markup(chat_id=sent_message.chat.id, message_id=sent_message.message_id, reply_markup=keyboard)
            # --- End of changes ---

        except Exception as e:
            await msg.reply(f"❌ НЕ УДАЛОСЬ ОПРАВИТЬ ФАЙЛ.\n\nОШИБКА:\n{e}")

        # Don't delete immediately, wait for potential audio extraction
        asyncio.create_task(delete_temp_file(video_info['filepath'], delay=600))
        return True
    else:
        print(f"yt-dlp failed to download video for {video_url}. Triggering fallback.")
        return False