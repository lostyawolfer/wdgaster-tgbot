import os
import asyncio
import re
import logging
from aiogram import Router, F, Bot
from aiogram.enums import ChatType
from aiogram.types import Message, ChatFullInfo, FSInputFile, CallbackQuery
from db.db import Pronouns
from utils.check_admin import check_admin
from utils.delete_message import delete_message
from info.help_text import help_text, startup_announce
from info.message_triggers import contains_triggers, admin_action_triggers, channel_post_triggers, exact_matches_triggers
from info.rules import rules
from utils.pronouns import do_pronouns
from utils.recognize_song_from_file import recognize_song_from_file
from utils.update import update
from utils.wingdings_conversion_map import conversion_map, conversion_map_backwards
from utils.youtube_downloader import do_youtube, get_youtube_video_id
from utils.cobalt_downloader import (
    do_cobalt_download, get_cobalt_link, get_tiktok_oembed_info, delete_temp_file,
    download_with_cobalt
)
from utils.ffmpeg_extract_audio import ffmpeg_extract_audio
from utils.string_stuff import *
from data.loader import main_chat_id
from data.cache import AUDIO_URL_CACHE, YT_AUDIO_CACHE
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


def is_this_a_comment_section(chat: ChatFullInfo) -> bool:
    logging.info(f"Checking if chat is a comment section. Linked chat ID: {chat.linked_chat_id}")
    return chat.linked_chat_id is not None


