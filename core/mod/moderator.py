"""Samaritan
Copyright (C) 2021 Samari.finance

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
---------------------------------------------------------------------"""

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Filters

from core import CALLBACK_DIVIDER
from core.db import MongoConn
from core.samaritable import Samaritable
from core.utils.utils import fallback_chat_id, log_entexit, fallback_message_id
from core.utils.utils_mod import only_superadmin


class Moderator(Samaritable):

    def __init__(self,
                 db: MongoConn):
        super().__init__(db)

    @only_superadmin
    @log_entexit
    def edit_lounge_deeplink(self, up: Update, ctx: CallbackContext):
        payload = ctx.args[0].split(CALLBACK_DIVIDER)
        super_grp = payload[1]
        lounge_id = fallback_chat_id(up)
        self.db.set_lounge_id_by_chat_id(super_grp, lounge_id)
        ctx.bot.delete_message(fallback_chat_id(up), fallback_message_id(up))

    @log_entexit
    def add_handlers(self, dp):
        dp.add_handler(CommandHandler('startgroup',
                                      self.edit_lounge_deeplink,
                                      Filters.regex(r'lounge_([_a-zA-Z0-9-]*)'),
                                      pass_args=True))

