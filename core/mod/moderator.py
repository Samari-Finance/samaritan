from core.db import MongoConn
from core.samaritable import Samaritable


class Moderator(Samaritable):

    def __init__(self,
                 db: MongoConn):
        super().__init__(db)

    def add_handlers(self, dp):
        pass
