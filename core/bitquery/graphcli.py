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

from statistics import mean

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from core import MARKDOWN_V2
from core.bitquery import run_query
from core.db import MongoConn
from core.samaritable import Samaritable
from core.utils.utils import log_entexit, send_message
from core.utils.utils_bot import format_price, format_mc


class GraphQLClient(Samaritable):

    def __init__(self,
                 db: MongoConn):
        super().__init__(db)
        self.sama_addr = '0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be'

    @log_entexit
    def price(self, up: Update, ctx: CallbackContext):
        price = self.fetch_price()
        text = self.db.get_text_by_handler('price') + format_price(price)
        send_message(up, ctx, text, parse_mode=MARKDOWN_V2)

    @log_entexit
    def mc(self, up: Update, ctx: CallbackContext):
        mc = self.fetch_mc()
        send_message(up, ctx, self.db.get_text_by_handler('mc') + format_mc(mc), parse_mode=MARKDOWN_V2)

    @log_entexit
    def fetch_price(self):
        prices = []
        response = self.q_price()
        for trade in self._dex_trades(response):
            if self.is_buy(trade):
                buy_amount = trade['buyAmount']
                sell_amount_usd = trade['sellAmountInUsd']
                prices.append(sell_amount_usd / buy_amount)
            else:
                buy_amount_usd = trade['buyAmountInUsd']
                sell_amount = trade['sellAmount']
                prices.append(buy_amount_usd / sell_amount)

        return mean(prices)

    @log_entexit
    def fetch_mc(self):
        return self.fetch_price() * 1273628335437

    @log_entexit
    def q_price(self) -> dict:
        query = """
            query{
  ethereum(network: bsc) {
    dexTrades(
      options: {limit: 10, desc: "block.height"}
      exchangeName: {is: "Pancake v2"}
      baseCurrency: {is: "%s"}
    ) {
      transaction {
        hash
      }
      smartContract {
        address {
          address
        }
        contractType
        currency {
          name
        }
      }
      tradeIndex
      date {
        date
      }
      block {
        height
      }
      buyAmount
      buyAmountInUsd: buyAmount(in: USD)
      buyCurrency {
        symbol
        address
      }
      sellAmount
      sellAmountInUsd: sellAmount(in: USD)
      sellCurrency {
        symbol
        address
      }
      sellAmountInUsd: sellAmount(in: USD)
      tradeAmount(in: USD)
      transaction {
        gasValue
        gasPrice
        gas
      }
    }
  }
}
        """ % self.sama_addr
        return run_query(query)

    def add_handlers(self, dp):
        dp.add_handler(CommandHandler('price', self.price))
        dp.add_handler(CommandHandler('mc', self.mc))

    @log_entexit
    def is_buy(self, trade):
        return trade['buyCurrency']['symbol'] == 'SAMA'

    @log_entexit
    def _dex_trades(self, path: dict):
        return path['data']['ethereum']['dexTrades']
