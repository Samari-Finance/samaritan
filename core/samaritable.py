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
