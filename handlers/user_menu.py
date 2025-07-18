import os
import asyncio
import re

from aiogram import Router, F, Bot
from aiogram.enums import ChatType, ChatAction
from aiogram.methods import SetMessageReaction
from aiogram.types import Message, Chat, ChatFullInfo, FSInputFile, ReactionTypeEmoji
from db.db import Pronouns
from utils.check_admin import check_admin
from utils.delete_message import delete_message
from utils.help_text import help_text, startup_announce
from utils.message_triggers import contains_triggers, admin_action_triggers, channel_post_triggers, exact_matches_triggers
from utils.pronouns import do_pronouns
from utils.youtube_downloader import do_youtube
from data.loader import main_chat_id

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



@router.message(F.chat.type.in_({ChatType.SUPERGROUP}))
async def main(msg: Message, bot: Bot):
    chat_member = await bot.get_chat_member(chat_id=msg.chat.id, user_id=msg.from_user.id)
    # user_link = (f'\"<a href="tg://user?id={msg.from_user.id}">'
    #              f'{msg.from_user.full_name.replace("&", "&amp;")
    #              .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>\"')
    message_text = msg.text if msg.text else " "

    is_admin = check_admin(chat_member, msg)
    is_decorative_admin = check_admin(chat_member, msg, decorative=True)

    if is_this_a_comment_section(await bot.get_chat(msg.chat.id)):
        await delete_message(msg, bot, is_admin, is_decorative_admin)

    await do_youtube(msg, bot)
    await do_pronouns(msg, bot)



    # funny reply triggers
    trigger = trigger_message(contains_triggers, message_text.lower(), check_method=0, channel_message=msg.is_automatic_forward)
    if trigger is not None:
        await msg.reply(trigger)

    trigger = trigger_message(exact_matches_triggers, message_text.lower(), check_method=3, channel_message=msg.is_automatic_forward)
    if trigger is not None:
        await msg.reply(trigger)

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

    if msg.new_chat_members:
        await msg.reply("ПРИВЕТСТВУЮ.\n\nПО ВЕЛЕНИЮ\nНАРКОЧУЩЕГО РЫЦАРЯ\nЗДЕСЬ ВСЕ РАСКИДЫВАЮТ ЗАКЛАДКИ\nИ ОТКРЫВАЮТ ФОНТАНЫ.\n\nТЕБЕ ТОЖЕ ПРЕДСТОИТ\nСДЕЛАТЬ СВОЙ ВКЛАД\nВ ЭТО.\n\n-----------------\n\nЯ - ВИНГ ГАСТЕР, КОРОЛЕВСКИЙ УЧЁНЫЙ ЭТОЙ ГРУППЫ.\n\nМОЖЕШЬ ДОБАВИТЬ СВОИ МЕСТОИМЕНИЯ КОМАНДОЙ +МЕСТ.\n\nЧТОБЫ УЗНАТЬ ОСТАЛЬНЫЕ МОИ ВОЗМОЖНОСТИ, НАПИШИ \"ГАСТЕР КОМАНДЫ\".\n\nНЕ ЗАБУДЬ ПОСМОТРЕТЬ ПРАВИЛА ГРУППЫ\nВ ЗАКРЕПЛЁННЫХ.")

    if message_text.lower() == "гастер команды":
        await msg.reply(help_text, parse_mode='HTML', disable_web_page_preview=True)



    if message_text.lower().startswith("гастер повтори") and msg.from_user.id == 653632008:
        await msg.delete()
        content = msg.text[len("гастер повтори "):].strip()
        delay_match = re.match(r'^((\d+)\s*([сcмm]))\s*(.*)', content.lower())
        delay_seconds = 0  # Default no delay
        text_to_repeat = content  # By default, repeat everything

        if delay_match:
            full_delay_str = delay_match.group(1)  # e.g., "5с"
            duration_value = int(delay_match.group(2))  # e.g., 5
            unit = delay_match.group(3)  # e.g., "с"
            remaining_text = delay_match.group(4).strip()  # The text after the delay part

            if unit == 'с' or unit == 'c':  # seconds
                delay_seconds = duration_value
            elif unit == 'м' or unit == 'm':  # minutes
                delay_seconds = duration_value * 60

            text_to_repeat = remaining_text

        if delay_seconds:
            await asyncio.sleep(delay_seconds)

        if msg.reply_to_message:
            await msg.reply_to_message.reply(text_to_repeat.upper())
        else:
            await msg.answer(text_to_repeat.upper())