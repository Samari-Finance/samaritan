import logging
from functools import wraps


def aggregate_logger(self):
    log = logging.getLogger(self.__name__().lower())
    log.addHandler(logging.StreamHandler())
    return log


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


def setup_log(log_level):
    tg_log = logging.getLogger('telegram.bot')
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger('telegram.bot').addFilter(PyTGBotLogFilter())


class PyTGBotLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if (
                record.getMessage().startswith('Exiting: get_updates') |
                record.getMessage().startswith('Entering: get_updates') |
                record.getMessage().startswith('No new updates found') |
                (record.getMessage().startswith('[]') & len(record.getMessage()) <= 3)
        ):
            return False
        return True

