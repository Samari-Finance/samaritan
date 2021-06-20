import logging

from samaritan.bot import Samaritan

if __name__ == '__main__':
    samaritan = Samaritan(log_level=logging.DEBUG,
                          tg_api_path='api_key',
                          db_api_path='mongo_api')
    samaritan.start_polling()
    samaritan.updater.idle()
