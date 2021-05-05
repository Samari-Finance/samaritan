import logging

from core import Samaritan

if __name__ == '__main__':
    samaritan = Samaritan(log_level=logging.INFO, api_key_file='api_key')
    samaritan.start_polling()
    samaritan.updater.idle()