@router.message(F.chat.type.in_({ChatType.SUPERGROUP, ChatType.GROUP}))
async def main(msg: Message, bot: Bot):
    global deactivated
    message_text = msg.text if msg.text else "<В СООБЩЕНИИ НЕТ ТЕКСТА.>"
    chat_member = await bot.get_chat_member(chat_id=msg.chat.id, user_id=msg.from_user.id)
    is_admin = False
    is_admin = check_admin(chat_member, msg)
    is_decorative_admin = check_admin(chat_member, msg, decorative=True)

    chat_info = await bot.get_chat(msg.chat.id)
    if is_this_a_comment_section(chat_info):
        await delete_message(msg, bot, is_admin, is_decorative_admin)

    message_command = is_message_command(message_text.lower())

    if message_command:
        if is_any_from(message_command, ["повтори"]) and msg.from_user.id == 653632008:
            await msg.delete()
            content = message_command[len("повтори "):].strip()
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

        if is_any_from(message_command, ["обновись", "обновить"]) and msg.from_user.id == 653632008:
            await update(msg, bot)
            return

        if is_any_from(message_command, ["врубись", "включись", "воскресни"]) and (is_admin or msg.from_user.id == 653632008):
            deactivated = False
            await msg.reply('БОТ СНОВА АКТИВЕН.')
            return

        if deactivated:
            return

        if is_any_from(message_command, ["вырубись", "выключись", "убейся"]) and (is_admin or msg.from_user.id == 653632008):
            deactivated = True
            await msg.reply('БОТ ДЕАКТИВИРОВАН.\nВКЛЮЧИТЬ: Г!ВКЛЮЧИСЬ')
            return

        if msg.new_chat_members:
            await msg.reply(
                "ПРИВЕТСТВУЮ.\n\nПО ВЕЛЕНИЮ\nНАРКОЧУЩЕГО РЫЦАРЯ\nЗДЕСЬ ВСЕ РАСКИДЫВАЮТ ЗАКЛАДКИ\nИ ОТКРЫВАЮТ ФОНТАНЫ.\n\nТЕБЕ ТОЖЕ ПРЕДСТОИТ\nСДЕЛАТЬ В ЭТО\nСВОЙ ВКЛАД.\n\n------------\n\nЯ - ВИНГ ГАСТЕР, КОРОЛЕВСКИЙ УЧЁНЫЙ!\n\nМОЖЕШЬ ДОБАВИТЬ СВОИ МЕСТОИМЕНИЯ КОМАНДОЙ +МЕСТ.\n\nЧТОБЫ УЗНАТЬ ОСТАЛЬНЫЕ МОИ ВОЗМОЖНОСТИ, НАПИШИ \"ГАСТЕР КОМАНДЫ\".\n\nНЕ ЗАБУДЬ ПОСМОТРЕТЬ ПРАВИЛА ГРУППЫ\nВ ЗАКРЕПЛЁННЫХ.")
            return

        if is_any_from(message_command, ["команды", "помощь"]):
            await msg.reply(help_text, parse_mode='HTML', disable_web_page_preview=True)

        if is_any_from(message_command, ["др рп", "ссылка на др рп", "рб", "роблокс", "ссылка на рб", "ссылка на роблокс"]):
            await msg.reply("НАШ СЕРВЕР:\nhttps://www.roblox.com/share?code=b01c5b9a6e97114ea80908cc1225e39d&type=Server")
            return

        if is_any_from(message_command, ["кто создал", "создатель"]):
            await msg.reply("@LOSTYAWOLFER")

        if is_any_from(message_command, ["созвать админов", "позвать админов", "позови админов", "у нас проблемы"]):
            await msg.reply("<b><u>ВЫЗЫВАЮ ВСЕХ АДМИНИСТРАТОРОВ</u></b>\n"
                            "ОБРАТИ ВНИМАНИЕ, ЧТО ИСПОЛЬЗОВАНИЕ ЭТОЙ КОМАНДЫ В СИТУАЦИЯХ, КОТОРЫЕ ЭТОГО НЕ ТРЕБУЮТ, КАРАЕТСЯ ВАРНОМ.\n\n"
                            "@HEHE_FITILECHEK @CRISPXMINT @AZUREOUSHUE @DAS_FICK @LITA_PENGUI @WHENIMDEAD @MASLO13KINNIE @LOSTYAWOLFER", parse_mode='HTML')

        if is_any_from(message_command, ["оне/ено", "оне", "неомест", "неоместоимения"]):
            await msg.reply_photo(FSInputFile(os.path.join('images', 'neopronouns.png')),
                                  caption="ОНЕ/ЕНО - НЕОМЕСТОИМЕНИЕ АВТОРСТВА @LOSTYAWOLFER,\nПРИЗВАННОЕ БЫТЬ ПОЛНОЙ АЛЬТЕРНАТИВОЙ\nАНГЛИЙСКОГО \"THEY/THEM\"\nВ ЕДИНСТВЕННОМ ЧИСЛЕ.\n\nДЛЯ НЕИЗВЕСТНЫХ ЛЮДЕЙ,\nДЛЯ ЛЮДЕЙ НЕБИНАРНЫХ...\nВЫБОР ЗА ТОБОЙ.\n\nЭТОТ ЕГО ЭКСПЕРИМЕНТ\nМНЕ КАЖЕТСЯ\nОЧЕНЬ\nОЧЕНЬ\nИНТЕРЕСНЫМ.")
            return

        if is_any_from_startswith(message_command, ["правило ", "правила "]):
            requested_rule = message_command[len("правило "):]
            resulting_rule = rules.get(requested_rule)
            if resulting_rule:
                await msg.reply(resulting_rule, parse_mode='HTML')
            else:
                await msg.reply("ТАКОГО ПРАВИЛА\nНЕ СУЩЕСТВУЕТ.")
            return

        if is_any_from_startswith(message_command, ["спойлеры"]):
            await msg.reply(
                "НА ДАННЫЙ МОМЕНТ,\nСПОЙЛЕРНЫЙ РЕЖИМ ОТКЛЮЧЕН.\n\nПОСЛЕДНИЙ РАЗ СПОЙЛЕРНЫЙ РЕЖИМ\nБЫЛ АКТИВЕН\n<b>13 ИЮЛЯ.</b>",
                parse_mode='HTML')
            return

        if is_any_from_startswith(message_command, ["вингдингс "]):
            requested_text = message_command[len("вингдингс "):]
            converted_text = ""
            for char in requested_text:
                converted_text += conversion_map.get(char, char)
            await msg.reply(f'<b><u>ЗАШИФРОВАННЫЙ В WINGDINGS ТЕКСТ:</u></b>\n\n{converted_text}', parse_mode='HTML')
            return

    if deactivated:
        return

    await do_pronouns(msg, bot)


    if get_youtube_video_id(message_text) or get_cobalt_link(message_text):
        if get_youtube_video_id(message_text):
            if not await do_youtube(msg, bot):
                await do_cobalt_download(msg, bot, is_youtube_fallback=True)
        else:
            await do_cobalt_download(msg, bot)
        return


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


    if message_text.lower() == "лостя фембой":
        await msg.reply_photo(FSInputFile(os.path.join('images', 'lostya_femboy.jpg')))

    if msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id and (message_text.lower() == "кто ты" or message_text.lower() == "ты кто"):
        await msg.reply("Я ВИНГ ГАСТЕР! КОРОЛЕВСКИЙ УЧЁНЫЙ")

    if msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id and (message_text.lower() == "дуэль"):
        await msg.reply("МОЯ ПОБЕДА ПРИВЕЛА К ТВОЕЙ СМЕРТИ.\nМНЕ ПРИШЛОСЬ ОТКАТЫВАТЬ РЕАЛЬНОСТЬ\nИСКЛЮЧИТЕЛЬНО\nЧТОБЫ ВОЗРОДИТЬ ТЕБЯ.")



# --- Start of changes ---

