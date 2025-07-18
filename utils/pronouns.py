from aiogram import Bot
from aiogram.enums import MessageEntityType
from db.db import Pronouns

db_pronouns = Pronouns()

async def do_pronouns(msg, bot: Bot):
    user_link = (f'\"<a href="tg://user?id={msg.from_user.id}">'
                 f'{msg.from_user.full_name.replace("&", "&amp;")
                 .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>\"')
    message_text = msg.text if msg.text else " "
    if message_text.lower().startswith("+местоимения ") or message_text.lower().startswith("+мест "):
        if message_text.lower().startswith("+местоимения "):
            new_pronouns = message_text.lower()[len("+местоимения "):].strip()
        else:
            new_pronouns = message_text.lower()[len("+мест "):].strip()

        if len(new_pronouns) <= 30:
            db_pronouns.add_pronouns(msg.from_user.id, msg.from_user.username, new_pronouns)
            await msg.reply(
                f"{user_link}.\n{new_pronouns.upper()}.\n\nЗАМЕЧАТЕЛЬНО.\n\nДЕЙСТВИТЕЛЬНО\nЗАМЕЧАТЕЛЬНО.\n\nСПАСИБО\nЗА ТВОЁ ВРЕМЯ.",
                parse_mode="HTML")
        else:
            await msg.reply(
                f"{user_link}.\nМЕСТОИМЕНИЯ\nНЕ ДОЛЖНЫ ЗАНИМАТЬ БОЛЬШЕ\nЧЕМ 30 СИМВОЛОВ.",
                parse_mode="HTML")

    elif message_text.lower().startswith("-местоимения") or message_text.lower().startswith("-мест"):
        await msg.reply(
            f"ФАЙЛ\nУДАЛЁН.",
            parse_mode="HTML")
        db_pronouns.rm_pronouns(msg.from_user.id)

    elif message_text.lower() == "мои местоимения" or message_text.lower() == "мои мест":
        pronouns = db_pronouns.get_pronouns(msg.from_user.id)
        if pronouns is not None:
            await msg.reply(f"МЕСТОИМЕНИЯ {user_link}:\n{pronouns.upper()}.", parse_mode='HTML')
        else:
            await msg.reply(f"ПОЛЬЗОВАТЕЛЬ {user_link}\nНЕ ВЫСТАВИЛ СВОИХ\nМЕСТОИМЕНИЙ.\n\n[[ЭТО МОЖНО СДЕЛАТЬ КОМАНДОЙ +МЕСТ.]]", parse_mode='HTML')

    elif ((message_text.lower() == "местоимения" or
         message_text.lower() == "мест" or
         message_text.lower() == "твои местоимения" or
         message_text.lower() == "твои мест" or
         message_text.lower() == "кто ты" or
         message_text.lower() == "ты кто")
            and msg.reply_to_message
            and not msg.reply_to_message.from_user.id == bot.id):

        pronouns = db_pronouns.get_pronouns(msg.reply_to_message.from_user.id)
        user_reply_link = (f'\"<a href="tg://user?id={msg.reply_to_message.from_user.id}">'
                           f'{msg.reply_to_message.from_user.full_name.replace("&", "&amp;")
                           .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>\"')
        if pronouns is not None:
            await msg.reply(f"МЕСТОИМЕНИЯ {user_reply_link}:\n{pronouns.upper()}.", parse_mode='HTML')
        else:
            await msg.reply(f"ПОЛЬЗОВАТЕЛЬ {user_reply_link}\nНЕ ВЫСТАВИЛ СВОИХ\nМЕСТОИМЕНИЙ.\n\n[[ЭТО МОЖНО СДЕЛАТЬ КОМАНДОЙ +МЕСТ.]]", parse_mode='HTML')

    elif (message_text.lower().startswith("местоимения @") or
        message_text.lower().startswith("мест @")):
            username = message_text.split("@", 1)[1].strip()
            try:
                user = await bot.get_chat_member(msg.chat.id, db_pronouns.get_user_id_by_username(username))
                user = user.user
                pronouns = db_pronouns.get_pronouns_by_username(username)
                user_reply_link = (f'\"<a href="tg://user?id={user}">'
                                   f'{user.full_name.replace("&", "&amp;")
                                   .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>\"')
                if pronouns is not None:
                    await msg.reply(f"МЕСТОИМЕНИЯ {user_reply_link}:\n{pronouns.upper()}.", parse_mode='HTML')
                else:
                    await msg.reply(
                        f"ПОЛЬЗОВАТЕЛЬ {user_reply_link}\nНЕ ВЫСТАВИЛ СВОИХ\nМЕСТОИМЕНИЙ.\n\n[[ЭТО МОЖНО СДЕЛАТЬ КОМАНДОЙ +МЕСТ.]]",
                        parse_mode='HTML')
            except Exception as e:
                print(e)
                await msg.reply(
                    f"ПОЛЬЗОВАТЕЛЬ @{username.upper()}\nНЕ ВЫСТАВИЛ СВОИХ\nМЕСТОИМЕНИЙ.\n\n[[ЭТО МОЖНО СДЕЛАТЬ КОМАНДОЙ +МЕСТ.]]",
                        parse_mode='HTML')

    elif message_text == "!все мест" and msg.from_user.id == 653632008:
        data = db_pronouns.get_all_data()
        result = '''ДЛЯ СПРАВКИ ОКРУЖАЮЩИМ,\nЭТА КОМАНДА РАБОТАЕТ ТОЛЬКО ДЛЯ @LOSTYAWOLFER.

СПИСОК ВСЕХ МЕСТОИМЕНИЙ В БАЗЕ ДАННЫХ:
<blockquote expandable>'''

        if data:
            for user_id, username, pronouns_text in data:
                try:
                    member_info = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
                    display_name = member_info.user.full_name
                    display_name_escaped = display_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    result += f'<a href="tg://user?id={user_id}">{display_name_escaped}</a>   ==   {pronouns_text}\n'
                except Exception as e:
                    # Fallback to just user ID if fetching info fails
                    print(f"Could not get member info for user_id {user_id}: {e}")
                    result += f'ID {user_id} (@{username})   ==   {pronouns_text}\n'
            result += '</blockquote>'
        else:
            result += '<i>В БАЗЕ ДАННЫХ ПУСТО.</i></blockquote>'

        await msg.reply(result, parse_mode='HTML')