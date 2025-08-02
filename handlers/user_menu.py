import os
import asyncio
import re
import logging
import subprocess
from aiogram import Router, F, Bot
from aiogram.enums import ChatType
from aiogram.types import Message, ChatFullInfo, FSInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from db.db import Pronouns
from utils.check_admin import check_admin
from utils.delete_message import delete_message
from info.help_text import help_text, startup_announce
from info.message_triggers import contains_triggers, admin_action_triggers, channel_post_triggers, exact_matches_triggers
from utils.pronouns import do_pronouns
from utils.update import update
from utils.youtube_downloader import do_youtube, get_youtube_video_id
from utils.cobalt_downloader import (
    do_cobalt_download, get_cobalt_link, get_tiktok_oembed_info,
    get_cobalt_audio_metadata, delete_temp_file
)
from data.loader import main_chat_id
from data.cache import AUDIO_URL_CACHE
import aiohttp

deactivated = False

router = Router()
db_pronouns = Pronouns()

@router.startup()
async def on_startup_notify(bot: Bot):
    await bot.send_message(
        chat_id=main_chat_id,
        text=startup_announce,
        parse_mode='HTML'
    )

def trigger_message(triggers: dict, main_str: str, check_method: int = 0, is_admin = False, channel_message = False):
    for s in triggers.keys():
        if check_method == 0 and s in main_str and not channel_message:
            return triggers[s]
        elif check_method == 1 and main_str.startswith(s) and is_admin:
            return triggers[s]
        elif check_method == 2 and s in main_str and channel_message:
            return triggers[s]
        elif check_method == 3 and main_str == s and not channel_message:
            return triggers[s]
    return None

def is_this_a_comment_section(chat: ChatFullInfo) -> bool:
    logging.info(f"Checking if chat is a comment section. Linked chat ID: {chat.linked_chat_id}")
    return chat.linked_chat_id is not None

async def extract_audio_with_ffmpeg(video_path: str, audio_path: str, metadata: dict) -> bool:
    """Конвертирует аудио в MP3 и встраивает метаданные."""
    try:
        command = [
            'ffmpeg', '-i', video_path,
            '-vn',                # Отключить видео
            '-acodec', 'libmp3lame',# Указать кодек MP3
            '-q:a', '2',          # Высокое качество VBR
            '-y'                  # Перезаписать файл
        ]
        
        # Добавляем метаданные, если они есть
        if metadata.get("title"):
            command.extend(['-metadata', f'title={metadata["title"]}'])
        if metadata.get("artist"):
            command.extend(['-metadata', f'artist={metadata["artist"]}'])
        
        command.append(audio_path)
        
        logging.info(f"Running FFmpeg command: {' '.join(command)}")
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, stderr = await process.communicate()
        
        if process.returncode != 0:
            logging.error(f"FFmpeg failed. Stderr: {stderr.decode(errors='ignore')}")
            return False
        
        return os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
            
    except FileNotFoundError:
        logging.error("FFmpeg command not found. Make sure FFmpeg is installed and in your system's PATH.")
        return False
    except Exception:
        logging.exception("An exception occurred during FFmpeg audio extraction.")
        return False

