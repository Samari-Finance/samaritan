from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from core.db import MongoConn
from core.samaritable import Samaritable
from core.utils.utils import log_entexit, fallback_chat_id, fallback_user_id, send_message


class Contestor(Samaritable):

    def __init__(self,
                 db: MongoConn):
        super().__init__(db)
        self.db = db

    @log_entexit
    def leaderboard(self, up: Update, ctx: CallbackContext):
        limit = 10
        counter = 1
        chat_id = fallback_chat_id(up)
        user_id = fallback_user_id(up)
        msg = f'🏆 INVITE CONTEST LEADERBOARD 🏆\n\n'
        scoreboard = sorted(self.db.get_members_pts(chat_id=chat_id), key=lambda i: i['pts'])

        try:
            if len(ctx.args) > 0:
                limit = int(ctx.args[0])
                if limit > 50:
                    limit = 50
            for member in scoreboard[:limit]:
                msg += f'{str(counter) + ".":<3} {chat_id.get_member(member["id"]).user.name:<20}' \
                       f' with {member["pts"]} {"pts"}\n'
                counter += 1

            caller = next((x for x in scoreboard if x['id'] == user_id.id), None)
            if caller:
                msg += f'\nYour score: {scoreboard.index(caller) + 1}. with {caller["pts"]:<3} {"pts"}'
            send_message(up, ctx, msg, disable_notification=True, reply=False)

        except ValueError:
            send_message(up, ctx, f'Invalid argument: {ctx.args} for leaderboard command')

    def add_handlers(self, dp):
        dp.add_handler(CommandHandler('leaderboard', self.leaderboard))
