import json
import os
from io import BytesIO
from typing import List, Union

from PIL.Image import Image
from telegram import Update, InlineKeyboardButton, Message
from telegram.ext import CallbackContext
from telegram.utils.helpers import DEFAULT_NONE

from core import CAPTCHA_PREFIX, CALLBACK_DIVIDER
from core.captcha.challenge import Challenge


def send_message(update: Update, context: CallbackContext,
                 text: str,
                 chat_id=None,
                 parse_mode=DEFAULT_NONE,
                 reply=True,
                 disable_web_page_preview=DEFAULT_NONE,
                 disable_notification=False,
                 reply_markup=None,
                 ) -> Message:
    """A wrapper around update.send_message

    :param chat_id: Chat to send message in
    :param update: Incoming telegram.Update
    :param context: Associated telegram.bot.CallbackContext
    :param text: String to send, must be at least 1 character
    :param parse_mode: Parse mode to send text, valid entries are 'html' or 'Markdown_v2'
    :param reply: If the outgoing message should be a reply
    :param disable_web_page_preview: Whether to enable or disable web previews
    :param disable_notification: Whether to send the outgoing message as a silent notification
    :param reply_markup: Markups to send with the text (keyboard, buttons etc.)

    :return: The outgoing telegram.Message instance.
    """
    reply_to_msg_id = None
    if reply:
        if update.message is not None:
            reply_to_msg_id = update.message.message_id

    if not chat_id:
        chat_id = update.effective_chat.id

    return context.bot.send_message(chat_id=chat_id,
                                    text=text,
                                    parse_mode=parse_mode,
                                    reply_to_message_id=reply_to_msg_id,
                                    disable_web_page_preview=disable_web_page_preview,
                                    disable_notification=disable_notification,
                                    reply_markup=reply_markup)


def send_image(up: Update, ctx: CallbackContext,
               img: Image,
               chat_id=None,
               caption: str = None,
               parse_mode=DEFAULT_NONE,
               reply=True,
               disable_notification=False,
               reply_markup=None) -> Message:
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
    :return: The outgoing telegram.Message instance
    """
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


def gen_captcha_request_deeplink(up: Update, ctx: CallbackContext):
    """Generates a new captcha request deeplink based on incoming Update and bot.CallbackContext
    :param up: Incoming telegram.Update
    :param ctx: CallbackContext for bot
    :return: Deeplink to private chat with bot for captcha request
    """
    deeplink = f'https://t.me/{ctx.bot.username}?start=' \
               f'{CAPTCHA_PREFIX+CALLBACK_DIVIDER}' \
               f'{str(up.effective_chat.id)+CALLBACK_DIVIDER}' \
               f'{str(up.chat_member.new_chat_member.user.id)}'
    print(f'deeplink: {deeplink}')
    return deeplink


def regex_req(msg: Message, req_len=4):
    """Regex requirement for regex handlers.

    :param msg: telegram.Message instance to check for requirement fulfillment
    :param req_len: Max length of the incoming message text
    :return bool: Whether requirement is fulfilled.
    """
    return len(msg.text.split()) < req_len


def pp_json(msg):
    """Pretty-printing json formatted strings.

    :param msg: Json-string to pretty print
    :return: None
    """
    json_str = json.loads(msg)
    print(json.dumps(json_str, indent=3))

