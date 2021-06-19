"""Samaritan
Copyright (C) 2021 Samari.finance

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
---------------------------------------------------------------------"""

import logging
import os
from functools import wraps
from io import BytesIO
from typing import List, Union

from PIL.Image import Image
from telegram import Update, InlineKeyboardButton, Message
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.utils.helpers import DEFAULT_NONE

from core import CAPTCHA_PREFIX, CALLBACK_DIVIDER, INVITE_PREFIX, LOUNGE_PREFIX

log = logging.getLogger('utils')


def send_message(up: Update, ctx: CallbackContext,
                 text: str,
                 chat_id: Union[str, int] = None,
                 message_id: Union[str, int] = None,
                 parse_mode=DEFAULT_NONE,
                 reply=True,
                 disable_web_page_preview=DEFAULT_NONE,
                 disable_notification=False,
                 reply_markup=None,
                 replace=False,
                 ) -> Message:
    """A wrapper around update.send_message

    :param up: Incoming telegram.Update
    :param ctx: Associated telegram.bot.CallbackContext
    :param chat_id: Chat to send message in. Uses fallback in case not present.
    :param message_id: Message id to provide. Uses fallback in case not present.
    :param text: String to send, must be at least 1 character
    :param parse_mode: Parse mode to send text, valid entries are 'html' or 'Markdown_v2'
    :param reply: If the outgoing message should be a reply
    :param disable_web_page_preview: Whether to enable or disable web previews
    :param disable_notification: Whether to send the outgoing message as a silent notification
    :param reply_markup: Markups to send with the text (keyboard, buttons etc.)
    :param replace: If the incoming update message should be deleted.

    :return: The outgoing telegram.Message instance.
    """
    if not chat_id:
        chat_id = fallback_chat_id(up)
    if not message_id:
       message_id = fallback_message_id(up)

    if replace:
        reply = False
        text = _append_tag(up, text)
        ctx.bot.delete_message(chat_id, message_id)

    reply_to_msg_id = None
    if reply:
        if message_id:
            reply_to_msg_id = message_id

    try:
        return ctx.bot.send_message(chat_id=chat_id,
                                    text=text,
                                    parse_mode=parse_mode,
                                    reply_to_message_id=reply_to_msg_id,
                                    disable_web_page_preview=disable_web_page_preview,
                                    disable_notification=disable_notification,
                                    reply_markup=reply_markup)
    except BadRequest as e:
        if e.message == 'Replied message not found':
            return ctx.bot.send_message(chat_id=chat_id,
                                        text=text,
                                        parse_mode=parse_mode,
                                        disable_web_page_preview=disable_web_page_preview,
                                        disable_notification=disable_notification,
                                        reply_markup=reply_markup)
        else:
            raise e


def send_image(up: Update, ctx: CallbackContext,
               img: Image,
               chat_id=None,
               caption: str = None,
               parse_mode=DEFAULT_NONE,
               reply=True,
               disable_notification=False,
               reply_markup=None,
               replace=False) -> Message:
    """Wrapper around telegram.bot.send_photo for convenience

    :param up: Incoming telegram.Update
    :param ctx: Associated telegram.bot.CallbackContext
    :param chat_id: ID of chat to send image in. If not provided, the incoming update's effective chat_id is used.
    :param img: Image to send
    :param caption: String to caption the image with
    :param parse_mode: Parse mode to send text, valid entries are 'html' or 'Markdown_v2'
    :param reply: Whether if the outgoing message should be a reply
    :param disable_notification: Whether to send the outgoing message as a silent notification
    :param reply_markup: Markups to send with the text (keyboard, buttons etc.)
    :param replace: If the incoming update message should be deleted.
    :return: The outgoing telegram.Message instance
    """
    if replace:
        reply = False
        caption = _append_tag(up, caption)
        ctx.bot.delete_message(fallback_chat_id(up), fallback_message_id(up))

    reply_to_msg_id = None
    if reply:
        if up.message is not None:
            reply_to_msg_id = up.message.message_id

    if not chat_id:
        chat_id = up.effective_chat.id

    if isinstance(img, Image):
        bio = BytesIO()
        bio.name = 'captcha.jpeg'
        img.save(bio, 'JPEG')
        bio.seek(0)
    else:
        bio = img

    return ctx.bot.send_photo(
        chat_id=chat_id,
        photo=bio,
        caption=caption,
        parse_mode=parse_mode,
        reply_to_message_id=reply_to_msg_id,
        disable_notification=disable_notification,
        reply_markup=reply_markup)


