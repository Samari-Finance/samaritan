import json
import os
from io import BytesIO
from typing import List, Union

from telegram import Update, InlineKeyboardButton, Message
from telegram.ext import CallbackContext
from telegram.utils.helpers import DEFAULT_NONE


def send_message(update: Update, context: CallbackContext,
                 text: str,
                 parse_mode=DEFAULT_NONE,
                 reply=True,
                 disable_web_page_preview=DEFAULT_NONE,
                 disable_notification=False,
                 reply_markup=None) -> Message:
    """A wrapper around update.send_message

    :param update: incoming telegram.Update.
    Required.
    :param context: associated telegram.bot.CallbackContext.
    Required.
    :param text: string to send, must be at least 1 character.
    Required.
    :param parse_mode: parse mode to send text, valid entries are 'html' or 'Markdown_v2'.
    Default: None
    :param reply: if the outgoing message should be a reply.
    Default: True
    :param disable_web_page_preview: whether to enable or disable web previews.
    Default: None or False.
    :param disable_notification: whether to send the outgoing message as a silent notification.
    Default: True.
    :param reply_markup: Markups to send with the text (keyboard, buttons etc.)
    Default: None

    :return: The outgoing telegram.Message instance.
    """
    reply_to_msg_id = None
    if reply:
        if update.message is not None:
            reply_to_msg_id = update.message.message_id

    return context.bot.send_message(chat_id=update.effective_chat.id,
                                    text=text,
                                    parse_mode=parse_mode,
                                    reply_to_message_id=reply_to_msg_id,
                                    disable_web_page_preview=disable_web_page_preview,
                                    disable_notification=disable_notification,
                                    reply_markup=reply_markup)


def send_image(up: Update, ctx: CallbackContext,
               img,
               caption: str = None,
               parse_mode=DEFAULT_NONE,
               reply=True,
               disable_web_page_preview=DEFAULT_NONE,
               disable_notification=False,
               reply_markup=None) -> Message:
    """Wrapper around telegram.bot.send_photo

    :param up: incoming telegram.Update
    Required.
    :param ctx: associated telegram.bot.CallbackContext
    :param img: Image to send.
    Required.
    :param caption: string to caption the image with.
    Default: None.
    :param parse_mode: parse mode to send text, valid entries are 'html' or 'Markdown_v2'.
    Default: None
    :param reply: whether if the outgoing message should be a reply.
    Default: True
    :param disable_web_page_preview: whether to enable or disable web previews.
    Default: None or False.
    :param disable_notification: whether to send the outgoing message as a silent notification.
    Default: True.
    :param reply_markup: Markups to send with the text (keyboard, buttons etc.)
    Default: None
    :return: returns the outgoing telegram.Message instance.
    """
    reply_to_msg_id = None
    if reply:
        if up.message is not None:
            reply_to_msg_id = up.message.message_id

    bio = BytesIO()
    bio.name = 'captcha.jpeg'
    img.save(bio, 'JPEG')
    bio.seek(0)

    return ctx.bot.sendPhoto(
        chat_id=up.effective_chat.id,
        photo=bio,
        caption=caption,
        parse_mode=parse_mode,
        reply_to_message_id=reply_to_msg_id,
        disable_notification=disable_notification,
        reply_markup=reply_markup)


def read_api(api_key_file):
    """Searches project files for api key file

    :param api_key_file: file name to search for

    :return: content of the read file.
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
    :param header_buttons: button to place at header placement
    Default: None
    :param footer_buttons: button to place at footer placement
    Default: None

    :return: the assembled button menu
    """
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons if isinstance(header_buttons, list) else [header_buttons])
    if footer_buttons:
        menu.append(footer_buttons if isinstance(footer_buttons, list) else [footer_buttons])
    return menu


def gen_captcha_request_deeplink(up: Update, ctx: CallbackContext):
    return f'https://t.me/{ctx.bot.username}?start=captcha_{str(up.effective_chat.id)}'


def regex_req(msg: Message, req_len=4):
    """Regex requirement for regex handlers

    :param msg: telegram.Message instance to check for requirement fulfillment.
    :param req_len: max length of the incoming message text.
    Default: 4

    :return bool: whether requirements is fulfilled.
    """
    return len(msg.text.split()) < req_len


def pp_json(msg):
    """Pretty-printing json formatted strings.

    :param msg: json-string to pretty print

    :return: None
    """
    json_str = json.loads(msg)
    print(json.dumps(json_str, indent=3))

