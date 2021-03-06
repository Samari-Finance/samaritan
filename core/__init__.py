from datetime import timedelta
from telegram import ChatMember, ChatPermissions, Chat

"""Message formats
"""
MARKDOWN_V2 = 'MarkdownV2'
HTML = 'html'

"""Constants used for incoming member updates
"""
KICKED = ChatMember.KICKED
LEFT = ChatMember.LEFT
MEMBER = ChatMember.MEMBER
ADMIN = ChatMember.ADMINISTRATOR
RESTRICTED = ChatMember.RESTRICTED
CREATOR = ChatMember.CREATOR

"""Constants for chat update types
"""
PRIVATE = Chat.PRIVATE
SUPERGROUP = Chat.SUPERGROUP
GROUP = Chat.GROUP
CHANNEL = Chat.CHANNEL

"""Handler type names
"""
REGEX = 'regex'
COMMAND = 'command'
TIMED = 'timed'
UTIL = 'util'
CAPTCHA = 'captcha'

"""Default delay for timed attributes
"""
DEFAULT_DELAY = timedelta(seconds=30)

"""Deeplink/callback constants
"""
CALLBACK_DIVIDER = '_'
CAPTCHA_CALLBACK_PREFIX = 'completed'
CAPTCHA_PREFIX = 'captcha'
INVITE_PREFIX = 'invite'
LOUNGE_PREFIX = 'lounge'

"""Standard member permissions
"""
MEMBER_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_invite_users=True,
    can_send_media_messages=True,
    can_add_web_page_previews=True,
    can_send_other_messages=True,
    can_change_info=True,
    can_send_polls=True,
    can_pin_messages=True,
)
