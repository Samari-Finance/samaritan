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

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, Filters, CallbackQueryHandler

from core import CALLBACK_DIVIDER, ADMIN_PREFIX
from core.db import MongoConn
from core.samaritable import Samaritable
from core.utils.utils import fallback_chat_id, log_entexit, fallback_message_id, build_menu, send_message, \
    fallback_user_id
from core.utils.utils_mod import only_superadmin, only_admin


class Moderator(Samaritable):

    def __init__(self,
                 db: MongoConn):
        super().__init__(db)
        self.current_mods = {}

    @only_superadmin
    @log_entexit
    def edit_lounge_deeplink(self, up: Update, ctx: CallbackContext):
        payload = ctx.args[0].split(CALLBACK_DIVIDER)
        super_grp = payload[1]
        lounge_id = fallback_chat_id(up)
        self.db.set_lounge_id_by_chat_id(super_grp, lounge_id)
        ctx.bot.delete_message(fallback_chat_id(up), fallback_message_id(up))

    @only_admin
    @log_entexit
    def admin_menu(self, up: Update, ctx: CallbackContext):
        options = ['settings', 'commands']
        user_id = fallback_user_id(up)
        callback = ADMIN_PREFIX
        reply_markup = self._build_callback_markup(callback, options)
        msg = send_message(
            up=up,
            ctx=ctx,
            text=self.db.get_text_by_handler('admin_menu'),
            replace=True,
            reply_markup=reply_markup)
        self.current_mods[int(user_id)] = {"msg_id": msg.message_id}

    @only_admin
    @log_entexit
    def menu_callback(self, up: Update, ctx: CallbackContext):
        payload = up.callback_query.data.split(CALLBACK_DIVIDER)
        payload.pop(0)
        return getattr(self, payload[0]+'_callback')(payload)

    @only_admin
    @log_entexit
    def settings_callback(self, up: Update, ctx: CallbackContext, payload):
        if len(payload) > 1:
            return getattr(self, payload[0]+'_callback')(payload)
        chat_id = fallback_chat_id(up)
        user_id = fallback_user_id(up)
        options = ['lounge', 'mod', 'delay']
        reply_markup = self._build_callback_markup(payload, options)
        ctx.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=self._get_map_by_user(user_id)['msg_id'],
            reply_markup=reply_markup
        )
        ctx.bot.edit_message_text(
            chat_id=chat_id,
            message_id=self._get_map_by_user(user_id)['msg_id']
        )

    @log_entexit
    def add_handlers(self, dp):
        dp.add_handler(CommandHandler('admin',
                                      self.admin_menu))
        dp.add_handler(CallbackQueryHandler(self.menu_callback,
                                            pattern=f"{ADMIN_PREFIX}{CALLBACK_DIVIDER}([_a-zA-Z0-9-]*)"))
        dp.add_handler(CommandHandler('startgroup',
                                      self.edit_lounge_deeplink,
                                      Filters.regex(r'lounge_([_a-zA-Z0-9-]*)'),
                                      pass_args=True))

    @log_entexit
    def _get_map_by_user(self, user_id):
        return self.current_mods.get(int(user_id))

    @log_entexit
    def _build_callback_markup(self, callback: str, options: list, n_cols=1):
        button_list = [InlineKeyboardButton(
            text=option,
            callback_data=callback + CALLBACK_DIVIDER + option) for option in options]
        return InlineKeyboardMarkup(build_menu(button_list, n_cols=n_cols))

