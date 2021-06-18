from telegram import ChatMember

from core import ADMIN


def is_superadmin(user: ChatMember):
    is_superadmin = user.can_manage_chat & user.can_manage_voice_chats & user.can_change_info \
                    & user.can_delete_messages & user.can_invite_users & user.can_restrict_members \
                    & user.can_pin_messages & user.can_promote_members and user.status == ADMIN
    return is_superadmin
