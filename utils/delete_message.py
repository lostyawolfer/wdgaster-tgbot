from aiogram.methods import SetMessageReaction
from aiogram.types import ReactionTypeEmoji
from utils import permissions
import asyncio
import datetime

async def delete_message(msg, bot, is_admin, is_decorative_admin):
    message_text = msg.text if msg.text else " "
    message_has_to_be_deleted = False
    if not msg.reply_to_message and not msg.is_automatic_forward:
        # if the message is not a reply and the message is not a channel message
        message_has_to_be_deleted = True

    # if the message is a reply to the bot's message
    elif msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id:
        await msg.delete()

    # set a reaction if message was something to be deleted but was not because admin
    if message_has_to_be_deleted and is_admin:
        print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username})\'s message was something to be deleted, but they are admin.\nThey said:\n{message_text}\n')
        await bot(SetMessageReaction(chat_id=msg.chat.id, message_id=msg.message_id,
                                     reaction=[ReactionTypeEmoji(emoji="❤️")]))

    if is_admin:
        message_has_to_be_deleted = False



    if message_has_to_be_deleted:
        if not is_decorative_admin:
            await bot.restrict_chat_member(
                chat_id=msg.chat.id,
                user_id=msg.from_user.id,
                permissions=permissions.mute_permissions,
                until_date=int(datetime.datetime.now().timestamp()) + 31
            )  # mutes the member for 30 seconds (telegram's lowest time for muting)

        # the message to be shown as explanation to what happened
        user_link = (f'<a href="tg://user?id={msg.from_user.id}">'
                     f'{msg.from_user.full_name.replace("&", "&amp;")
                     .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>')
        sent_message = await msg.reply(
            f'<b><u>\"{user_link}\". ЗДЕСЬ - НЕ ЧАТ.</u></b>\n'
            f"ЗДЕСЬ - ВСЕГО ЛИШЬ СПОСОБ ОСТАВЛЯТЬ КОММЕНТАРИИ\n"
            f"ПОД КАНАЛОМ.\n"
            f'НЕ ОТПРАВЛЯЙ ЗДЕСЬ СООБЩЕНИЯ, НЕ ЯВЛЯЮЩИЕСЯ ЧАСТЬЮ КОММЕНТАРИЕВ.\n'
            f'ОНИ ЛЕТЯТ В ПУСТОТУ, КО МНЕ.\n\n'
            f"ЕСЛИ ТЕБЯ ИНТЕРЕСУЕТ СОХРАНИТЬ СВОЁ СООБЩЕНИЕ,\n"
            f"ДЕРЖИ.\n"
            f"НО БУДЬ БЫСТР — ОНО ИСЧЕЗНЕТ ЧЕРЕЗ 30 СЕКУНД.\n"
            f'<blockquote>{message_text}</blockquote>\n\n'
            f"ТВОЙ ГОЛОС НЕ МОЖЕТ ПРОИЗНОСИТЬ СЛОВА.\n"
            f"НО НЕ ПУГАЙСЯ.\n"
            f"ЧЕРЕЗ 30 СЕКУНД ЭТО ОГРАНИЧЕНИЕ БУДЕТ СНЯТО.\n\n"
            f'<b>ДЛЯ ЧАТА, ПРОШУ ТЕБЯ РАССМОТРЕТЬ ИСПОЛЬЗОВАНИЕ @utdrchat.</b>', parse_mode='HTML')
        await msg.delete()

        print(
            f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username})\'s message was deleted.\nThey said:\n{message_text}\n')

        await asyncio.sleep(30)

        await sent_message.delete()

        if not is_decorative_admin:
            await bot.restrict_chat_member(
                chat_id=msg.chat.id,
                user_id=msg.from_user.id,
                permissions=permissions.unmute_permissions
            )  # automatically unmute the person as soon as said message gets deleted
