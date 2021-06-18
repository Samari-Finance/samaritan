"""
    Telegram bot for Samari.finance Telegram group using python-telegram-bot
    @ https://github.com/Samari-Finance/samaritan
    @ https://github.com/python-telegram-bot/python-telegram-bot

"""

import logging
from datetime import datetime
from typing import Callable, Union
from telegram import (
    Update,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ChatMemberHandler,
    MessageHandler,
    Filters,
)
from telegram.utils.helpers import (
    DEFAULT_NONE)

from core import *
from core.bitquery.graphcli import GraphQLClient
from core.captcha.challenger import Challenger
from core.contest.contestor import Contestor
from core.contest.inviter import Inviter
from core.db.mongo_db import MongoConn
from core.samaritable import Samaritable
from core.utils.utils import (
    read_api,
    send_message,
    regex_req,
    setup_log,
    log_entexit,
    fallback_user_id,
    fallback_chat_id,
    fallback_message_id)
from core.utils.utils_bot import (
    gen_filter)


class Samaritan(Samaritable):

    def __init__(self,
                 tg_api_path: str = None,
                 db_api_path: str = None,
                 log_level: logging = logging.INFO):
        self.db = MongoConn(read_api(db_api_path))
        self.updater = Updater(token=read_api(tg_api_path), use_context=True)
        self.dispatcher = self.updater.dispatcher
        super().__init__(self.db)
        setup_log(log_level=log_level)
        self.graphql = GraphQLClient(self.db)
        self.current_captchas = {}
        self.welcome = (Union[int, str], datetime)
        self.challenger = Challenger(self.db, self.current_captchas)
        self.inviter = Inviter(self.db)
        self.contestor = Contestor(self.db)
        self.add_handlers(self.dispatcher)

    def gen_handler_attr(self):
        """Generates all handlers, based on their attributes in db.
        :return:
        """
        for key in self.db.default_handlers.find():
            if key.get('regex'):
                #  If the handler has regexes, create these as well
                _handle = self.gen_handler(key, REGEX)
                setattr(self, self.get_handler_name(key, REGEX), _handle)
            _handle = self.gen_handler(key)
            setattr(self, self.get_handler_name(key), _handle)

    def gen_handler(self, handler_attr: dict, handler_type=None) -> Callable:
        """Generates a handler, based on the given attributes.

        :param handler_attr: attributes of the handler to generate
        :param handler_type: if specified, will generate this type, if not uses type specified in the attributes
        :return: the generated handler method
        """
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
        """Generates a simple send message method for a CommandHandler.

        :param up: incoming telegram.Update
        :param ctx: context for bot
        :param attributes: handler attributes
        :return: the outgoing telegram.Message object
        """
        return send_message(up, ctx,
                            text=attributes['text'],
                            reply=attributes.get('reply', False),
                            replace=attributes.get('replace', False),
                            parse_mode=attributes.get('parse_mode', DEFAULT_NONE),
                            disable_notification=attributes.get('disable_notification', False),
                            disable_web_page_preview=attributes.get('disable_web_preview', DEFAULT_NONE))

    def gen_timed_handler(self, up: Update, ctx: CallbackContext, attributes: dict):
        """Generates a timed handler, which will send the message, if the timeout window has not been passed,
        otherwise sends a reference to the previous message. Useful if some commands' text take up too much space in the
        chat.

        :param up: incoming telegram.Update
        :param ctx: context for bot
        :param attributes: handler attributes
        :return: None
        """
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
        """Generates a regex handler.

        :param up: incoming telegram.Update
        :param ctx: context for bot
        :param attributes: handler attributes
        :return: None
        """
        if regex_req(up.message):
            if attributes['type'] == REGEX:
                getattr(self, self.get_handler_name(attributes))(up, ctx)
            else:
                getattr(self, self.get_handler_name(attributes, COMMAND))(up, ctx)

    def add_dp_handlers(self, dp):
        """Adds all applicable handlers to the dispatcher. First calls to generate them, then adds them, using their
        respective methods, based on what type they are.

        :param dp: dispatcher to add the handlers to
        :return: None
        """
        self.gen_handler_attr()
        for key in self.db.default_handlers.find():
            handler_type = key['type']
            if handler_type not in [COMMAND, TIMED, REGEX]:
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
        self.challenger.request_captcha(up, ctx)

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
        chat_id = fallback_chat_id(up)
        user_id = fallback_user_id(up)
        self.db.remove_ref(chat_id=chat_id, user_id=user_id)
        self.db.set_captcha_status(chat_id=chat_id, user_id=user_id, status=False)

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

    def start_polling(self):
        self.updater.start_polling(allowed_updates=[Update.ALL_TYPES, 'chat_member'])

    @staticmethod
    def get_handler_name(attributes: dict, handler_type=None):
        handler_type = handler_type if handler_type else attributes['type']
        name = f"_handler_{attributes['_id']}_{handler_type}"
        return name

    @log_entexit
    def add_handlers(self, dp):
        dp.add_handler(MessageHandler(Filters.status_update.new_chat_members |
                                      Filters.status_update.left_chat_member, self.member_msg))
        dp.add_handler(ChatMemberHandler(
            chat_member_types=ChatMemberHandler.ANY_CHAT_MEMBER, callback=self.member_updated))
        self.challenger.add_handlers(dp)
        self.inviter.add_handlers(dp)
        self.contestor.add_handlers(dp)
        self.graphql.add_handlers(dp)
        self.add_dp_handlers(dp)

    def _format_reference(self, update: Update, prev_msg):
        return f"{self.db.get_text_by_handler('too_fast')}/{str(update.message.chat_id)[4:]}/{str(prev_msg)})"
