import os

import utils.message_triggers
from aiogram import Router, F, Bot
from aiogram.enums import ChatType
from aiogram.types import Message, Chat, ChatFullInfo, FSInputFile
from db.db import Pronouns
from utils.check_admin import check_admin
from utils.delete_message import delete_message
from utils.message_triggers import contains_triggers, admin_action_triggers, channel_post_triggers, matches_triggers

router = Router()
db_pronouns = Pronouns()


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
    user_link = (f'\"<a href="tg://user?id={msg.from_user.id}">'
                 f'{msg.from_user.full_name.replace("&", "&amp;")
                 .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>\"')
    message_text = msg.text if msg.text else " "

    is_admin = check_admin(chat_member, msg)
    is_decorative_admin = check_admin(chat_member, msg, decorative=True)

    if is_this_a_comment_section(await bot.get_chat(msg.chat.id)):
        await delete_message(msg, bot, is_admin, is_decorative_admin)

    # add administrating logic
    print(msg.text)
    # funny reply triggers
    trigger = trigger_message(contains_triggers, message_text.lower(), check_method=0, channel_message=msg.is_automatic_forward)
    if trigger is not None:
        await msg.reply(trigger)
        print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered {trigger}; they said\n{message_text}\n')

    trigger = trigger_message(matches_triggers, message_text.lower(), check_method=3, channel_message=msg.is_automatic_forward)
    if trigger is not None:
        await msg.reply(trigger)
        print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered {trigger}; they said\n{message_text}\n')



    trigger = trigger_message(admin_action_triggers, message_text.lower(), check_method=1, is_admin=is_admin)
    if trigger is not None:
        await msg.reply(trigger)
        print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered {trigger}; they said\n{message_text}\n')

    trigger = trigger_message(channel_post_triggers, message_text.lower(), check_method=2, channel_message=msg.is_automatic_forward)
    if trigger is not None:
        await msg.reply(trigger)
        print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered {trigger}; they said\n{message_text}\n')

    # pronouns command
    if message_text.lower().startswith("+местоимения ") or message_text.lower().startswith("+мест "):
        if message_text.lower().startswith("+местоимения "):
            new_pronouns = message_text.lower()[len("+местоимения "):].strip()
        else:
            new_pronouns = message_text.lower()[len("+мест "):].strip()

        if len(new_pronouns) <= 30:
            db_pronouns.add_pronouns(msg.from_user.id, new_pronouns)
            await msg.reply(f"{user_link}.\n{new_pronouns.upper()}.\n\nЗАМЕЧАТЕЛЬНО.\n\nДЕЙСТВИТЕЛЬНО\nЗАМЕЧАТЕЛЬНО.\n\nСПАСИБО\nЗА ТВОЁ ВРЕМЯ.", parse_mode="HTML")
        else:
            await msg.reply(
                f"{user_link}.\nМЕСТОИМЕНИЯ\nНЕ ДОЛЖНЫ ЗАНИМАТЬ БОЛЬШЕ\nЧЕМ 30 СИМВОЛОВ.",
                parse_mode="HTML")

    if message_text.lower().startswith("-местоимения") or message_text.lower().startswith("-мест"):
        await msg.reply(
            f"ФАЙЛ\nУДАЛЁН.",
            parse_mode="HTML")
        db_pronouns.rm_pronouns(msg.from_user.id)

    if message_text.lower() == "мои местоимения" or message_text.lower() == "мои мест":
        pronouns = db_pronouns.get_pronouns(msg.from_user.id)
        if pronouns is not None:
            await msg.reply(f"МЕСТОИМЕНИЯ {user_link}:\n{pronouns.upper()}.", parse_mode='HTML')
        else:
            await msg.reply(f"ПОЛЬЗОВАТЕЛЬ {user_link}\nНЕ ВЫСТАВИЛ СВОИХ\nМЕСТОИМЕНИЙ.", parse_mode='HTML')

    if (message_text.lower() == "местоимения" or message_text.lower() == "мест" or message_text.lower() == "кто ты" or message_text.lower() == "ты кто") and msg.reply_to_message:
        pronouns = db_pronouns.get_pronouns(msg.reply_to_message.from_user.id)
        user_reply_link = (f'\"<a href="tg://user?id={msg.reply_to_message.from_user.id}">'
                     f'{msg.reply_to_message.from_user.full_name.replace("&", "&amp;")
                     .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>\"')
        if pronouns is not None:
            await msg.reply(f"МЕСТОИМЕНИЯ {user_reply_link}:\n{pronouns.upper()}.", parse_mode='HTML')
        else:
            await msg.reply(f"ПОЛЬЗОВАТЕЛЬ {user_reply_link}\nНЕ ВЫСТАВИЛ СВОИХ\nМЕСТОИМЕНИЙ.", parse_mode='HTML')

    if message_text.lower() == "гастер оне/ено" or message_text.lower() == "гастер оне" or message_text.lower() == "гастер неомест":
        await msg.reply_photo(FSInputFile(os.path.join('images', 'neopronouns.png')), caption="ОНЕ/ЕНО - НЕОМЕСТОИМЕНИЕ АВТОРСТВА @LOSTYAWOLFER,\nПРИЗВАННОЕ БЫТЬ ПОЛНОЙ АЛЬТЕРНАТИВОЙ\nАНГЛИЙСКОГО \"THEY/THEM\"\nВ ЕДИНСТВЕННОМ ЧИСЛЕ.\n\nДЛЯ НЕИЗВЕСТНЫХ ЛЮДЕЙ,\nДЛЯ ЛЮДЕЙ НЕБИНАРНЫХ...\nВЫБОР ЗА ТОБОЙ.\n\nЭТОТ ЕГО ЭКСПЕРИМЕНТ\nМНЕ КАЖЕТСЯ\nОЧЕНЬ\nОЧЕНЬ\nИНТЕРЕСНЫМ.")

    if message_text.lower() == "лостя фембой":
        await msg.reply_photo(FSInputFile(os.path.join('images', 'lostya_femboy.jpg')))

    if message_text.lower() == "спойлеры" or message_text.lower() == "спойлер":
        await msg.reply(f"НА ДАННЫЙ МОМЕНТ,\nСПОЙЛЕРНЫЙ РЕЖИМ ОТКЛЮЧЕН.\n\nПОСЛЕДНИЙ РАЗ СПОЙЛЕРНЫЙ РЕЖИМ\nБЫЛ АКТИВЕН\n<b>13 ИЮЛЯ.</b>", parse_mode='HTML')

    if message_text.lower() == "гастер команды":
        await msg.reply(f'МОИ КОМАНДЫ.\n\n\n'
                        f'БОТ, ГАСТЕР ИЛИ ТЕСТ - Я ОТЗОВУСЬ. ПРОВЕРКА ЖИВ ЛИ БОТ.\n\n'
                        f'ГАСТЕР КОМАНДЫ - ПОКАЗАТЬ ЭТОТ СПИСОК.\n\n'
                        f'МЕСТОИМЕНИЯ ИЛИ МЕСТ ИЛИ КТО ТЫ ИЛИ ТЫ КТО - В ОТВЕТ НА ЧЬЁ-ЛИБО СООБЩЕНИЕ: ПОКАЗАТЬ МЕСТОИМЕНИЯ.\n\n'
                        f'+МЕСТОИМЕНИЯ ИЛИ +МЕСТ - ВЫСТАВИТЬ МЕСТОИМЕНИЯ СЕБЕ.\n\n'
                        f'-МЕСТОИМЕНИЯ ИЛИ -МЕСТ - УДАЛИТЬ СВОИ МЕСТОИМЕНИЯ.\n\n'
                        f'МОИ МЕСТОИМЕНИЯ ИЛИ МОИ МЕСТ - ПОСМОТРЕТЬ СВОИ МЕСТОИМЕНИЯ.\n\n'
                        f'ГАСТЕР ОНЕ/ЕНО, ГАСТЕР ОНЕ, ГАСТЕР НЕОМЕСТ - ОТПРАВИТЬ ТАБЛИЦУ С ИНФОРМАЦИЕЙ ПРО НЕОМЕСТОИМЕНИЕ \"ОНЕ/ЕНО\".\n\n'
                        f'СПОЙЛЕРЫ - ПРОВЕРИТЬ НАЛИЧИЕ СПОЙЛЕРНОГО РЕЖИМА НА ДАННЫЙ МОМЕНТ.')
