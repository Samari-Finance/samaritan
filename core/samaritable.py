import logging
from abc import ABC, abstractmethod
from functools import wraps

from core import CREATOR
from core.db import MongoConn


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
            if user_id not in self.db.get_admins:
                print(f'Unauthorized access denied on {method.__name__}'
                      f'for {user_id} : {args[0].message.chat.username}.')
                args[0].message.reply_text('You do not have the required permissions to access this command')
                return None  # quit handling command
            return method(self_inner, *args, **kwargs)
        return inner

    def only_creator(self, method):
        @wraps(method)
        def inner(self_inner, *args, **kwargs):
            user_id = args[0].effective_user.id
            is_creator = args[0].chat_member.new_chat_member.status == CREATOR  # args[0]: update

            if is_creator:
                print(f'Unauthorized access denied on {method.__name__}'
                      f'for {user_id} : {args[0].message.chat.username}.')
                args[0].message.reply_text('You do not have the required permissions to access this command')
                return None  # quit handling command
            return method(self_inner, *args, **kwargs)
        return inner

    @abstractmethod
    def add_handlers(self, dp):
        pass
