import logging
import re
from datetime import datetime, timedelta
from telegram import Update, ChatMember
from telegram.ext import Updater, CommandHandler, CallbackContext, ChatMemberHandler, MessageHandler, \
    Filters
from core.default_commands import commands
from core.db.mongo_db import MongoConn
from core.utils import read_api, pp_json, send_message, MARKDOWN_V2

KICKED = ChatMember.KICKED
LEFT = ChatMember.LEFT
MEMBER = ChatMember.MEMBER
ADMIN = ChatMember.ADMINISTRATOR


class Samaritan:

    def __init__(self,
                 api_key_file: str = None,
                 db_path: str = None,
                 log_level: logging = logging.INFO):
        self.setup(log_level=log_level)
        self.updater = Updater(token=read_api(api_key_file), use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.shillist_timer = datetime.now() - timedelta(minutes=30)
        self.shillreddit_timer = datetime.now() - timedelta(minutes=10)
        self.add_handles(self.dispatcher)
        self.shillist_msg = None
        self.shillreddit_msg = None
        self.check_commands()
        self.db = MongoConn(read_api(db_path))

    def start(self, update: Update, context: CallbackContext):
        send_message(update, context, text=commands['start'])

    def website(self, update, context):
        send_message(update, context, commands['website'], parse_mode=MARKDOWN_V2)

    def chart(self, update, context):
        send_message(update, context, commands['chart'])

    def version(self, up, ctx):
        send_message(up, ctx, 'V2')

    def trade(self, update, context):
        send_message(update, context, commands['trade'])

    def contract(self, update, context):
        send_message(update, context, commands['contract'], disable_web_page_preview=True)

    def socials(self, update, context):
        send_message(update, context, commands['socials'])

    def price(self, update, context):
        send_message(update, context, commands['price'])

    def mc(self, update, context):
        send_message(update, context, commands['mc'])

    def lp(self, update, context):
        send_message(update, context, commands['lp'], disable_web_page_preview=True, parse_mode=MARKDOWN_V2)

    def shill_list(self, update: Update, context: CallbackContext):
        now = datetime.now()
        if self.shillist_timer + timedelta(minutes=30) <= now:
            self.shillist_msg = send_message(update, context, commands['shillist'])
            self.shillist_timer = now
        else:
            send_message(
                update, context, text=self._prettify_reference(update, 'too_fast', self.shillist_msg.message_id.real))

    @staticmethod
    def _prettify_reference(update: Update, command, prev_msg):
        return f"{commands[command]}/{str(update.message.chat_id)[4:]}/{str(prev_msg)})"

    def shillin(self, update, context):
        send_message(update, context, commands['shillin'])

    def shill_reddit(self, update, context):
        now = datetime.now()
        if self.shillreddit_timer + timedelta(minutes=10) <= now:
            self.shillreddit_msg = send_message(update, context, commands['shillreddit'])
            self.shillreddit_timer = now
        else:
            send_message(
                update, context, parse_mode=MARKDOWN_V2,
                text=self._prettify_reference(update, 'too_fast', self.shillist_msg.message_id.real))

    def shill_telegram(self, update, context):
        send_message(update, context, commands['shilltelegram'])

    def shill_twitter(self, update, context):
        send_message(update, context, commands['shilltwitter'])

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
        new_status = update.chat_member.new_chat_member.status
        old_status = update.chat_member.old_chat_member.status
        if self.evaluate_membership(new_status, old_status)[1]:
            print('evaluated left')
            self.left_member(update, context)
        elif self.evaluate_membership(new_status, old_status)[0]:
            print('evaluated joined')
            self.new_member(update, context)

    def new_member(self, update: Update, context: CallbackContext):
        print('new member')
        pp_json(update.chat_member.to_json())

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
                       f'{chat.get_member(member["id"]).user.full_name}\n'
                counter += 1

            caller = next((x for x in scoreboard if x['id'] == user.id))
            if caller:
                msg += f'\nYour score: {scoreboard.index(caller)+1}. with {caller["pts"]} {"pts":<10}'
            send_message(update, context, msg)

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
        dp.add_handler(CommandHandler('chart', self.chart))
        dp.add_handler(CommandHandler(['trade', 'buy'], self.trade))
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_handler(CommandHandler('commands', self.start))
        dp.add_handler(CommandHandler('price', self.price))
        dp.add_handler(CommandHandler('website', self.website))
        dp.add_handler(CommandHandler(['mc', 'marketcap'], self.mc))
        dp.add_handler(CommandHandler('socials', self.socials))
        dp.add_handler(CommandHandler('contract', self.contract))
        dp.add_handler(CommandHandler(['shillin', 'shill'], self.shillin))
        dp.add_handler(CommandHandler('shillreddit', self.shill_reddit))
        dp.add_handler(CommandHandler('shillist', self.shill_list))
        dp.add_handler(CommandHandler('shilltwitter', self.shill_telegram))
        dp.add_handler(CommandHandler(['shilltelegram', 'shilltg'], self.shill_telegram))
        dp.add_handler(CommandHandler(['invite', 'contest'], self.contest))
        dp.add_handler(CommandHandler('leaderboard', self.leaderboard))
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
            self.lp))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'contract\??', re.IGNORECASE)) |
            Filters.regex(re.compile(r'sc\??', re.IGNORECASE)),
            self.contract))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'website\??', re.IGNORECASE)),
            self.website))
        dp.add_handler(MessageHandler(
            Filters.regex(re.compile(r'pancakeswap\??', re.IGNORECASE)) |
            Filters.regex(re.compile(r'pcs\??', re.IGNORECASE)),
            self.trade))

    @staticmethod
    def setup(log_level):
        logging.basicConfig(level=log_level,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def check_commands(self):
        for key in self.dispatcher.handlers.keys():
            if key not in commands:
                print(f'Command missing: {key}')
