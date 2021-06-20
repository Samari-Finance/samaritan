from abc import ABC, abstractmethod
from samaritan.db import MongoConn
from test.log.logger import aggregate_logger


class Samaritable(ABC):
    def __init__(self,
                 db: MongoConn):
        self.log = aggregate_logger(self)
        self.db = db

    @abstractmethod
    def add_handlers(self, dp):
        pass

    @classmethod
    def __name__(cls):
        return cls.__module__
