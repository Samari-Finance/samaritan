import logging
import re
from datetime import datetime, timedelta
from functools import wraps

from telegram import (
    Update,
    ChatMember,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup, Message
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ChatMemberHandler,
    MessageHandler,
    Filters, CallbackQueryHandler
)
from telegram.utils.helpers import (
    DEFAULT_NONE,
    create_deep_linked_url
)

from core.default_commands import commands
from core.db.mongo_db import MongoConn
from core.utils import read_api, send_message, MARKDOWN_V2, build_menu

# Constants used for incoming member updates
KICKED = ChatMember.KICKED
LEFT = ChatMember.LEFT
MEMBER = ChatMember.MEMBER
ADMIN = ChatMember.ADMINISTRATOR
RESTRICTED = ChatMember.RESTRICTED
CREATOR = ChatMember.CREATOR

# Default delay for timed attributes
DEFAULT_DELAY = timedelta(seconds=30)

# Just captcha
CAPTCHA = 'captcha'
CAPTCHA_CALLBACK = 'completed'


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
        for key in self.db.default_handlers.find():
            _handle = self.gen_handler(key)
            setattr(self, f"_handler_{key['_id']}", _handle)

    def gen_handler(self, handler_attr: dict):

        def handler(update, context):
            if 'command' == handler_attr['type']:
                return self.gen_command_handler(update, context, handler_attr)
            elif 'timed' == handler_attr['type']:
                return self.gen_timed_handler(update, context, handler_attr)
            elif 'regex' == handler_attr['type']:
                return self.gen_regex_handler(update, context, handler_attr)
        return handler

    def gen_command_handler(self, update, context, attributes: dict):
        return send_message(update, context,
                            text=attributes['text'],
                            reply=attributes.get('reply', False),
                            parse_mode=attributes.get('parse_mode', DEFAULT_NONE),
                            disable_notification=attributes.get('disable_notification', False),
                            disable_web_page_preview=attributes.get('disable_web_preview', DEFAULT_NONE))

    def gen_timed_handler(self, up: Update, ctx: CallbackContext, attributes: dict):
        now = datetime.now()
        timer_str = f"_{attributes['_id']}_timer"
        msg_str = f"_{attributes['_id']}_msg"
        attr_delay = timedelta(seconds=attributes.get('delay', DEFAULT_DELAY))
        attr_timer = getattr(self, timer_str, now - attr_delay)

        if attr_timer + attr_delay <= now:
            new_msg = send_message(up, ctx, attributes.get('text'))
            setattr(self, msg_str, new_msg)
            setattr(self, timer_str, now)
        else:
            send_message(up, ctx,
                         text=self._prettify_reference(up, getattr(self, msg_str).message_id.real),
                         parse_mode=MARKDOWN_V2)

    def gen_regex_handler(self, up: Update, ctx: CallbackContext, attributes: dict):
        if regex_req(up.message):
            return getattr(self, f"_handler_{attributes['_id']}")

    def set_dp_handlers(self, dp):
        self.gen_handler_attr()
        resolvers = {
            'command': CommandHandler,
            'timed': CommandHandler,
            'regex': MessageHandler,
        }
        for key in self.db.default_handlers.find():
            if key['type'] == 'util':
                continue
            handler_type = resolvers[key['type']]
            dp.add_handler(handler_type(key['aliases'], getattr(self, f"_handler_{key['_id']}")))

    def website_regex(self, update: Update, context):
        if regex_req(update.message):
            send_message(update, context, commands['website']['text'], parse_mode=MARKDOWN_V2)

    def chart_regex(self, update, context):
        if regex_req(update.message):
            send_message(update, context, commands['chart']['text'])

    def version(self, up, ctx):
        if regex_req(up.message):
            send_message(up, ctx, 'V2')

    def trade_regex(self, update: Update, context):
        if regex_req(update.message):
            getattr(self, f"_handler_trade")(update, context)

    def contract(self, update, context):
        send_message(update, context, commands['contract'], disable_web_page_preview=True)

    def contract_regex(self, update: Update, context):
        if regex_req(update.message):
            self.contract(update, context)

    def price(self, update, context):
        send_message(update, context, commands['price'])

    def lp_regex(self, update: Update, context):
        if regex_req(update.message):
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
            print(f'statuses: {new_status}, {old_status}')
            if self.evaluate_membership(new_status, old_status)[1]:
                print('evaluated left')
                self.left_member(update, context)
            elif self.evaluate_membership(new_status, old_status)[0]:
                print('evaluated joined')
                self.new_member(update, context)

    def new_member(self, update: Update, context: CallbackContext):
        context.bot.restrict_chat_member(chat_id=update.effective_chat.id,
                                         user_id=update.effective_user.id,
                                         permissions=ChatPermissions(can_send_messages=False))
        self.request_captcha(update, context)

        if update.chat_member.invite_link:
            link = update.chat_member.invite_link.invite_link
            self.db.set_new_ref(link, update.effective_user.id)

    def left_member(self, update: Update, context: CallbackContext):
        self.db.remove_ref(user_id=update.effective_user.id)

    def request_captcha(self, up: Update, ctx: CallbackContext):
        print('requesting captcha')
        url = f'https://t.me/{ctx.bot.username}?start=captcha'
        print(url)
        button_list = [InlineKeyboardButton(text="Click Me!", url=url)]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        send_message(up, ctx, text='Please complete the captcha!', reply_markup=reply_markup)

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
                msg += f'{str(counter)+".":<3} {chat.get_member(member["id"]).user.name:<20} with {member["pts"]} {"pts"}\n' \

                counter += 1

            caller = next((x for x in scoreboard if x['id'] == user.id))
            if caller:
                msg += f'\nYour score: {scoreboard.index(caller)+1}. with {caller["pts"]:<3} {"pts"}'
            send_message(update, context, msg, disable_notification=True)

        except ValueError:
            send_message(update, context, f'Invalid argument: {context.args} for leaderboard command')

    @staticmethod
    def evaluate_membership(new, old):
        just_joined = False
        just_left = False

        if (old == KICKED or old == LEFT or old == RESTRICTED) and (new == MEMBER or new == RESTRICTED):
            just_joined = True
        elif (old == MEMBER | old == RESTRICTED) and (new == LEFT or new == KICKED):
            just_left = True

        return just_joined, just_left

    def start_polling(self):
        self.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    def captcha_deeplink(self, up: Update, ctx: CallbackContext):
        url = f'https://t.me/samaritantestt?captcha=completed'
        button_list = [InlineKeyboardButton(text="Click me to confirm you're a human!", url=url)]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        send_message(up, ctx,
                     text='Welcome to the Samaritan family ❤️ Click below to return to the chat:',
                     reply_markup=reply_markup)
        up.callback_query.answer()

    def captcha_callback(self, up: Update, ctx: CallbackContext):
        payload = ctx.args
        print('payload')
        if payload.count('completed') > 0:
            send_message(up, ctx, f'Welcome {up.effective_user}! enter /commands to read all commands')

    def add_handles(self, dp):
        dp.add_handler(CommandHandler('start', self.captcha_deeplink, Filters.regex(CAPTCHA), pass_args=True))
        self.set_dp_handlers(dp)
        dp.add_handler(CallbackQueryHandler(self.captcha_callback, pattern=CAPTCHA_CALLBACK))
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

    def _wrap_method(self, method):  # Wrapper called in case of a method
        @wraps(method)
        def inner(self_inner, *args, **kwargs):  # `self` is the *inner* class' `self` here
            user_id = args[0].effective_user.id  # args[0]: update
            if user_id not in self.db.get_admins:
                print(f'Unauthorized access denied on {method.__name__} '
                      f'for {user_id} : {args[0].message.chat.username}.')
                args[0].message.reply_text('You do not have the required permissions to access this command')
                return None  # quit handling command
            return method(self_inner, *args, **kwargs)
        return inner


def regex_req(msg: Message):
    return len(msg.text.split()) < 4


def setup_log(log_level):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
