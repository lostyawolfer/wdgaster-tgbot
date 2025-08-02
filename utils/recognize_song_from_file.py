import logging
import os
from aiogram.client.session import aiohttp


async def recognize_song_from_file(session: aiohttp.ClientSession, filepath: str) -> str:
    """Распознает трек и возвращает отформатированную строку или пустую строку."""
    if not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "rb") as audio_file:
            form_data = aiohttp.FormData()
            form_data.add_field('file', audio_file, filename=os.path.basename(filepath), content_type='audio/mpeg')
            shazam_api_url = "https://shz.aartzz.pp.ua/recognize_song/"
            async with session.post(shazam_api_url, data=form_data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    if result and result.get("track"):
                        track = result["track"]
                        title = track.get("title", "Неизвестно")
                        artist = track.get("subtitle", "Неизвестно")
                        shazam_url = track.get("share", {}).get("href", "")
                        if shazam_url:
                            return f'🎶 <a href="{shazam_url}">{artist} - {title}</a>'
                else:
                    logging.error(f"Shazam API error: {response.status} - {await response.text()}")
                    return ""
    except Exception:
        logging.exception("An error occurred during song recognition.")
    return ""