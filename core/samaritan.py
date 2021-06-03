import logging
import re
from datetime import datetime, timedelta

import telegram
from telegram import Update, ChatMember
from telegram.ext import Updater, CommandHandler, CallbackContext, ChatMemberHandler, MessageHandler, \
    Filters
from telegram.utils.helpers import DEFAULT_NONE

from core.default_commands import commands
from core.db.mongo_db import MongoConn
from core.utils import read_api, send_message, MARKDOWN_V2

KICKED = ChatMember.KICKED
LEFT = ChatMember.LEFT
MEMBER = ChatMember.MEMBER
ADMIN = ChatMember.ADMINISTRATOR

DEFAULT_DELAY = timedelta(seconds=30)


class Samaritan:

    def __init__(self,
                 api_key_file: str = None,
                 db_path: str = None,
                 log_level: logging = logging.INFO):
        setup_log(log_level=log_level)
        self.updater = Updater(token=read_api(api_key_file), use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.db = MongoConn(read_api(db_path))
        self.add_handles(self.dispatcher)

    def gen_handler_attr(self):
        for key in self.db.handlers:
            setattr(key['_id'], )

    def gen_handler(self, handler_name: str):

        def handler(attributes: dict):
            if 'command' in dict.keys():
                return self.gen_commandhandler(handler_name, attributes)
        return handler


    def start(self, update: Update, context: CallbackContext):
        send_message(update, context, text=commands['start'])

    def website(self, update, context):
        send_message(update, context, commands['website'], parse_mode=MARKDOWN_V2)

    def website_regex(self, update: Update, context):
        if self.isnot_sentence(update.message):
            self.website(update, context)

    def chart(self, update: Update, context):
        send_message(update, context, commands['chart'])

    def chart_regex(self, update, context):
        if self.isnot_sentence(update.message):
            self.chart(update, context)

    def version(self, up, ctx):
        if self.isnot_sentence(up.message):
            send_message(up, ctx, 'V2')

    def trade(self, update, context):
        send_message(update, context, commands['trade'])

    def trade_regex(self, update: Update, context):
        if self.isnot_sentence(update.message):
            self.trade(update, context)

    def contract(self, update, context):
        send_message(update, context, commands['contract'], disable_web_page_preview=True)

    def contract_regex(self, update: Update, context):
        if self.isnot_sentence(update.message):
            self.contract(update, context)

    def socials(self, update, context):
        send_message(update, context, commands['socials'])

    def price(self, update, context):
        send_message(update, context, commands['price'])

    def mc(self, update, context):
        send_message(update, context, commands['mc'])

    def lp_regex(self, update: Update, context):
        if self.isnot_sentence(update.message):
            self.lp(update, context)

    def lp(self, update, context):
        send_message(update, context, commands['lp'], disable_web_page_preview=True, parse_mode=MARKDOWN_V2)

    @staticmethod
    def _prettify_reference(update: Update, prev_msg):
        return f"{commands['too_fast']['text']}/{str(update.message.chat_id)[4:]}/{str(prev_msg)})"

    def contest(self, update: Update, context: CallbackContext):
        user = update.effective_user
        chat_id = update.effective_chat.id
        link = self.db.get_invite_by_user_id(user.id)
        if not link:
            link = context.bot.create_chat_invite_link(chat_id).invite_link
            self.db.set_invite_link_by_id(link=link, user_id=user.id)
        else:
            link = link['invite_link']
        send_message(update, context,
                     reply=True,
                     text=f'Here is your personal invite link: {link}')

    def member_updated(self, update: Update, context: CallbackContext):
        if update.chat_member.new_chat_member and update.chat_member.old_chat_member:
            new_status = update.chat_member.new_chat_member.status
            old_status = update.chat_member.old_chat_member.status
            if self.evaluate_membership(new_status, old_status)[1]:
                print('evaluated left')
                self.left_member(update, context)
            elif self.evaluate_membership(new_status, old_status)[0]:
                print('evaluated joined')
                self.new_member(update, context)

    def new_member(self, update: Update, context: CallbackContext):
        if update.chat_member.invite_link:
            link = update.chat_member.invite_link.invite_link
            self.db.set_new_ref(link, update.effective_user.id)

    def left_member(self, update: Update, context: CallbackContext):
        self.db.remove_ref(user_id=update.effective_user.id)

    def leaderboard(self, update: Update, context: CallbackContext):
        limit = 10
        counter = 1
        chat = update.effective_chat
        user = update.effective_user
        msg = f'🏆 INVITE CONTEST LEADERBOARD 🏆\n\n'
        scoreboard = sorted(self.db.get_members_pts(), key=lambda i: i['pts'])

        try:
            if len(context.args) > 0:
                limit = int(context.args[0])
                if limit > 50:
                    limit = 50
            for member in scoreboard[:limit]:
                msg += f'{counter}. with {member["pts"]} {"pts:":<10}' \
                       f'{chat.get_member(member["id"]).user.name}\n'
                counter += 1

            caller = next((x for x in scoreboard if x['id'] == user.id))
            if caller:
                msg += f'\nYour score: {scoreboard.index(caller)+1}. with {caller["pts"]} {"pts":<10}'
            send_message(update, context, msg, disable_notification=True)

        except ValueError:
            send_message(update, context, f'Invalid argument: {context.args} for leaderboard command')

    @staticmethod
    def evaluate_membership(new, old):
        just_joined = False
        just_left = False

        if (old == KICKED or old == LEFT) and new == MEMBER:
            just_joined = True
        elif (old == MEMBER) and (new == LEFT or new == KICKED):
            just_left = True

        return just_joined, just_left

    def start_polling(self):
        self.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    def add_handles(self, dp):
        self.set_dp_handlers(dp)
        dp.add_handler(CommandHandler('leaderboard', self.leaderboard))
        dp.add_handler(CommandHandler(['invite', 'contest'], self.contest))
        dp.add_handler(ChatMemberHandler(
            chat_member_types=ChatMemberHandler.ANY_CHAT_MEMBER, callback=self.member_updated))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'v2\??')) |
            Filters.regex(re.compile(r'v1\??')),
            self.version))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'lp locked\??', re.IGNORECASE)) |
            Filters.regex(re.compile(r'liquidity locked\??', re.IGNORECASE)) |
            Filters.regex(re.compile(r'locked\??', re.IGNORECASE)) |
            Filters.regex(re.compile(r'lp\??', re.IGNORECASE)),
            self.lp_regex))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'contract\??', re.IGNORECASE)) |
            Filters.regex(re.compile(r'sc\??', re.IGNORECASE)),
            self.contract_regex))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'website\??', re.IGNORECASE)),
            self.website_regex))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'pancakeswap\??', re.IGNORECASE)) |
            Filters.regex(re.compile(r'pcs\??', re.IGNORECASE)),
            self.trade_regex))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'chart\??', re.IGNORECASE)),
            self.chart_regex
        ))


def regex_req(msg: telegram.Message):
    return len(msg.text.split()) < 4


def setup_log(log_level):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
