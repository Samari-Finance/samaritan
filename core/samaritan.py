"""
    Telegram bot for Samari.finance Telegram group using python-telegram-bot
    @ https://github.com/python-telegram-bot/python-telegram-bot

"""

import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable

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
    LEFT, KICKED, RESTRICTED, MEMBER, ADMIN, CREATOR, REGEX, COMMAND, TIMED, CAPTCHA, UTIL
)
from core.captcha.challenger import Challenger
from core.default_commands import commands
from core.db.mongo_db import MongoConn
from core.utils.test import dump_obj
from core.utils.utils import (
    read_api,
    build_menu,
    send_message,
    regex_req,
    gen_captcha_request_deeplink, gen_filter
)


class Samaritan:

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

    def gen_handler_attr(self):
        for key in self.db.default_handlers.find():
            if key.get('regex'):
                _handle = self.gen_handler(key, REGEX)
                setattr(self, self.get_handler_name(key, REGEX), _handle)
            _handle = self.gen_handler(key)
            setattr(self, self.get_handler_name(key), _handle)

    def gen_handler(self, handler_attr: dict, handler_type=None) -> Callable:
        handler_type = handler_type if handler_type else handler_attr['type']

        def handler(update, context):
            if COMMAND == handler_type:
                return self.gen_command_handler(update, context, handler_attr)
            elif TIMED == handler_type:
                return self.gen_timed_handler(update, context, handler_attr)
            elif REGEX == handler_type:
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
            if attributes['type'] == REGEX:
                getattr(self, self.get_handler_name(attributes))(up, ctx)
            else:
                getattr(self, self.get_handler_name(attributes, COMMAND))(up, ctx)

    def add_dp_handlers(self, dp):
        self.gen_handler_attr()
        for key in self.db.default_handlers.find():
            handler_type = key['type']
            if handler_type == UTIL or handler_type == CAPTCHA:
                continue
            elif handler_type == COMMAND or handler_type == TIMED:
                self.add_command_handler(dp, key)
                if key.get('regex'):
                    self.add_regex_handler(dp, key, key['regex'])
            elif handler_type == REGEX:
                self.add_regex_handler(dp, key)

    def add_command_handler(self, dp, key):
        dp.add_handler(CommandHandler(key['aliases'], getattr(self, self.get_handler_name(key))))

    def add_regex_handler(self, dp, key, aliases=None):
        aliases = aliases if aliases else key['aliases']
        dp.add_handler(MessageHandler(gen_filter(aliases), getattr(self, self.get_handler_name(key, REGEX))))

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
            new_member = update.chat_member.new_chat_member
            old_member = update.chat_member.old_chat_member
            if self.evaluate_membership(new_member, old_member)[1]:
                self.left_member(update, context)
            elif self.evaluate_membership(new_member, old_member)[0]:
                self.new_member(update, context)
        elif update.chat_member.new_chat_member and not update.chat_member.old_chat_member:
            self.new_member(update, context)

    def new_member(self, update: Update, context: CallbackContext):
        context.bot.restrict_chat_member(chat_id=update.effective_chat.id,
                                         user_id=update.chat_member.new_chat_member.user.id,
                                         permissions=ChatPermissions(can_send_messages=False))
        self.request_captcha(update, context)

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
        url = gen_captcha_request_deeplink(up, ctx)
        button_list = [InlineKeyboardButton(text="👋 Click here for captcha 👋", url=url)]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        send_message(
            text=self.captcha_text(up, ctx),
            reply_markup=reply_markup,
            update=up,
            context=ctx)

    def start_polling(self):
        self.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    def add_handles(self, dp):
        dp.add_handler(CommandHandler('start',
                                      self.challenger.captcha_deeplink,
                                      Filters.regex(r'captcha_([a-zA-Z0-9]*)'),
                                      pass_args=True))
        dp.add_handler(CommandHandler('leaderboard', self.leaderboard))
        dp.add_handler(CommandHandler(['invite', 'contest'], self.contest))
        dp.add_handler(ChatMemberHandler(
            chat_member_types=ChatMemberHandler.ANY_CHAT_MEMBER, callback=self.member_updated))
        dp.add_handler(CallbackQueryHandler(self.challenger.captcha_callback, pattern="completed_([_a-zA-Z0-9-]*)"))
        self.add_dp_handlers(dp)
        dump_obj(self)

    @staticmethod
    def captcha_text(up: Update, ctx: CallbackContext):
        return f"Welcome {up.effective_user.name}, to Samari Finance ❤️\n" \
               f"To participate in the chat, a captcha is required.\nPress below to continue 👇"

    @staticmethod
    def get_handler_name(attributes: dict, handler_type=None):
        handler_type = handler_type if handler_type else attributes['type']
        name = f"_handler_{attributes['_id']}_{handler_type}"
        return name

    def _wrap_method(self, method):  # Wrapper called in case of a method
        @wraps(method)
        def inner(self_inner, *args, **kwargs):
            user_id = args[0].effective_user.id  # args[0]: update
            if user_id not in self.db.get_admins:
                print(f'Unauthorized access denied on {method.__name__}'
                      f'for {user_id} : {args[0].message.chat.username}.')
                args[0].message.reply_text('You do not have the required permissions to access this command')
                return None  # quit handling command
            return method(self_inner, *args, **kwargs)
        return inner

    @staticmethod
    def _prettify_reference(update: Update, prev_msg):
        return f"{commands['too_fast']['text']}/{str(update.message.chat_id)[4:]}/{str(prev_msg)})"


def setup_log(log_level):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
