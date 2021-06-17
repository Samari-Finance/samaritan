from pprint import pprint
from statistics import mean

from core.bitquery import run_query
from core.samaritable import Samaritable
from core.utils.utils import log_entexit


class GraphQLClient(Samaritable):

    def __init__(self):
        super().__init__()
        self.sama_addr = '0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be'

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

        print(prices)

        return mean(prices)

    @log_entexit
    def fetch_mc(self):
        return self.fetch_price() * 1273628335437

    @log_entexit
    def is_buy(self, trade):
        return trade['buyCurrency']['symbol'] == 'SAMA'

    @log_entexit
    def _dex_trades(self, path: dict):
        return path['data']['ethereum']['dexTrades']


