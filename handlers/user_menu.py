import asyncio
import datetime
from aiogram import Router, F, Bot
from aiogram.enums import ChatType
from aiogram.methods import SetMessageReaction
from aiogram.types import Message
from aiogram.types.reaction_type_emoji import ReactionTypeEmoji
from data import permissions

router = Router()

def is_substring_in_string(substrings: list, main_str: str) -> bool:
    for s in substrings:
        if s in main_str:
            return True
    return False

# ORPHAN MESSAGES DELETER [comment section cleaner]
@router.message(F.chat.type.in_({ChatType.SUPERGROUP}))
async def delete_messages(msg: Message, bot: Bot):
    chat_member = await bot.get_chat_member(chat_id=msg.chat.id, user_id=msg.from_user.id)
    # get the message author object to see if they, maybe, have permissions to send the message

    is_admin = False
    is_decorative_admin = False

    if chat_member.user.id == 653632008 and "///" in msg.text:
        is_admin = True

    elif chat_member.status in ['administrator', 'creator']:
        if chat_member.status == 'administrator':
            is_admin = (
                    chat_member.can_delete_messages or
                    chat_member.can_restrict_members or
                    chat_member.can_promote_members or
                    chat_member.can_change_info or
                    chat_member.can_pin_messages
            )
            if not is_admin:
                is_decorative_admin = True
        else:
            is_admin = True

    if is_admin:
        is_decorative_admin = True

    message_has_to_be_deleted = False
    if not msg.reply_to_message and not msg.is_automatic_forward:
        # if the message is not a reply, the message is not a channel message
        message_has_to_be_deleted = True

    # if the message is a reply to the bot's message
    elif msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id:
        await msg.delete()

    # set a reaction if message was something to be deleted but was not because admin
    if message_has_to_be_deleted and is_admin:
        print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username})\'s message was something to be deleted, but they are admin.\nThey said:\n{msg.text}\n')
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
            f'<b><u>{user_link}. ЗДЕСЬ - НЕ ЧАТ.</u></b>\n'
            f"ЗДЕСЬ - ВСЕГО ЛИШЬ СПОСОБ ОСТАВЛЯТЬ КОММЕНТАРИИ\n"
            f"ПОД КАНАЛОМ.\n"
            f'НЕ ОТПРАВЛЯЙ ЗДЕСЬ СООБЩЕНИЯ, НЕ ЯВЛЯЮЩИЕСЯ ЧАСТЬЮ КОММЕНТАРИЕВ.\n'
            f'ОНИ ЛЕТЯТ В ПУСТОТУ, КО МНЕ.\n\n'
            f"ЕСЛИ ТЕБЯ ИНТЕРЕСУЕТ СОХРАНИТЬ СВОЁ СООБЩЕНИЕ,\n"
            f"ДЕРЖИ.\n"
            f"НО БУДЬ БЫСТР — ОНО ИСЧЕЗНЕТ ЧЕРЕЗ 30 СЕКУНД.\n"
            f'<blockquote>{msg.text}</blockquote>\n\n'
            f"ТВОЙ ГОЛОС НЕ МОЖЕТ ПРОИЗНОСИТЬ СЛОВА.\n"
            f"НО НЕ ПУГАЙСЯ.\n"
            f"ЧЕРЕЗ 30 СЕКУНД ЭТО ОГРАНИЧЕНИЕ БУДЕТ СНЯТО.\n\n"
            f'<b>ДЛЯ ЧАТА, ПРОШУ ТЕБЯ РАССМОТРЕТЬ ИСПОЛЬЗОВАНИЕ @utdrchat.</b>', parse_mode='HTML')
        await msg.delete()

        print(
            f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username})\'s message was deleted.\nThey said:\n{msg.text}\n')

        await asyncio.sleep(30)

        await sent_message.delete()

        if not is_decorative_admin:
            await bot.restrict_chat_member(
                chat_id=msg.chat.id,
                user_id=msg.from_user.id,
                permissions=permissions.unmute_permissions
            )  # automatically unmute the person as soon as said message gets deleted


    # funny replies
    very_interesting_triggers = [
        "ааа женщина",
        "многа букав",
        "много букв",
        "много букав",
        "лень читать"
    ]
    if is_substring_in_string(very_interesting_triggers, msg.text.lower()):
        await msg.reply("ОЧЕНЬ\nИНТЕРЕСНО.")
        print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered VERY INTERESTING; they said\n{msg.text}\n')
    # elif msg.text == "здравствуйте это главный фанат крюзи\nя вас одобряю\nдо свидания":
    #     await msg.reply("ОЧЕНЬ\nИНТЕРЕСНО.")
    #     print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered KRUSIE; they said\n{msg.text}\n')

    # moderator_bot_id = 5226378684 # iris deep purple
    # if msg.from_user.id == moderator_bot_id:
    if is_admin:
        if msg.text.startswith("варн"):
            await msg.reply("КАК ЖАЛЬ ЧТО\nУЧАСТНИКИ ЭКСПЕРИМЕНТА\nРУШАТ ЕГО ПОРЯДОК.")
            print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered WARN; they said\n{msg.text}\n')
        elif msg.text.startswith("снять варн"):
            await msg.reply("ОЧЕНЬ ИНТЕРЕСНОЕ ПОВЕДЕНИЕ.")
            print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered UNWARN; they said\n{msg.text}\n')
        elif msg.text.startswith("мут"):
            await msg.reply("КАЖЕТСЯ, КТО-ТО СОРВАЛ ГОЛОС.\nВОЗВРАЩАЙСЯ, КОГДА БУДЕШЬ,\nМММ... ПОСПОКОЙНЕЙ.")
            print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered MUTE; they said\n{msg.text}\n')
        elif msg.text.startswith("бан"):
            await msg.reply("НЕКОТОРЫМ\nК СОЖАЛЕНИЮ\nЛУЧШЕ НЕ УЧАВСТВОВАТЬ В ЭКСПЕРИМЕНТЕ.")
            print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered BAN; they said\n{msg.text}\n')

    if msg.is_automatic_forward:
        if "загор" in msg.text.lower():
            await msg.reply("КАКАЯ ИНТЕРЕСНАЯ\nТЕОРИЯ.\nЗАГОР.\nМНЕ С НИМ\nЕЩЁ ПРЕДСТОИТ\nПОВИДАТЬСЯ.")
            print(f'\ntg://user?id={msg.from_user.id} (@{msg.from_user.username}) triggered ZAGOR; they said\n{msg.text}\n')
