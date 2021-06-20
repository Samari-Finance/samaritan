import logging


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
