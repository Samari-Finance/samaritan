"""Samaritan
Copyright (C) 2021 Samari.finance

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
---------------------------------------------------------------------"""

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
ADMIN_PREFIX = 'admin'

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

"""Cool dev user id"""
DEV_ID = 1616611398