@router.message(F.chat.type.in_({ChatType.SUPERGROUP, ChatType.GROUP, ChatType.PRIVATE}))
async def main(msg: Message, bot: Bot):
    message_text = msg.text if msg.text else " "
    is_admin = False
    if msg.chat.type != ChatType.PRIVATE:
        try:
            chat_member = await bot.get_chat_member(chat_id=msg.chat.id, user_id=msg.from_user.id)
            is_admin = check_admin(chat_member, msg)
            is_decorative_admin = check_admin(chat_member, msg, decorative=True)
            chat_info = await bot.get_chat(msg.chat.id)
            if is_this_a_comment_section(chat_info):
                await delete_message(msg, bot, is_admin, is_decorative_admin)
                return
        except Exception as e:
            logging.error(f"Error in group-specific logic for chat {msg.chat.id}: {e}")

    if message_text.lower() == "г!обновись" and msg.from_user.id == 653632008:
        await update(msg, bot)
        return

    global deactivated
    if (message_text.lower() in ["г!вырубись", "г!выключись", "г!убейся"]) and is_admin:
        deactivated = True
        await msg.reply('БОТ ДЕАКТИВИРОВАН.\nВКЛЮЧИТЬ: Г!ВКЛЮЧИСЬ'.upper())
        return
    if (message_text.lower() in ["г!врубись", "г!включись", "г!воскресни"]) and is_admin:
        deactivated = False
        await msg.reply('БОТ СНОВА АКТИВЕН.'.upper())
        return
    if deactivated:
        return

    if msg.new_chat_members:
        await msg.reply(
            "ПРИВЕТСТВУЮ.\n\nПО ВЕЛЕНИЮ\nНАРКОЧУЩЕГО РЫЦАРЯ\nЗДЕСЬ ВСЕ РАСКИДЫВАЮТ ЗАКЛАДКИ\nИ ОТКРЫВАЮТ ФОНТАНЫ.\n\nТЕБЕ ТОЖЕ ПРЕДСТОИТ\nСДЕЛАТЬ СВОЙ ВКЛАД\nВ ЭТО.\n\n-----------------\n\nЯ - ВИНГ ГАСТЕР, КОРОЛЕВСКИЙ УЧЁНЫЙ ЭТОЙ ГРУППЫ.\n\nМОЖЕШЬ ДОБАВИТЬ СВОИ МЕСТОИМЕНИЯ КОМАНДОЙ +МЕСТ.\n\nЧТОБЫ УЗНАТЬ ОСТАЛЬНЫЕ МОИ ВОЗМОЖНОСТИ, НАПИШИ \"ГАСТЕР КОМАНДЫ\".\n\nНЕ ЗАБУДЬ ПОСМОТРЕТЬ ПРАВИЛА ГРУППЫ\nВ ЗАКРЕПЛЁННЫХ.")
        return

    if get_youtube_video_id(message_text) or get_cobalt_link(message_text):
        if get_youtube_video_id(message_text):
            if not await do_youtube(msg, bot):
                await do_cobalt_download(msg, bot, is_youtube_fallback=True)
        else:
            await do_cobalt_download(msg, bot)

    await do_pronouns(msg, bot)

    # funny reply triggers
    trigger = trigger_message(contains_triggers, message_text.lower(), check_method=0, channel_message=msg.is_automatic_forward)
    if trigger is not None:
        await msg.reply(trigger)

    trigger = trigger_message(exact_matches_triggers, message_text.lower(), check_method=3, channel_message=msg.is_automatic_forward)
    if trigger is not None:
        await msg.reply(trigger)

    if msg.chat.type != ChatType.PRIVATE:
        trigger = trigger_message(admin_action_triggers, message_text.lower(), check_method=1, is_admin=is_admin)
        if trigger is not None:
            await msg.reply(trigger)

    trigger = trigger_message(channel_post_triggers, message_text.lower(), check_method=2, channel_message=msg.is_automatic_forward)
    if trigger is not None:
        await msg.reply(trigger)

    if message_text.lower() == "гастер оне/ено" or message_text.lower() == "гастер оне" or message_text.lower() == "гастер неомест":
        await msg.reply_photo(FSInputFile(os.path.join('images', 'neopronouns.png')), caption="ОНЕ/ЕНО - НЕОМЕСТОИМЕНИЕ АВТОРСТВА @LOSTYAWOLFER,\nПРИЗВАННОЕ БЫТЬ ПОЛНОЙ АЛЬТЕРНАТИВОЙ\nАНГЛИЙСКОГО \"THEY/THEM\"\nВ ЕДИНСТВЕННОМ ЧИСЛЕ.\n\nДЛЯ НЕИЗВЕСТНЫХ ЛЮДЕЙ,\nДЛЯ ЛЮДЕЙ НЕБИНАРНЫХ...\nВЫБОР ЗА ТОБОЙ.\n\nЭТОТ ЕГО ЭКСПЕРИМЕНТ\nМНЕ КАЖЕТСЯ\nОЧЕНЬ\nОЧЕНЬ\nИНТЕРЕСНЫМ.")

    if message_text.lower() == "лостя фембой":
        await msg.reply_photo(FSInputFile(os.path.join('images', 'lostya_femboy.jpg')))

    if message_text.lower() == "гастер спойлеры":
        await msg.reply(f"НА ДАННЫЙ МОМЕНТ,\nСПОЙЛЕРНЫЙ РЕЖИМ ОТКЛЮЧЕН.\n\nПОСЛЕДНИЙ РАЗ СПОЙЛЕРНЫЙ РЕЖИМ\nБЫЛ АКТИВЕН\n<b>13 ИЮЛЯ.</b>", parse_mode='HTML')

    if msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id and (message_text.lower() == "кто ты" or message_text.lower() == "ты кто"):
        await msg.reply("Я ВИНГ ГАСТЕР! КОРОЛЕВСКИЙ УЧЁНЫЙ")

    if msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id and (message_text.lower() == "дуэль"):
        await msg.reply("МОЯ ПОБЕДА ПРИВЕЛА К ТВОЕЙ СМЕРТИ.\nМНЕ ПРИШЛОСЬ ОТКАТЫВАТЬ РЕАЛЬНОСТЬ\nИСКЛЮЧИТЕЛЬНО\nЧТОБЫ ВОЗРОДИТЬ ТЕБЯ.")

    if message_text.lower() == "гастер команды":
        await msg.reply(help_text, parse_mode='HTML', disable_web_page_preview=True)

    if message_text.lower().startswith("г!повтори ") and msg.from_user.id == 653632008:
        await msg.delete()
        content = msg.text[len("г!повтори "):].strip()
        delay_match = re.match(r'^((\d+)\s*([сcмm]))\s*(.*)', content.lower())
        delay_seconds = 0
        text_to_repeat = content

        if delay_match:
            duration_value = int(delay_match.group(2))
            unit = delay_match.group(3)
            text_to_repeat = delay_match.group(4).strip()
            if unit in ('с', 'c'):
                delay_seconds = duration_value
            elif unit in ('м', 'm'):
                delay_seconds = duration_value * 60

        if delay_seconds:
            await asyncio.sleep(delay_seconds)

        if msg.reply_to_message:
            await msg.reply_to_message.reply(text_to_repeat.upper())
        else:
            await msg.answer(text_to_repeat.upper())

    #if is_admin and (message_text.lower().startswith("г!локдаун") or message_text.lower().startswith("г!локдаун"))

