"""Samaritan
Copyright (C) 2021 Samari.finance

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
---------------------------------------------------------------------"""

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
