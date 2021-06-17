import re

from telegram.ext import Filters


def format_mc(mc):
    return '_*' + f"{mc:,.2f}".replace('.', '\\.') + '*_'


def format_price(price):
    return '_*'+f"{price:.12f}".replace('.', '\\.')+'*_'


def gen_filter(aliases: list):
    """Generates a regex expression based on a list of aliases

    :param aliases: List of aliases to
    :return: regex expression which has
    """
    expr = Filters.regex(re.compile(aliases[0]+r'\??', re.IGNORECASE))
    for alias in aliases[1:]:
        expr = expr | Filters.regex(re.compile(alias+r'\??', re.IGNORECASE))
    return expr