@router.callback_query(F.data.startswith("extract_audio:"))
async def handle_extract_audio(callback_query: CallbackQuery, bot: Bot):
    message_id = int(callback_query.data.split(":", 1)[1])
    original_message = callback_query.message
    logging.info(f"Callback received for message_id: {message_id}")

    cache_entry = AUDIO_URL_CACHE.get(message_id)
    if not cache_entry:
        await callback_query.answer("ОШИБКА: Данные не найдены.", show_alert=True)
        return

    video_filepath = cache_entry["filepath"]
    original_url = cache_entry["original_url"]
    host = cache_entry["host"]

    if not os.path.exists(video_filepath):
        await callback_query.answer("ОШИБКА: Исходный видеофайл уже удалён.", show_alert=True)
        return

    await callback_query.answer("ИЗВЛЕКАЮ ЗВУК...", show_alert=False)
    
    async with aiohttp.ClientSession() as session:
        metadata = await get_cobalt_audio_metadata(session, original_url, host)
    
    if not metadata or not metadata.get("title"):
        logging.warning("Failed to get metadata from Cobalt API, falling back to oEmbed.")
        oembed_data = await get_tiktok_oembed_info(original_url)
        if oembed_data:
            metadata = {"title": oembed_data.get("title"), "artist": oembed_data.get("artist")}
        else:
            metadata = {"title": "Audio", "artist": "Unknown"}
    
    audio_path = f"{os.path.splitext(video_filepath)[0]}.mp3"
    
    success = await extract_audio_with_ffmpeg(video_filepath, audio_path, metadata)
    
    if not success:
        await original_message.reply("❌ НЕ УДАЛОСЬ ИЗВЛЕЧЬ ЗВУК.")
        return
    
    try:
        audio_file = FSInputFile(audio_path)
        await original_message.reply_audio(
            audio=audio_file, 
            title=metadata.get("title"), 
            performer=metadata.get("artist")
        )

        await bot.edit_message_reply_markup(chat_id=original_message.chat.id, message_id=original_message.message_id, reply_markup=None)
        
        await delete_temp_file(audio_path, delay=10)

        if message_id in AUDIO_URL_CACHE:
            del AUDIO_URL_CACHE[message_id]
            
    except Exception as e:
        logging.exception("An error occurred while sending extracted audio.")
        await original_message.reply(f"❌ ПРОИЗОШЛА ВНУТРЕННЯЯ ОШИБКА: {e}")