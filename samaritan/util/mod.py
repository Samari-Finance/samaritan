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

from functools import wraps

from telegram import ChatMember

from samaritan import ADMIN, CREATOR
from samaritan.util.pytgbot import fallback_user_id, fallback_chat_id


def only_admin(method):
    @wraps(method)
    def inner(self, *args, **kwargs):
        # args[0]: update
        # args[1]: context
        user_id = args[0].effective_user.id
        chat_id = args[0].effective_chat.id
        chat_member = args[1].bot.get_chat_member(chat_id, user_id)
        is_admin = chat_member.status in [CREATOR, ADMIN]
        if not is_admin:
            self.log.debug(f'Unauthorized access denied on %s for %s : %s.',
                           method.__name__, user_id, args[1].bot.get_chat(chat_id))
            if args[0].callback_query:
                args[0].callback_query.answer('You do not have the required permissions to access this command')
            elif args[0].message:
                args[0].message.reply_text('You do not have the required permissions to access this command')
            return None  # quit handling command
        return method(self, *args, **kwargs)
    return inner


def only_superadmin(method):
    @wraps(method)
    def inner(self, *args, **kwargs):
        # args[0]: update
        # args[1]: context
        user_id = args[0].effective_user.id  # args[0]: update
        chat_id = args[0].effective_chat.id
        user = args[1].bot.get_chat_member(chat_id, user_id)
        if not is_superadmin(user):
            self.log.debug(f'Unauthorized access denied on %s for %s : %s.',
                           method.__name__, user_id, args[1].bot.get_chat(chat_id))
            if args[0].callback_query:
                args[0].callback_query.answer('You do not have the required permissions to access this command')
            elif args[0].message:
                args[0].message.reply_text('You do not have the required permissions to access this command')
            return None  # quit handling command
        return method(self, *args, **kwargs)
    return inner


def is_superadmin(user: ChatMember):
    is_ = user.can_manage_chat & user.can_manage_voice_chats & user.can_change_info \
                    & user.can_delete_messages & user.can_invite_users & user.can_restrict_members \
                    & user.can_pin_messages & user.can_promote_members and user.status == ADMIN
    if user.status == CREATOR:
        is_ = True
    return is_


def not_banned(method):
    @wraps(method)
    def inner(self, *args, **kwargs):
        # args[0]: update
        user_id = fallback_user_id(args[0])  # args[0]: update
        chat_id = fallback_chat_id(args[0])
        # arg[1]: context
        if self.db.user_not_banned(chat_id, user_id) is False:
            self.log.debug(f'Unauthorized access denied on %s for %s : %s.',
                           method.__name__, user_id, args[0].message.chat.username)
            args[0].message.reply_text('You do not have the required permissions to access this command')
            return None  # quit handling command
        return method(self, *args, **kwargs)
    return inner
