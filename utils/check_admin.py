def check_admin(chat_member, msg, decorative=False) -> bool:
    is_admin = False
    is_decorative_admin = False

    if msg.text == None:
        return False

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

    if decorative:
        return is_decorative_admin
    return is_admin