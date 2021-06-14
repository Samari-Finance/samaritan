import logging


class Samaritable:
    def __init__(self):
        self.log = self._aggregate_log_name()

    def __set_name__(self, owner, name):
        self.name = name

    def _aggregate_log_name(self):
        if self.__class__.__name__.lower() == 'samaritable' or self.__class__.__name__.lower() == 'samaritan':
            name = 'samaritan'
        else:
            name = 'samaritan.'+self.__class__.__name__.lower()
        return logging.getLogger(name)
