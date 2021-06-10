"""
    Telegram bot for Samari.finance Telegram group using python-telegram-bot
    @ https://github.com/python-telegram-bot/python-telegram-bot

"""

import logging
import re
from datetime import datetime, timedelta
from functools import wraps

from telegram import (
    Update,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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
)

from core import (
    DEFAULT_DELAY,
    MARKDOWN_V2,
    LEFT, KICKED, RESTRICTED, MEMBER, ADMIN, CREATOR
)
from core.captcha.challenger import Challenger
from core.default_commands import commands
from core.db.mongo_db import MongoConn
from core.samaritable import Samaritable
from core.utils import (
    read_api,
    build_menu,
    send_message,
    regex_req,
    gen_captcha_request_deeplink, setup_log
)

log = logging.getLogger('telegram.bot')


class Samaritan(Samaritable):

    def __init__(self,
                 api_key_file: str = None,
                 db_path: str = None,
                 log_level: logging = logging.INFO):
        setup_log(log_level=log_level)
        self.updater = Updater(token=read_api(api_key_file), use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.db = MongoConn(read_api(db_path))
        self.challenger = Challenger(self.db)
        self.add_handles(self.dispatcher)
        super().__init__()

    def gen_handler_attr(self):
        for key in self.db.default_handlers.find():
            _handle = self.gen_handler(key)
            setattr(self, f"_handler_{key['_id']}", _handle)

    def gen_handler(self, handler_attr: dict):

        def handler(up, ctx):
            if 'command' == handler_attr['type']:
                return self.gen_command_handler(up, ctx, handler_attr)
            elif 'timed' == handler_attr['type']:
                return self.gen_timed_handler(up, ctx, handler_attr)
            elif 'regex' == handler_attr['type']:
                return self.gen_regex_handler(up, ctx, handler_attr)
        return handler

    def gen_command_handler(self, up, ctx, attributes: dict):
        return send_message(up, ctx,
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
            if key['type'] == 'util' or key['type'] == 'captcha':
                continue
            handler_type = resolvers[key['type']]
            dp.add_handler(handler_type(key['aliases'], getattr(self, f"_handler_{key['_id']}")))

    def website_regex(self, up: Update, ctx: CallbackContext):
        if regex_req(up.message):
            send_message(up, ctx, commands['website']['text'], parse_mode=MARKDOWN_V2)

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

    def contest(self, up: Update, ctx: CallbackContext):
        user = up.effective_user
        chat_id = up.effective_chat.id
        link = self.db.get_invite_by_user_id(user.id)
        if not link:
            link = ctx.bot.create_chat_invite_link(chat_id).invite_link
            self.db.set_invite_link_by_id(link=link, user_id=user.id)
        else:
            link = link['invite_link']
        send_message(up, ctx,
                     reply=True,
                     text=f'Here is your personal invite link: {link}')

    def member_updated(self, up: Update, ctx: CallbackContext):
        if up.chat_member.new_chat_member and up.chat_member.old_chat_member:
            new_member = up.chat_member.new_chat_member
            old_member = up.chat_member.old_chat_member
            if self.evaluate_membership(new_member, old_member)[1]:
                self.left_member(up, ctx)
            elif self.evaluate_membership(new_member, old_member)[0]:
                self.new_member(up, ctx)
        elif up.chat_member.new_chat_member and not up.chat_member.old_chat_member:
            self.new_member(up, ctx)

    def new_member(self, up: Update, ctx: CallbackContext):
        ctx.bot.restrict_chat_member(chat_id=up.effective_chat.id,
                                     user_id=up.chat_member.new_chat_member.user.id,
                                     permissions=ChatPermissions(can_send_messages=False))
        self.request_captcha(up, ctx)

        if up.chat_member.invite_link:
            link = up.chat_member.invite_link.invite_link
            self.db.set_new_ref(link, up.chat_member.new_chat_member.user.id)

    def left_member(self, up: Update, ctx: CallbackContext):
        self.db.remove_ref(user_id=up.effective_user.id)
        self.db.set_captcha_status(user_id=up.effective_user.id, status=False)

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

            caller = next((x for x in scoreboard if x['id'] == user.id), None)
            if caller:
                msg += f'\nYour score: {scoreboard.index(caller)+1}. with {caller["pts"]:<3} {"pts"}'
            send_message(update, context, msg, disable_notification=True, reply=False)

        except ValueError:
            send_message(update, context, f'Invalid argument: {context.args} for leaderboard command')

    @staticmethod
    def evaluate_membership(new_member, old_member):
        old_status = old_member.status
        new_status = new_member.status

        print(f'old_status: {old_status}')
        print(f'new_status: {new_status}')

        just_joined = False
        just_left = False

        if new_status == RESTRICTED or old_status == RESTRICTED:
            if new_member.is_member is False and old_member.is_member is True:
                just_left = True
            elif new_member.is_member is True and old_member.is_member is False:
                just_joined = True
        elif old_status and new_status:
            if (old_status == LEFT or old_status == KICKED) and (new_status == MEMBER or new_status == RESTRICTED):
                just_joined = True
            elif (old_status == MEMBER or old_status == ADMIN or old_status == CREATOR) and \
                    (new_status == KICKED or new_status == LEFT):
                just_left = True

        print(f'just_joined: {just_joined}, just_left: {just_left}')
        return just_joined, just_left

    def request_captcha(self, up: Update, ctx: CallbackContext):
        url = gen_captcha_request_deeplink(up, ctx, -1)
        button_list = [InlineKeyboardButton(text="👋 Click here for captcha 👋", url=url)]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        msg = send_message(
            text=self.captcha_text(up, ctx),
            reply_markup=reply_markup,
            update=up,
            context=ctx)
        url = gen_captcha_request_deeplink(up, ctx, msg.message_id)
        button_list = [InlineKeyboardButton(text="👋 Click here for captcha 👋", url=url)]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        ctx.bot.edit_message_reply_markup(
            chat_id=up.effective_chat.id,
            message_id=msg.message_id,
            reply_markup=reply_markup
        )

    def start_polling(self):
        self.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    def add_handles(self, dp):
        dp.add_handler(CommandHandler('start',
                                      self.challenger.captcha_deeplink,
                                      Filters.regex(r'captcha_([a-zA-Z0-9]*)'),
                                      pass_args=True))
        self.set_dp_handlers(dp)
        dp.add_handler(CommandHandler('leaderboard', self.leaderboard))
        dp.add_handler(CommandHandler(['invite', 'contest'], self.contest))
        dp.add_handler(ChatMemberHandler(
            chat_member_types=ChatMemberHandler.ANY_CHAT_MEMBER, callback=self.member_updated))
        dp.add_handler(CallbackQueryHandler(self.challenger.captcha_callback, pattern="completed_([_a-zA-Z0-9-]*)"))
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
                print(f'Unauthorized access denied on {method.__name__}'
                      f'for {user_id} : {args[0].message.chat.username}.')
                args[0].message.reply_text('You do not have the required permissions to access this command')
                return None  # quit handling command
            return method(self_inner, *args, **kwargs)
        return inner

    @staticmethod
    def captcha_text(up: Update, ctx: CallbackContext):
        return f"Welcome {up.effective_user.name}, to Samari Finance ❤️\n" \
               f"To participate in the chat, a captcha is required.\nPress below to continue 👇"

