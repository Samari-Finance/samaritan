import logging
import os
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from core.commands import commands


class Samaritan:

    def __init__(self,
                 api_key_file: str = None,
                 log_level: logging = logging.INFO):
        self.setup(log_level=log_level)
        self.updater = Updater(token=self._read_api(api_key_file), use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.list_timer = datetime.now() - timedelta(minutes=10)
        self.add_handles()
        self.shillist_msg = None

    def start(self, update, context):
        self.send_message(update, context, text=commands['start'])

    def website(self, update, context):
        self.send_message(update, context, commands['website'])

    def chart(self, update, context):
        self.send_message(update, context, commands['chart'])

    def price(self, update, context):
        self.send_message(update, context, commands['price'])

    def mc(self, update, context):
        self.send_message(update, context, commands['mc'])

    def shill_list(self, update: Update, context: CallbackContext):
        now = datetime.now()
        if self.list_timer + timedelta(minutes=10) <= now:
            self.shillist_msg = self.send_message(update, context, commands['shillist'])
            self.list_timer = now
        else:
            self.send_message_markdown(
                update, context, text=self._prettify_reference(update, 'too_fast', self.shillist_msg.message_id.real))

    @staticmethod
    def _prettify_reference(update: Update, command, prev_msg):
        return f"{commands[command]}/{str(update.message.chat_id)[4:]}/{str(prev_msg)})"

    def shillin(self, update, context):
        self.send_message(update, context, commands['shillin'])

    def shill_reddit(self, update, context):
        self.send_message(update, context, commands['shillreddit'])

    def shill_telegram(self, update, context):
        self.send_message(update, context, commands['shilltelegram'])

    def shill_twitter(self, update, context):
        self.send_message(update, context, commands['shilltwitter'])

    @staticmethod
    def send_message(update, context: CallbackContext, text: str):
        return context.bot.send_message(chat_id=update.message.chat_id, text=text)

    @staticmethod
    def send_message_markdown(update, context: CallbackContext, text: str):
        return context.bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode='MarkdownV2')

    def start_polling(self):
        self.updater.start_polling()

    def add_handles(self):
        self.dispatcher.add_handler(CommandHandler('chart', self.chart))
        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(CommandHandler('commands', self.start))
        self.dispatcher.add_handler(CommandHandler('price', self.price))
        self.dispatcher.add_handler(CommandHandler('website', self.website))
        self.dispatcher.add_handler(CommandHandler('marketcap', self.mc))
        self.dispatcher.add_handler(CommandHandler('shill', self.shillin))
        self.dispatcher.add_handler(CommandHandler('shillin', self.shillin))
        self.dispatcher.add_handler(CommandHandler('shillreddit', self.shill_reddit))
        self.dispatcher.add_handler(CommandHandler('shillist', self.shill_list))
        self.dispatcher.add_handler(CommandHandler('shilltwitter', self.shill_reddit))
        self.dispatcher.add_handler(CommandHandler('shilltelegram', self.shill_telegram))
        self.dispatcher.add_handler(CommandHandler('shilltg', self.shill_telegram))


    @staticmethod
    def _format_link(prefix, chat_id, msg_id):
        return f"{prefix}/{chat_id}/{msg_id})"

    @staticmethod
    def setup(log_level):
        logging.basicConfig(level=log_level,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    @staticmethod
    def _read_api(api_key_file):
        if not os.path.exists(api_key_file):
            api_key_file = os.path.dirname(os.getcwd()) + '/' + api_key_file
        key_file = open(api_key_file)
        return key_file.read()
