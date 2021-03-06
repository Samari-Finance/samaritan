from functools import wraps

from telegram import ChatMember

from core import ADMIN


def only_admins(method):
    @wraps(method)
    def inner(self, *args, **kwargs):
        user_id = args[0].effective_user.id  # args[0]: update
        chat_id = args[0].effective_chat.id
        is_admin = args[1].bot.get_chat_member(chat_id, user_id).status == ADMIN
        if not is_admin:
            self.log.debug(f'Unauthorized access denied on %s for %s : %s.',
                           method.__name__, user_id, args[0].message.chat.username)
            args[0].message.reply_text('You do not have the required permissions to access this command')
            return None  # quit handling command
        return method(self, *args, **kwargs)
    return inner


def only_superadmin(method):
    @wraps(method)
    def inner(self, *args, **kwargs):
        # args[0]: update
        user_id = args[0].effective_user.id  # args[0]: update
        chat_id = args[0].effective_chat.id
        user = args[1].bot.get_chat_member(chat_id, user_id)
        if not is_superadmin(user):
            self.log.debug(f'Unauthorized access denied on %s for %s : %s.',
                           method.__name__, user_id, args[0].message.chat.username)
            args[0].message.reply_text('You do not have the required permissions to access this command')
            return None  # quit handling command
        return method(self, *args, **kwargs)
    return inner


def is_superadmin(user: ChatMember):
    is_superadmin = user.can_manage_chat & user.can_manage_voice_chats & user.can_change_info \
                    & user.can_delete_messages & user.can_invite_users & user.can_restrict_members \
                    & user.can_pin_messages & user.can_promote_members and user.status == ADMIN
    return is_superadmin
