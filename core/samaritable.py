import logging


class Samaritable:
    def __init__(self):
        self.log = logging.getLogger()

    def __set_name__(self, owner, name):
        self.name = name

