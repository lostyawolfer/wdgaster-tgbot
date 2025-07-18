from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.methods import SetMessageReaction
from aiogram.types import Message, ReactionTypeEmoji
import os
import sys
import subprocess

async def update(msg: Message, bot: Bot):
    await bot(SetMessageReaction(chat_id=msg.chat.id, message_id=msg.message_id,
                                 reaction=[ReactionTypeEmoji(emoji="👾")]))
    await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.UPLOAD_DOCUMENT)
    print(f"Admin {msg.from_user.full_name} triggered !update.")

    try:
        # 1. Pull latest changes from Git
        pull_result = subprocess.run(
            ['git', 'pull'],
            capture_output=True,
            text=True,
            check=True # Raise an exception if git pull fails
        )
        git_output = pull_result.stdout + pull_result.stderr
        print(f"Git Pull Output:\n{git_output}")

        # 2. Reinstall dependencies (important if requirements.txt changed)
        # Find the active Python executable
        python_executable = sys.executable
        pip_executable = os.path.join(os.path.dirname(python_executable), 'pip')

        await bot(SetMessageReaction(chat_id=msg.chat.id, message_id=msg.message_id,
                                     reaction=[ReactionTypeEmoji(emoji="⚡️")]))
        await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.CHOOSE_STICKER)
        install_result = subprocess.run(
            [pip_executable, 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True,
            check=True
        )
        pip_output = install_result.stdout + install_result.stderr
        print(f"Pip Install Output:\n{pip_output}")

        await bot(SetMessageReaction(chat_id=msg.chat.id, message_id=msg.message_id,
                                     reaction=[ReactionTypeEmoji(emoji="💯")]))
        await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.FIND_LOCATION)

        # 3. Restart the bot process
        # This is tricky: we want the current script to exit, and a new one to start.
        # We use os.execlp to replace the current process with a new one.
        # sys.argv[0] is the current script name (e.g., 'main.py')
        # sys.argv contains the arguments used to start the current script.
        # Example: python main.py -> sys.executable is 'python', sys.argv[0] is 'main.py'
        # The *args for os.execlp are: (program, arg0, arg1, ...)
        # So, program is sys.executable ('python'), arg0 is sys.executable ('python'), arg1 is sys.argv[0] ('main.py')
        print("Restarting bot...")
        os.execlp(sys.executable, sys.executable, *sys.argv)

    except subprocess.CalledProcessError as e:
        error_message = f"Ошибка при обновлении/установке: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        print(error_message)
        await msg.reply(f"ПРОИЗОШЛА ОШИБКА ПРИ ЗАГРУЗКЕ ОБНОВЛЕНИЙ:\n<blockquote expandable>{error_message[:1000]}...</blockquote>") # Truncate for Telegram
    except Exception as e:
        error_message = f"Непредвиденная ошибка при обновлении: {e}"
        print(error_message)
        await msg.reply(f"НЕПРЕДВИДЕННАЯ ОШИБКА:\n<blockquote expandable>{error_message[:1000]}...</blockquote>")