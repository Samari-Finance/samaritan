import logging
from functools import wraps


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
        if (
                record.msg.startswith('Exiting: get_updates') or
                record.msg.startswith('Entering: get_updates') or
                record.msg.startswith('No new updates found.') or
                (record.msg.startswith('[]') and len(record.msg) <= 3)
        ):
            return False
        return True
