import asyncio
import logging
import os
import subprocess

async def ffmpeg_extract_audio(video_path: str, audio_path: str, metadata: dict) -> bool:
    """Конвертирует аудио в MP3 и встраивает метаданные."""
    try:
        command = [
            'ffmpeg', '-i', video_path,
            '-vn',  # Отключить видео
            '-acodec', 'libmp3lame',  # Указать кодек MP3
            '-q:a', '2',  # Высокое качество VBR
            '-y'  # Перезаписать файл
        ]

        # Добавляем метаданные, если они есть
        if metadata.get("title"):
            command.extend(['-metadata', f'title={metadata["title"]}'])
        if metadata.get("artist"):
            command.extend(['-metadata', f'artist={metadata["artist"]}'])

        command.append(audio_path)

        logging.info(f"Running FFmpeg command: {' '.join(command)}")
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, stderr = await process.communicate()

        if process.returncode != 0:
            logging.error(f"FFmpeg failed. Stderr: {stderr.decode(errors='ignore')}")
            return False

        return os.path.exists(audio_path) and os.path.getsize(audio_path) > 0

    except FileNotFoundError:
        logging.error("FFmpeg command not found. Make sure FFmpeg is installed and in your system's PATH.")
        return False
    except Exception:
        logging.exception("An exception occurred during FFmpeg audio extraction.")
        return False