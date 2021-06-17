"""
    Telegram bot for Samari.finance Telegram group using python-telegram-bot
    @ https://github.com/Samari-Finance/samaritan
    @ https://github.com/python-telegram-bot/python-telegram-bot

"""

import logging
from datetime import datetime
from functools import wraps
from typing import Callable, Union
from telegram import (
    Update,
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
    DEFAULT_NONE)

from core import *
from core.bitquery.graphcli import GraphQLClient
from core.captcha.challenger import Challenger
from core.default_commands import commands
from core.db.mongo_db import MongoConn
from core.samaritable import Samaritable
from core.utils.utils import (
    read_api,
    build_menu,
    send_message,
    regex_req,
    gen_captcha_request_deeplink,
    setup_log,
    log_entexit, fallback_user_id, fallback_chat_id, fallback_message_id)
from core.utils.utils_bot import (
    format_price,
    format_mc,
    gen_filter)


class Samaritan(Samaritable):

    def __init__(self,
                 tg_api_path: str = None,
                 db_api_path: str = None,
                 log_level: logging = logging.INFO):
        super().__init__()
        setup_log(log_level=log_level)
        self.updater = Updater(token=read_api(tg_api_path), use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.db = MongoConn(read_api(db_api_path))
        self.graphql = GraphQLClient()
        self.current_captchas = {}
        self.welcome = (Union[int, str], datetime)
        self.challenger = Challenger(self.db, self.current_captchas)
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
            else:
                raise KeyError('Unknown handler type: {}'.format(str(handler_type)))

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
                         text=self._format_reference(up, getattr(self, msg_str).message_id.real),
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

    @log_entexit
    def contest(self, up: Update, ctx: CallbackContext):
        user = up.effective_user
        chat_id = up.effective_chat.id
        link = self.db.get_invite_by_user_id(chat_id, user.id)
        if not link:
            link = ctx.bot.create_chat_invite_link(chat_id).invite_link
            self.db.set_invite_link_by_id(chat_id=chat_id, link=link, user_id=user.id)
        send_message(up, ctx,
                     reply=True,
                     text=f'Here is your personal invite link: {link}')

    @log_entexit
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

    @log_entexit
    def new_member(self, up: Update, ctx: CallbackContext):
        invite_link = up.chat_member.invite_link
        self.request_captcha(up, ctx)

        if invite_link:
            self.log.info('User has joined using invite link: {name: %s, link: %s}',
                          str(up.chat_member.new_chat_member.user.id),
                          str(invite_link.invite_link))
            link = invite_link.invite_link
            self.db.set_new_ref(up.effective_chat.id, link, up.chat_member.new_chat_member.user.id)

        ctx.bot.restrict_chat_member(chat_id=up.effective_chat.id,
                                     user_id=up.chat_member.new_chat_member.user.id,
                                     permissions=ChatPermissions(can_send_messages=False))

    @log_entexit
    def member_msg(self, up: Update, ctx: CallbackContext):
        ctx.bot.delete_message(fallback_chat_id(up), fallback_message_id(up))

    @log_entexit
    def left_member(self, up: Update, ctx: CallbackContext):
        self.db.remove_ref(chat_id=up.effective_chat.id, user_id=up.effective_user.id)
        self.db.set_captcha_status(chat_id=up.effective_chat.id, user_id=up.effective_user.id, status=False)

    @log_entexit
    def leaderboard(self, up: Update, ctx: CallbackContext):
        limit = 10
        counter = 1
        chat_id = up.effective_chat
        user_id = up.effective_user
        msg = f'🏆 INVITE CONTEST LEADERBOARD 🏆\n\n'
        scoreboard = sorted(self.db.get_members_pts(chat_id=chat_id), key=lambda i: i['pts'])

        try:
            if len(ctx.args) > 0:
                limit = int(ctx.args[0])
                if limit > 50:
                    limit = 50
            for member in scoreboard[:limit]:
                msg += f'{str(counter)+".":<3} {chat_id.get_member(member["id"]).user.name:<20} with {member["pts"]} {"pts"}\n' \

                counter += 1

            caller = next((x for x in scoreboard if x['id'] == user_id.id), None)
            if caller:
                msg += f'\nYour score: {scoreboard.index(caller)+1}. with {caller["pts"]:<3} {"pts"}'
            send_message(up, ctx, msg, disable_notification=True, reply=False)

        except ValueError:
            send_message(up, ctx, f'Invalid argument: {ctx.args} for leaderboard command')

    @log_entexit
    def price(self, up: Update, ctx: CallbackContext):
        price = self.graphql.fetch_price()
        text = self.db.get_text_by_handler('price')+format_price(price)
        send_message(up, ctx, text, parse_mode=MARKDOWN_V2)

    @log_entexit
    def mc(self, up: Update, ctx: CallbackContext):
        mc = self.graphql.fetch_mc()
        send_message(up, ctx, self.db.get_text_by_handler('mc')+format_mc(mc), parse_mode=MARKDOWN_V2)

    @log_entexit
    def evaluate_membership(self, new_member, old_member):
        old_status = old_member.status
        new_status = new_member.status
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
        elif new_status and not old_status:
            just_joined = True

        if just_joined:
            self.log.info('User has joined the chat: { name: %s, id: %s }',
                          str(new_member.user.name),
                          str(new_member.user.id))
        elif just_left:
            self.log.info('User has left the chat: { name: %s, id: %s }',
                          str(new_member.user.name),
                          str(new_member.user.id))
        return just_joined, just_left

    @log_entexit
    def request_captcha(self, up: Update, ctx: CallbackContext):
        url = gen_captcha_request_deeplink(up, ctx)
        button_list = [InlineKeyboardButton(text="👋 Click here for captcha 👋", url=url)]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        self.log.debug('Requesting captcha:{ deeplink=%s', url)
        msg = send_message(
            up=up,
            ctx=ctx,
            text=self.captcha_text(up, ctx),
            reply_markup=reply_markup)
        if not self.current_captchas.get(up.effective_user.id, None):
            self.current_captchas[fallback_user_id(up)] = {
                "pub_msg": msg,
                "attempts": 0}

    def start_polling(self):
        self.updater.start_polling(allowed_updates=[Update.ALL_TYPES, 'chat_member'])

    @log_entexit
    def add_handles(self, dp):
        dp.add_handler(MessageHandler(Filters.status_update.new_chat_members |
                                      Filters.status_update.left_chat_member, self.member_msg))
        dp.add_handler(ChatMemberHandler(
            chat_member_types=ChatMemberHandler.ANY_CHAT_MEMBER, callback=self.member_updated))
        dp.add_handler(CommandHandler('leaderboard', self.leaderboard))
        dp.add_handler(CommandHandler(['invite', 'contest'], self.contest))
        dp.add_handler(CommandHandler('price', self.price))
        dp.add_handler(CommandHandler('mc', self.mc))
        dp.add_handler(CommandHandler('start',
                                      self.challenger.captcha_deeplink,
                                      Filters.regex(r'captcha_([_a-zA-Z0-9-]*)'),
                                      pass_args=True))
        dp.add_handler(CallbackQueryHandler(self.challenger.captcha_callback, pattern="completed_([_a-zA-Z0-9-]*)"))
        self.add_dp_handlers(dp)

    @staticmethod
    def captcha_text(up: Update, ctx: CallbackContext):
        return f"Welcome {up.chat_member.new_chat_member.user.name}, to Samari Finance ❤️\n" \
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
    def _format_reference(update: Update, prev_msg):
        # todo use backend command instead
        return f"{commands['too_fast']['text']}/{str(update.message.chat_id)[4:]}/{str(prev_msg)})"
