def trigger_message(triggers: dict, main_str: str, check_method: int = 0, is_admin = False, channel_message = False):
    for s in triggers.keys():
        if check_method == 0 and s in main_str and not channel_message: # not channel message, contains
            return triggers[s]
        elif check_method == 1 and main_str.startswith(s) and is_admin:
            return triggers[s]
        elif check_method == 2 and s in main_str and channel_message:
            return triggers[s]
        elif check_method == 3 and main_str == s and not channel_message:
            return triggers[s]
    return None

def is_message_command(msg: str) -> str | None:
    msg = msg.lower()
    for s in ["г!", "гастер ", "гасир ", "гасер ", "гастур ", "гасёр ", "гангстер ", "гастрит ", "гастроэнтеролог ", "гастроентеролог ", "гандон ", "гитлер ", "любитель подрочить в тени "]:
        if msg.startswith(s):
            return msg[len(s):]

def is_any_from(string: str, queries: list) -> bool:
    for s in queries:
        if string == s:
            return True
    return False

def is_any_from_startswith(string: str, queries: list) -> bool:
    for s in queries:
        if string.startswith(s):
            return True
    return False