def fallback_user_id(up: Update):
    if up.effective_user.id:
        return int(up.effective_user.id)
    elif up.chat_member.new_chat_member.user.id:
        return int(up.chat_member.new_chat_member.user.id)
    elif up.message.from_user.id:
        return int(up.message.from_user.id)
    elif up.effective_message.from_user.id:
        return int(up.effective_message.from_user.id)


def fallback_chat_id(up: Update):
    if up.effective_chat.id:
        return int(up.effective_chat.id)
    elif up.chat_member.chat.id:
        return int(up.chat_member.chat.id)
    elif up.message.chat_id:
        return int(up.message.chat_id)


def fallback_message_id(up: Update):
    if up.message:
        return int(up.message.message_id)
    elif up.effective_message:
        return int(up.effective_message.message_id)


def _append_tag(up: Update, msg):
    return f"{up.effective_user.name} {msg}"


def read_api(api_key_file):
    """Searches project files for api key file

    :param api_key_file: File name to search for
    :return: Content of the read file.
    """
    if not os.path.exists(api_key_file):
        api_key_file = os.path.dirname(os.getcwd()) + '/' + api_key_file
    key_file = open(api_key_file)
    return key_file.read()


def build_menu(
        buttons: List[InlineKeyboardButton],
        n_cols: int,
        header_buttons: Union[InlineKeyboardButton, List[InlineKeyboardButton]] = None,
        footer_buttons: Union[InlineKeyboardButton, List[InlineKeyboardButton]] = None
) -> List[List[InlineKeyboardButton]]:
    """Easy button menu builder.

    :param buttons: Buttons to build.
    :param n_cols: number of columns
    :param header_buttons: Buttons to place at header placement
    :param footer_buttons: Buttons to place at footer placement
    :return: The assembled button menu
    """
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons if isinstance(header_buttons, list) else [header_buttons])
    if footer_buttons:
        menu.append(footer_buttons if isinstance(footer_buttons, list) else [footer_buttons])
    return menu


def gen_invite_request_deeplink(up: Update, ctx: CallbackContext):
    """Generates a new captcha request deeplink based on incoming Update and bot.CallbackContext
        :param up: Incoming telegram.Update
        :param ctx: CallbackContext for bot
        :return: Deeplink to private chat with bot for captcha request
        """
    chat_id = fallback_chat_id(up)

    deeplink = f'https://t.me/{ctx.bot.username}?start=' \
               f'{INVITE_PREFIX + CALLBACK_DIVIDER}' \
               f'{str(chat_id)}'
    log.debug('Invite deeplink: %s', deeplink)
    return deeplink


def gen_captcha_request_deeplink(up: Update, ctx: CallbackContext):
    """Generates a new captcha request deeplink based on incoming Update and bot.CallbackContext
    :param up: Incoming telegram.Update
    :param ctx: CallbackContext for bot
    :return: Deeplink to private chat with bot for captcha request
    """
    chat_id = up.effective_chat.id if up.effective_chat.id else up.message.chat_id

    deeplink = f'https://t.me/{ctx.bot.username}?start=' \
               f'{CAPTCHA_PREFIX + CALLBACK_DIVIDER}' \
               f'{str(chat_id)}'
    log.debug('Captcha deeplink: %s', deeplink)
    return deeplink


def gen_lounge_request_deeplink(up: Update, ctx: CallbackContext):
    """Generates a new lounge add bot to group deeplink based on incoming Update and bot.CallbackContext
    :param up: Incoming telegram.Update
    :param ctx: CallbackContext for bot
    :return: Deeplink to add bot to lounge chat
    """
    chat_id = up.effective_chat.id if up.effective_chat.id else up.message.chat_id

    deeplink = f'https://t.me/{ctx.bot.username}?startgroup=' \
               f'{LOUNGE_PREFIX + CALLBACK_DIVIDER}' \
               f'{str(chat_id)}'
    log.debug('Lounge deeplink: %s', deeplink)
    return deeplink


def regex_req(msg: Message, req_len=4):
    """Regex requirement for regex handlers.

    :param msg: telegram.Message instance to check for requirement fulfillment
    :param req_len: Max length of the incoming message text
    :return bool: Whether requirement is fulfilled.
    """
    return len(msg.text.split()) < req_len


def setup_log(log_level):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log_curr_captchas(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        self.log.debug('Current captchas: %s', str(self.current_captchas))
        return method(self, *args, **kwargs)
    return _impl


def log_entexit(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        self.log.debug('Entering: %s', method.__name__)
        tmp = method(self, *args, **kwargs)
        if tmp:
            self.log.debug('%s', tmp)
        self.log.debug('Exiting: %s', method.__name__)
        return tmp
    return _impl
