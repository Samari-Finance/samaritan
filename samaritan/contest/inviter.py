from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, Filters

from samaritan import PRIVATE, CALLBACK_DIVIDER
from samaritan.db import MongoConn
from samaritan.samaritable import Samaritable
from samaritan.util.pytgbot import fallback_user_id, fallback_chat_id, send_message, gen_invite_request_deeplink, \
    build_menu
from test.log.logger import log_entexit


class Inviter(Samaritable):

    def __init__(self,
                 db: MongoConn):
        super().__init__(db)
        self.db = db

    @log_entexit
    def invite(self, up: Update, ctx: CallbackContext):
        user_id = fallback_user_id(up)
        chat_id = fallback_chat_id(up)
        priv_chat_id = self.db.get_private_chat_id(chat_id, user_id)

        if up.message.chat.type == PRIVATE:
            send_message(up, ctx,
                         text='Cannot generate invite link for private conversation 😔\n'
                              'Use this command in a group we are both part of!',
                         reply=False)
        elif not priv_chat_id:
            url = gen_invite_request_deeplink(up, ctx)
            button_list = [InlineKeyboardButton(text="Click here to start private conversation", url=url)]
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            self.log.debug('Requesting invite: {deeplink=%s', url)
            send_message(
                up=up,
                ctx=ctx,
                text=self.db.get_text_by_handler('invite'),
                replace=True,
                reply_markup=reply_markup)
        else:
            self.send_invite_link(up, ctx, chat_id, priv_chat_id, user_id)
            send_message(up, ctx,
                         text='check your dms 😉',
                         replace=True)

    @log_entexit
    def invite_deeplink(self, up: Update, ctx: CallbackContext):
        payload = ctx.args[0].split(CALLBACK_DIVIDER)
        pub_chat_id = payload[1]
        priv_chat_id = fallback_chat_id(up)
        user_id = fallback_user_id(up)
        self.send_invite_link(up, ctx, pub_chat_id, priv_chat_id, user_id)
        self.db.set_private_chat_id(pub_chat_id, user_id, priv_chat_id)

    @log_entexit
    def send_invite_link(self, up: Update, ctx: CallbackContext, public_chat_id, private_chat_id, user_id):
        link = self.db.get_invite_by_user_id(public_chat_id, user_id)
        if not link:
            link = ctx.bot.create_chat_invite_link(public_chat_id).invite_link
            self.db.set_invite_link_by_id(chat_id=public_chat_id, link=link, user_id=user_id)
        send_message(up, ctx,
                     chat_id=private_chat_id,
                     reply=False,
                     text=f'Here is your personal invite link: {link}\n'
                          f'Share this to earn points in the community challenge! 💪')

    def add_handlers(self, dp):
        dp.add_handler(CommandHandler(['invite', 'contest'], self.invite))
        dp.add_handler(CommandHandler('start',
                                      self.invite_deeplink,
                                      Filters.regex(r'invite_([_a-zA-Z0-9-]*)'),
                                      pass_args=True))