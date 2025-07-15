from db.db import Pronouns

db_pronouns = Pronouns()

async def do_pronouns(msg):
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
            db_pronouns.add_pronouns(msg.from_user.id, new_pronouns)
            await msg.reply(
                f"{user_link}.\n{new_pronouns.upper()}.\n\nЗАМЕЧАТЕЛЬНО.\n\nДЕЙСТВИТЕЛЬНО\nЗАМЕЧАТЕЛЬНО.\n\nСПАСИБО\nЗА ТВОЁ ВРЕМЯ.",
                parse_mode="HTML")
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
            await msg.reply(f"ПОЛЬЗОВАТЕЛЬ {user_link}\nНЕ ВЫСТАВИЛ СВОИХ\nМЕСТОИМЕНИЙ.\n\n[[ЭТО МОЖНО СДЕЛАТЬ КОМАНДОЙ +МЕСТ.]]", parse_mode='HTML')

    if (
            message_text.lower() == "местоимения" or message_text.lower() == "мест" or message_text.lower() == "кто ты" or message_text.lower() == "ты кто") and msg.reply_to_message:
        pronouns = db_pronouns.get_pronouns(msg.reply_to_message.from_user.id)
        user_reply_link = (f'\"<a href="tg://user?id={msg.reply_to_message.from_user.id}">'
                           f'{msg.reply_to_message.from_user.full_name.replace("&", "&amp;")
                           .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>\"')
        if pronouns is not None:
            await msg.reply(f"МЕСТОИМЕНИЯ {user_reply_link}:\n{pronouns.upper()}.", parse_mode='HTML')
        else:
            await msg.reply(f"ПОЛЬЗОВАТЕЛЬ {user_reply_link}\nНЕ ВЫСТАВИЛ СВОИХ\nМЕСТОИМЕНИЙ.\n\n[[ЭТО МОЖНО СДЕЛАТЬ КОМАНДОЙ +МЕСТ.]]", parse_mode='HTML')
