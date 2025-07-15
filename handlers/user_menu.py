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
from utils.message_triggers import contains_triggers, admin_action_triggers, channel_post_triggers, matches_triggers
from utils.pronouns import do_pronouns
from utils.youtube_downloader import download_youtube_video, delete_temp_file

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
    # user_link = (f'\"<a href="tg://user?id={msg.from_user.id}">'
    #              f'{msg.from_user.full_name.replace("&", "&amp;")
    #              .replace("<", "&lt;").replace(">", "&gt;").upper()}</a>\"')
    message_text = msg.text if msg.text else " "

    is_admin = check_admin(chat_member, msg)
    is_decorative_admin = check_admin(chat_member, msg, decorative=True)

    if is_this_a_comment_section(await bot.get_chat(msg.chat.id)):
        await delete_message(msg, bot, is_admin, is_decorative_admin)

    youtube_url_match = re.search(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/[^\s]+', message_text)
    if youtube_url_match:
        video_url = youtube_url_match.group(0)
        print(f"Detected YouTube link: {video_url} from {msg.from_user.full_name}")

        await bot(SetMessageReaction(chat_id=msg.chat.id, message_id=msg.message_id,
                                     reaction=[ReactionTypeEmoji(emoji="👾")]))
        await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.CHOOSE_STICKER)

        try:
            video_info = await download_youtube_video(video_url)

            if video_info and video_info['filepath']:
                video_file = FSInputFile(video_info['filepath'])


                # Prepare caption: Include title and description
                # Keep total caption length in mind (max 1024 characters for video captions)
                caption_parts = []
                caption_parts.append(f"<b><u>{video_info['title']}</u></b>")  # Make title bold

                # Add description if available and not empty
                if video_info['description']:
                    description_to_add = video_info['description']
                    # Important: Escape HTML characters in the description itself
                    # before wrapping it in blockquote tags, otherwise description content
                    # like '<script>' or '&' will break the parsing.
                    description_to_add_escaped = description_to_add.replace("&", "&amp;").replace("<", "&lt;").replace(
                        ">", "&gt;")

                    # Basic truncation example (after escaping)
                    if len(description_to_add_escaped) > 1024:
                        description_to_add_escaped = description_to_add_escaped[:1021] + "..."

                    # Wrap the escaped description in blockquote tags
                    caption_parts.append(f"<blockquote expandable>{description_to_add_escaped}</blockquote>")

                final_caption = "\n".join(caption_parts)

                # Ensure the entire caption doesn't exceed 1024 characters
                if len(final_caption) > 1024:
                    final_caption = final_caption[:1011] + "...</blockquote>"  # Truncate with ellipsis

                await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.UPLOAD_VIDEO)
                sent_video = await msg.reply_video(
                    video_file,
                    caption=final_caption,
                    parse_mode='HTML',  # Use HTML parse mode for bold tags and potentially timecodes
                    duration=video_info.get('duration'),
                    # width=720, # Optional: You can set these based on your needs or extracted info
                    # height=480
                    #thumbnail=thumbnail_file
                )
                print(f"Successfully sent video for {video_url}. Message ID: {sent_video.message_id}")

                asyncio.create_task(delete_temp_file(video_info['filepath']))
                return

            else:
                await msg.reply(f"❌ ВНУТРЕННЯЯ\nОШИБКА\nСКАЧИВАНИЯ.\n\nВОЗМОЖНО,\nВИДЕО\nСЛИШКОМ БОЛЬШОЕ.")
                print(f"Failed to convert video for {video_url}")

        except Exception as e:
            await msg.reply(f"❌ ВНУТРЕННЯЯ\nОШИБКА\nСКАЧИВАНИЯ.\n\nВОЗМОЖНО,\nВИДЕО\nСЛИШКОМ БОЛЬШОЕ.\n\nОШИБКА,\nПРЕДОСТАВЛЕННАЯ ПРОГРАММОЙ:\n{e}")
        return



    await do_pronouns(msg)



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

    if message_text.lower() == "гастер оне/ено" or message_text.lower() == "гастер оне" or message_text.lower() == "гастер неомест":
        await msg.reply_photo(FSInputFile(os.path.join('images', 'neopronouns.png')), caption="ОНЕ/ЕНО - НЕОМЕСТОИМЕНИЕ АВТОРСТВА @LOSTYAWOLFER,\nПРИЗВАННОЕ БЫТЬ ПОЛНОЙ АЛЬТЕРНАТИВОЙ\nАНГЛИЙСКОГО \"THEY/THEM\"\nВ ЕДИНСТВЕННОМ ЧИСЛЕ.\n\nДЛЯ НЕИЗВЕСТНЫХ ЛЮДЕЙ,\nДЛЯ ЛЮДЕЙ НЕБИНАРНЫХ...\nВЫБОР ЗА ТОБОЙ.\n\nЭТОТ ЕГО ЭКСПЕРИМЕНТ\nМНЕ КАЖЕТСЯ\nОЧЕНЬ\nОЧЕНЬ\nИНТЕРЕСНЫМ.")

    if message_text.lower() == "лостя фембой":
        await msg.reply_photo(FSInputFile(os.path.join('images', 'lostya_femboy.jpg')))

    if message_text.lower() == "спойлеры" or message_text.lower() == "спойлер":
        await msg.reply(f"НА ДАННЫЙ МОМЕНТ,\nСПОЙЛЕРНЫЙ РЕЖИМ ОТКЛЮЧЕН.\n\nПОСЛЕДНИЙ РАЗ СПОЙЛЕРНЫЙ РЕЖИМ\nБЫЛ АКТИВЕН\n<b>13 ИЮЛЯ.</b>", parse_mode='HTML')

    if msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id and (message_text.lower() == "кто ты" or message_text.lower() == "ты кто"):
        await msg.reply("Я ВИНГ ГАСТЕР! КОРОЛЕВСКИЙ УЧЁНЫЙ")

    if message_text.lower() == "гастер команды":
        await msg.reply(f'<b><u>МОИ КОМАНДЫ</u></b>\n\n\n'
                        f'БОТ, ГАСТЕР ИЛИ ТЕСТ - Я ОТЗОВУСЬ. ПРОВЕРКА ЖИВ ЛИ БОТ.\n\n'
                        f'ГАСТЕР КОМАНДЫ - ПОКАЗАТЬ ЭТОТ СПИСОК.\n\n'
                        f'\n'
                        f'МЕСТОИМЕНИЯ ИЛИ МЕСТ ИЛИ КТО ТЫ ИЛИ ТЫ КТО - В ОТВЕТ НА ЧЬЁ-ЛИБО СООБЩЕНИЕ: ПОКАЗАТЬ МЕСТОИМЕНИЯ.\n\n'
                        f'+МЕСТОИМЕНИЯ ИЛИ +МЕСТ - ВЫСТАВИТЬ МЕСТОИМЕНИЯ СЕБЕ.\n\n'
                        f'-МЕСТОИМЕНИЯ ИЛИ -МЕСТ - УДАЛИТЬ СВОИ МЕСТОИМЕНИЯ.\n\n'
                        f'МОИ МЕСТОИМЕНИЯ ИЛИ МОИ МЕСТ - ПОСМОТРЕТЬ СВОИ МЕСТОИМЕНИЯ.\n\n'
                        f'\n'
                        f'ГАСТЕР ОНЕ/ЕНО, ГАСТЕР ОНЕ, ГАСТЕР НЕОМЕСТ - ОТПРАВИТЬ ТАБЛИЦУ С ИНФОРМАЦИЕЙ ПРО НЕОМЕСТОИМЕНИЕ \"ОНЕ/ЕНО\".\n\n'
                        f'\n'
                        f'СПОЙЛЕРЫ - ПРОВЕРИТЬ НАЛИЧИЕ СПОЙЛЕРНОГО РЕЖИМА НА ДАННЫЙ МОМЕНТ.\n\n'
                        f'\n'
                        f'ЛЮБАЯ ССЫЛКА НА ЮТУБ ВИДЕО - АВТОМАТИЧЕСКИ СКАЧАТЬ ЕГО И ОТПРАВИТЬ КАК ФАЙЛ.\n\n'
                        f'<blockquote expandable><b><u>[[В ПЛАНАХ]]</u></b>'
                        f'\n'
                        f'+СПОЙЛЕРЫ - АДМИНСКАЯ КОМАНДА ДЛЯ ВКЛЮЧЕНИЯ СПОЙЛЕРНОГО РЕЖИМА.\n\n'
                        f'-СПОЙЛЕРЫ - АДМИНСКАЯ КОМАНДА ДЛЯ ВЫКЛЮЧЕНИЯ СПОЙЛЕРНОГО РЕЖИМА.\n\n'
                        f'\n'
                        f'АДМИНСКИЕ КОМАНДЫ ВАРН, БАН, МУТ, -ЧАТ, +ЧАТ\n\n'
                        f'АДМИНСКАЯ КОМАНДА /ш ЧТОБЫ ПРЕВРАТИТЬ ДРУГИЕ АДМИНСКИЕ КОМАНДЫ В ШУТКИ ИЛИ НАОБОРОТ.\n\n'
                        f'\n'
                        f'АДМИНСКИЕ КОМАНДЫ ДЛЯ АВТОМАТИЧЕСКОГО СОЗДАНИЯ И УДАЛЕНИЯ ТРИГГЕРОВ.\n\n'
                        f'\n'
                        f'ВОЗМОЖНОСТЬ ПОСМОТРЕТЬ ЧУЖИЕ МЕСТОИМЕНИЯ ПО @ ВМЕСТО ОТВЕТА НА СООБЩЕНИЕ.</blockquote>', parse_mode='HTML')
