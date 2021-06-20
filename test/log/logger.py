import logging
from functools import wraps


def aggregate_logger(self):
    if self.__class__.__name__.lower() == 'samaritable' or self.__class__.__name__.lower() == 'samaritan':
        name = 'samaritan'
    else:
        name = 'samaritan.' + self.__class__.__name__.lower()
    log = logging.getLogger(self.__name__().lower())
    log.addFilter(DebugLogFilter())
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
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class DebugLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        print(record.msg)
        if (
                record.name.startswith('telegram') & (
                record.msg.startswith('Exiting: %s') |
                record.msg.startswith('Entering: %s') |
                record.msg.startswith('No new updates found') |
                (record.msg.startswith('[]') & len(record.msg) <= 3))
        ):
            return False
        return True
