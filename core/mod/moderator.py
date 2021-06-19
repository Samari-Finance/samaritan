from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Filters

from core import CALLBACK_DIVIDER
from core.db import MongoConn
from core.mod import only_superadmin
from core.samaritable import Samaritable
from core.utils.utils import fallback_chat_id


class Moderator(Samaritable):

    def __init__(self,
                 db: MongoConn):
        super().__init__(db)

    @only_superadmin
    def edit_lounge_deeplink(self, up: Update, ctx: CallbackContext):
        payload = ctx.args[0].split(CALLBACK_DIVIDER)
        super_grp = payload[1]
        lounge_id = fallback_chat_id(up)
        self.db.set_lounge_id_by_chat_id(super_grp, lounge_id)

    def add_handlers(self, dp):
        dp.add_handler(CommandHandler('startgroup',
                                      self.edit_lounge_deeplink,
                                      Filters.regex(r'lounge_([_a-zA-Z0-9-]*)'),
                                      pass_args=True))

