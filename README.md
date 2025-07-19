[Читати на українській](README.uk.md)

[Читать на русском](README.ru.md)

---

# W. D. Gaster Telegram Bot

[![Telegram Bot](https://img.shields.io/badge/Telegram-@utdrgasterbot-blue.svg?style=flat-square&logo=telegram)](https://t.me/utdrgasterbot)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![aiogram](https://img.shields.io/badge/aiogram-v3-green.svg)

A multi-purpose moderation and utility Telegram bot designed for *Deltarune* fandom communities, themed after the enigmatic character W. D. Gaster. The bot provides a mix of moderation tools, fun commands, and unique utilities to enhance the chat experience.

The bot's personality and responses are crafted to mimic W. D. Gaster, providing an immersive role-playing element. Its primary language for commands and responses is Ukrainian/Russian.

### ✨ Showcase

![About](/images/readme/update.png)
![About](/images/readme/commands.png)
![Image](/images/readme/image.png)

## ✨ Features

This bot comes with a variety of features designed for community engagement and moderation:

* **🗣️ Pronoun Management**: Allows users to set, update, remove, and check their own or other users' pronouns, fostering an inclusive environment.
* **💬 Comment Section Moderation**: Automatically deletes messages that are not replies in chats linked to a channel (i.e., comment sections). This keeps the discussion threads clean. Users are temporarily muted for 30 seconds as a soft penalty.
* **▶️ Video Downloader**: Powered by `yt-dlp`, the bot automatically detects links from YouTube and many other video sites. It downloads the video (up to 20MB) and uploads it directly to the chat as a file, complete with title and description.
* **🤖 Trigger-Based Responses**: Reacts to various fandom-specific keywords and phrases with pre-programmed, in-character responses.
* **🚀 Remote Live Update**: A special command for the bot owner to pull the latest changes from the Git repository, install/update dependencies, and restart the bot on the fly.
* **📢 Startup Announcements**: Notifies a designated chat upon startup, displaying the current version and a detailed changelog.
* **👮 Admin Privileges**: Admins are exempt from certain restrictions, like message deletion in comment sections.

## 🚀 Getting Started

To run your own instance of the W. D. Gaster bot, follow these steps.

### Prerequisites

* [Python 3.10](https://www.python.org/downloads/) or newer
* [Git](https://git-scm.com/downloads)

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/lostyawolfer/wdgaster-tgbot.git
    cd wdgaster-tgbot
    ```

2.  **Create a virtual environment (recommended):**
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**
    The project's dependencies are listed in `requirements.txt`.
    ```sh
    pip install -r requirements.txt
    ```

4.  **Configure your environment variables:**
    Create a file named `.env` in the root directory of the project. This file will hold your bot's token and other settings.

    Add the following lines to your `.env` file:
    ```env
    TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    MAIN_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
    ```
    * `TOKEN`: Your unique token from Telegram's [@BotFather](https://t.me/BotFather).
    * `MAIN_CHAT_ID`: The ID of the chat where the bot should send startup announcements and updates.

5.  **Run the bot:**
    Execute the `main.py` script to start the bot.
    ```sh
    python main.py
    ```
    The bot will initialize its database tables if they don't exist and start polling for messages.

## 🛠 Usage

The bot responds to a variety of commands and triggers. To see the full list, use the `гастер команды` command in chat.

### Key Commands

#### **General**
* `бот` / `гастер` / `тест` (and other aliases) — Checks if the bot is online.
* `гастер спойлеры` — Shows spoilers :)
* `гастер создатель` / `гастер кто создал` — Shows the creator of the bot.
* `гастер исходный код` / `гастер сурс` (and other aliases) — Provides a link to the bot's source code.
* `гастер оне/ено` / `гастер оне` — Displays an informational image about the neopronoun "оне/ено".
* `кто ты` / `ты кто` (in reply to the bot) — The bot introduces itself.
* `!снимаю полномочия` — A joke command.
* `дуэль @utdrgasterbot` — A joke command for dueling the bot.

#### **Pronouns**
* `+мест [pronouns]` / `+местоимения [pronouns]` — Set or update your personal pronouns (up to 30 characters).
* `-мест` / `-местоимения` — Remove your pronouns from the database.
* `мои мест` / `мои местоимения` — Show your own saved pronouns.
* `мест` / `местоимения` (as a reply) — Show the pronouns of the user you replied to.
* `мест @[username]` — Show a user's pronouns by their username.

#### **For Admins & Owner**
* `варн`, `мут`, `бан`, `снять варн` — Moderation commands. (WIP)
* `г!обновись` — Updates the bot to the latest version from Git.
* `г!повтори [text]` — Makes the bot repeat the given text.
* `г!все мест` — Shows all pronouns from the database.

### Triggers
The bot responds to certain phrases if they are part of a message.
* `ааа женщина`
* `многа букав` / `много букв` / `лень читать`
* `driving in my car🚗, right after a beer🍺`
* `сел за руль🚗, я после пивка🍺`
* `я не понимаю почему многие жалеют крис`
* `человек яйца` / `человек-яйца`
* `дессриэль` / `дессриэли`
* `крюзи` / `крузи`
* `нуберт`
* `убежище`
* `др рп`
* `лостя фембой`
* `уникальные листья` (and its grammatical cases)
* `ангел` / `рай ангела` / `небеса ангела`
* `загор` (in channel posts)