import os
import asyncio
import re
from aiogram import Router, F, Bot
from aiogram.enums import ChatType
from aiogram.types import Message, ChatFullInfo, FSInputFile
from db.db import Pronouns
from utils.check_admin import check_admin
from utils.delete_message import delete_message
from info.help_text import help_text, startup_announce
from info.message_triggers import contains_triggers, admin_action_triggers, channel_post_triggers, exact_matches_triggers
from utils.pronouns import do_pronouns
from utils.update import update
from utils.youtube_downloader import do_youtube, get_youtube_video_id
from utils.cobalt_downloader import do_cobalt_download, get_cobalt_link
from data.loader import main_chat_id

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
    print(chat.linked_chat_id)
    return chat.linked_chat_id is not None

@router.message(F.chat.type.in_({ChatType.SUPERGROUP, ChatType.GROUP, ChatType.PRIVATE}))
async def main(msg: Message, bot: Bot):
    message_text = msg.text if msg.text else " "

    # --- Group-Specific Logic ---
    is_admin = False
    if msg.chat.type != ChatType.PRIVATE:
        chat_member = await bot.get_chat_member(chat_id=msg.chat.id, user_id=msg.from_user.id)
        is_admin = check_admin(chat_member, msg)
        is_decorative_admin = check_admin(chat_member, msg, decorative=True)

        if is_this_a_comment_section(await bot.get_chat(msg.chat.id)):
            await delete_message(msg, bot, is_admin, is_decorative_admin)
    # --- End Group-Specific Logic ---

    if message_text.lower() == "г!обновись" and msg.from_user.id == 653632008:
        await update(msg, bot)
        return

    global deactivated
    if (message_text.lower() == "г!вырубись" or message_text.lower() == "г!выключись" or message_text.lower() == "г!убейся") and is_admin:
        deactivated = True
        await msg.reply('БОТ ДЕАКТИВИРОВАН.\nВКЛЮЧИТЬ: Г!ВКЛЮЧИСЬ'.upper())

    if (message_text.lower() == "г!врубись" or message_text.lower() == "г!включись" or message_text.lower() == "г!воскресни") and is_admin:
        deactivated = False
        await msg.reply('БОТ СНОВА АКТИВЕН.'.upper())

    if deactivated:
        return

    if msg.new_chat_members:
        await msg.reply(
            "ПРИВЕТСТВУЮ.\n\nПО ВЕЛЕНИЮ\nНАРКОЧУЩЕГО РЫЦАРЯ\nЗДЕСЬ ВСЕ РАСКИДЫВАЮТ ЗАКЛАДКИ\nИ ОТКРЫВАЮТ ФОНТАНЫ.\n\nТЕБЕ ТОЖЕ ПРЕДСТОИТ\nСДЕЛАТЬ СВОЙ ВКЛАД\nВ ЭТО.\n\n-----------------\n\nЯ - ВИНГ ГАСТЕР, КОРОЛЕВСКИЙ УЧЁНЫЙ ЭТОЙ ГРУППЫ.\n\nМОЖЕШЬ ДОБАВИТЬ СВОИ МЕСТОИМЕНИЯ КОМАНДОЙ +МЕСТ.\n\nЧТОБЫ УЗНАТЬ ОСТАЛЬНЫЕ МОИ ВОЗМОЖНОСТИ, НАПИШИ \"ГАСТЕР КОМАНДЫ\".\n\nНЕ ЗАБУДЬ ПОСМОТРЕТЬ ПРАВИЛА ГРУППЫ\nВ ЗАКРЕПЛЁННЫХ.")


    # --- Downloader Logic ---
    is_youtube = get_youtube_video_id(message_text) is not None
    is_cobalt_supported = get_cobalt_link(message_text) is not None

    if is_youtube:
        yt_dlp_success = await do_youtube(msg, bot)
        if not yt_dlp_success:
            # If yt-dlp fails, fallback to cobalt
            await do_cobalt_download(msg, bot, is_youtube_fallback=True)
    elif is_cobalt_supported:
        # If it's not a YouTube link, but is another supported link, use cobalt
        await do_cobalt_download(msg, bot)
    # --- End Downloader Logic ---

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