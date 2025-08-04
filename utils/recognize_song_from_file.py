import logging
import os
from aiogram.client.session import aiohttp
from urllib.parse import quote
import json


async def get_song_link(session: aiohttp.ClientSession, shazam_data: dict) -> str | None:
    """
    Tries to get a song.link URL from Shazam data using a priority list of supported identifiers.
    Falls back to the original Shazam URL if no supported identifiers are found.
    """
    track_data = shazam_data.get("track", {})
    if not track_data:
        return None

    # --- Final, Corrected Logic: Create a prioritized list of methods to try ---
    api_query_url = None

    # Each function checks for a specific, supported identifier and returns a song.link API URL if found.
    def get_spotify_url():
        if track_data.get("hub", {}).get("providers"):
            for provider in track_data["hub"]["providers"]:
                if provider.get("type", "").lower() == "spotify" and provider.get("actions"):
                    for action in provider["actions"]:
                        # Ensure it's a direct track link, not a search query
                        if action.get("type") == "uri" and "spotify:track:" in action.get("uri", ""):
                            logging.info(f"Found Spotify URI: {action['uri']}")
                            return f"https://api.song.link/v1-alpha.1/links?url={quote(action['uri'])}"
        return None

    def get_apple_music_url():
        if track_data.get("hub", {}).get("actions"):
            for action in track_data["hub"]["actions"]:
                # 'applemusicplay' provides the direct track ID
                if action.get("type") == "applemusicplay" and action.get("id"):
                    logging.info(f"Found Apple Music ID: {action['id']}")
                    return f"https://api.song.link/v1-alpha.1/links?platform=itunes&type=song&id={action['id']}"
        return None

    def get_isrc_url():
        if track_data.get("isrc"):
            logging.info(f"Found ISRC: {track_data['isrc']}")
            return f"https://api.song.link/v1-alpha.1/links?isrc={track_data['isrc']}"
        return None

    # Try each method in order of priority
    for method in [get_spotify_url, get_apple_music_url, get_isrc_url]:
        api_query_url = method()
        if api_query_url:
            break
            
    # If a supported identifier was found and a query URL was constructed, use it
    if api_query_url:
        try:
            logging.info(f"Querying song.link API with: {api_query_url}")
            async with session.get(api_query_url, timeout=10) as response:
                if response.status == 200:
                    song_link_data = await response.json()
                    page_url = song_link_data.get("pageUrl")
                    if page_url:
                        return page_url  # Success!
                else:
                    logging.warning(f"song.link API returned status {response.status} for URL {api_query_url}")
        except Exception as e:
            logging.error(f"Failed to query {api_query_url}: {e}")
    else:
        logging.warning("No supported identifiers (Spotify, Apple Music, ISRC) found in Shazam response.")

    # Absolute fallback: if no supported ID was found, return the original Shazam share link.
    logging.warning("Falling back to original Shazam share link.")
    return track_data.get("share", {}).get("href")


async def recognize_song_from_file(session: aiohttp.ClientSession, filepath: str) -> str:
    """Recognizes a track and gets a universal link."""
    if not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "rb") as audio_file:
            form_data = aiohttp.FormData()
            form_data.add_field('file', audio_file, filename=os.path.basename(filepath), content_type='audio/mpeg')
            shazam_api_url = "https://shz.aartzz.pp.ua/recognize_song/"
            
            async with session.post(shazam_api_url, data=form_data, timeout=30) as response:
                if response.status != 200:
                    logging.error(f"Shazam API error: {response.status} - {await response.text()}")
                    return ""

                result = await response.json()
                print("--- SHAZAM API RESPONSE ---")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("---------------------------")

                track_data = result.get("track")
                if not track_data:
                    return ""

                title = track_data.get("title", "Неизвестно")
                artist = track_data.get("subtitle", "Неизвестно")
                
                final_url = await get_song_link(session, result)

                # Return the best available link
                return f'🎶 <a href="{final_url}">{artist} - {title}</a>' if final_url else f'🎶 {artist} - {title}'

    except Exception:
        logging.exception("An error occurred during song recognition.")
        return ""