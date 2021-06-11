from pprint import pprint

from core.bitquery import run_query


class GraphQLClient:

    def __init__(self,
                 api_key_path: str = None):
        self.sama_addr = '0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be'

    def q_price(self) -> dict:
        query = """
            query{
  ethereum(network: bsc) {
    dexTrades(
      options: {limit: 1, desc: "block.height"}
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