#
# extract audio from tiktok/twitter/etc video
#
@router.callback_query(F.data.startswith("extract_audio:"))
async def handle_extract_audio(callback_query: CallbackQuery, bot: Bot):
    message_id = int(callback_query.data.split(":", 1)[1])
    original_message = callback_query.message
    logging.info(f"Callback received for message_id: {message_id}")

    await bot.edit_message_reply_markup(
        chat_id=original_message.chat.id,
        message_id=original_message.message_id,
        reply_markup=None
    )

    cache_entry = AUDIO_URL_CACHE.get(message_id)
    if not cache_entry:
        await callback_query.answer("ОШИБКА.\nДАННЫЕ ИССЕЗЛИ.", show_alert=True)
        return

    video_filepath = cache_entry["filepath"]

    # Re-download if file is missing
    if not os.path.exists(video_filepath):
        await callback_query.answer("ФАЙЛ УДАЛЁН ИЗ КЕША.\nПОВТОРНО ЗАГРУЖАЮ...", show_alert=False)
        async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0...'}) as session:
            download_info, _ = await download_with_cobalt(session, cache_entry["original_url"], cache_entry["host"])
            if download_info and isinstance(download_info, dict) and download_info.get('filepath'):
                video_filepath = download_info['filepath']
                # Update cache entry with new filepath to prevent re-downloading again
                AUDIO_URL_CACHE[message_id]['filepath'] = video_filepath
            else:
                await original_message.reply("НЕ УДАЛОСЬ\nПОВТОРНО ЗАГРУЗИТЬ\nВИДЕО.")
                return

    await callback_query.answer("ИЗВЛЕКАЮ ЗВУК...\nЭТОТ ПРОЦЕСС\nМОЖЕТ ЗАНЯТЬ\nНЕКОТОРОЕ ВРЕМЯ.", show_alert=False)

    audio_path = f"{os.path.splitext(video_filepath)[0]}.mp3"
    
    async with aiohttp.ClientSession() as session:
        success = await ffmpeg_extract_audio(video_filepath, audio_path, {})
        if not success:
            await original_message.reply("НЕ УДАЛОСЬ\nИЗВЛЕЧЬ\nЗВУК.")
            return

        # Try to recognize the song
        caption_text = await recognize_song_from_file(session, audio_path)

        # Get metadata for the audio title
        oembed_data = await get_tiktok_oembed_info(cache_entry["original_url"])
        metadata = {"title": "Audio", "artist": "Unknown"}
        if oembed_data:
            metadata = {"title": oembed_data.get("title"), "artist": oembed_data.get("author_name")}

        try:
            audio_file = FSInputFile(audio_path)
            # Send audio regardless of shazam result
            await original_message.reply_audio(
                audio=audio_file,
                title=metadata.get("title"),
                performer=metadata.get("artist"),
                caption=caption_text if caption_text else None, # Caption will only be added if song is recognized
                parse_mode='HTML'
            )
        except Exception as e:
            logging.exception("An error occurred while sending extracted audio.")
            await original_message.reply(f"ПРОИЗОШЛА\nВНУТРЕННЯЯ\nОШИБКА:\n{e}")
        finally:
            # Clean up temp files
            await delete_temp_file(audio_path, delay=10)
            if message_id in AUDIO_URL_CACHE:
                del AUDIO_URL_CACHE[message_id]

#
# extract audio from youtube video
#
@router.callback_query(F.data.startswith("extract_youtube_audio:"))
async def handle_extract_youtube_audio(callback_query: CallbackQuery, bot: Bot):
    message_id = int(callback_query.data.split(":", 1)[1])
    original_message = callback_query.message
    logging.info(f"YouTube audio extraction callback received for message_id: {message_id}")

    await bot.edit_message_reply_markup(
        chat_id=original_message.chat.id,
        message_id=original_message.message_id,
        reply_markup=None
    )

    cache_entry = YT_AUDIO_CACHE.get(message_id)
    if not cache_entry:
        await callback_query.answer("ОШИБКА.\nДАННЫЕ ИССЕЗЛИ.\nПОПРОБУЙТЕ ОТПРАВИТЬ ССЫЛКУ СНОВА.", show_alert=True)
        return

    video_filepath = cache_entry["filepath"]
    if not os.path.exists(video_filepath):
        await callback_query.answer("ОШИБКА.\nИСХОДНЫЙ ФАЙЛ УЖЕ УДАЛЁН.\nПОПРОБУЙТЕ ОТПРАВИТЬ ССЫЛКУ СНОВА.", show_alert=True)
        return

    await callback_query.answer("ИЗВЛЕКАЮ ЗВУК...\nЭТОТ ПРОЦЕСС\nМОЖЕТ ЗАНЯТЬ\nНЕКОТОРОЕ ВРЕМЯ.", show_alert=False)

    audio_path = f"{os.path.splitext(video_filepath)[0]}.mp3"

    success = await ffmpeg_extract_audio(video_filepath, audio_path, {})
    if not success:
        await original_message.reply("НЕ УДАЛОСЬ\nИЗВЛЕЧЬ\nЗВУК.")
        return

    try:
        audio_file = FSInputFile(audio_path)
        await original_message.reply_audio(
            audio=audio_file,
            title=cache_entry.get("title", "Audio"),
            performer=cache_entry.get("artist", "Unknown Artist")
        )
    except Exception as e:
        logging.exception("An error occurred while sending extracted YouTube audio.")
        await original_message.reply(f"ПРОИЗОШЛА\nВНУТРЕННЯЯ\nОШИБКА:\n{e}")
    finally:
        # Clean up temp files
        await delete_temp_file(audio_path, delay=10)
        if message_id in YT_AUDIO_CACHE:
            del YT_AUDIO_CACHE[message_id]

# --- End of changes ---