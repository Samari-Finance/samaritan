import json
import os
from typing import List, Union, Optional

from telegram import Update, InlineKeyboardButton, ReplyMarkup
from telegram.ext import CallbackContext
from telegram.utils.helpers import DEFAULT_NONE

MARKDOWN_V2 = 'MarkdownV2'
HTML = 'html'


def read_api(api_key_file):
    if not os.path.exists(api_key_file):
        api_key_file = os.path.dirname(os.getcwd()) + '/' + api_key_file
    key_file = open(api_key_file)
    return key_file.read()


def pp_json(msg):
    json_str = json.loads(msg)
    print(json.dumps(json_str, indent=3))


def send_message(update: Update, context: CallbackContext, text: str, parse_mode=DEFAULT_NONE, reply=True,
                 disable_web_page_preview=DEFAULT_NONE, disable_notification=False, reply_markup=None):
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

def build_menu(
    buttons: List[InlineKeyboardButton],
    n_cols: int,
    header_buttons: Union[InlineKeyboardButton, List[InlineKeyboardButton]] = None,
    footer_buttons: Union[InlineKeyboardButton, List[InlineKeyboardButton]] = None
) -> List[List[InlineKeyboardButton]]:
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons if isinstance(header_buttons, list) else [header_buttons])
    if footer_buttons:
        menu.append(footer_buttons if isinstance(footer_buttons, list) else [footer_buttons])
    return menu
