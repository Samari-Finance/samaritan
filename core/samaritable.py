import logging
from abc import ABC, abstractmethod
from functools import wraps

from telegram import ChatMember

from core import CREATOR, ADMIN
from core.db import MongoConn
from core.utils.utils_mod import is_superadmin


class Samaritable(ABC):
    def __init__(self,
                 db: MongoConn):
        self.log = self._aggregate_logger()
        self.db = db

    def __set_name__(self, owner, name):
        self.name = name

    def _aggregate_logger(self):
        if self.__class__.__name__.lower() == 'samaritable' or self.__class__.__name__.lower() == 'samaritan':
            name = 'samaritan'
        else:
            name = 'samaritan.'+self.__class__.__name__.lower()
        return logging.getLogger(name)

    def only_admins(self, method):
        @wraps(method)
        def inner(self_inner, *args, **kwargs):
            user_id = args[0].effective_user.id  # args[0]: update
            chat_id = args[0].effective_chat.id
            is_admin = args[1].bot.get_chat_member(chat_id, user_id).status == ADMIN
            if not is_admin:
                self.log.debug(f'Unauthorized access denied on %s for %s : %s.',
                               method.__name__, user_id, args[0].message.chat.username)
                args[0].message.reply_text('You do not have the required permissions to access this command')
                return None  # quit handling command
            return method(self_inner, *args, **kwargs)
        return inner

    def only_superadmin(self, method):
        @wraps(method)
        def inner(self_inner, *args, **kwargs):
            # args[0]: update
            user_id = args[0].effective_user.id  # args[0]: update
            chat_id = args[0].effective_chat.id
            user = args[1].bot.get_chat_member(chat_id, user_id)
            if not is_superadmin(user):
                self.log.debug(f'Unauthorized access denied on %s for %s : %s.',
                               method.__name__, user_id, args[0].message.chat.username)
                args[0].message.reply_text('You do not have the required permissions to access this command')
                return None  # quit handling command
            return method(self_inner, *args, **kwargs)
        return inner

    @abstractmethod
    def add_handlers(self, dp):
        pass
