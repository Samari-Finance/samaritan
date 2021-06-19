import logging
from abc import ABC, abstractmethod
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

    @abstractmethod
    def add_handlers(self, dp):
        pass
