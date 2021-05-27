from core.bitquery import run_query


class GraphQLClient:

    def __init__(self):
        sama_addr = '0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be'

    @staticmethod
    def q_price():
        query = f"""
            query{{
                ethereum(network: bsc) {{
                    dexTrades(
                      options: {{limit: 1, desc: "block.height"}}
                      exchangeName: {{is: "Pancake v2"}}
                      baseCurrency: {{is: "0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be"}}
                    ) {{
                      transaction {{
                        hash
                      }}
                      smartContract {{
                        address {{
                          address
                        }}
                        contractType
                        currency {{
                          name
                        }}
                      }}
                      tradeIndex
                      date {{
                        date
                      }}
                      block {{
                        height
                      }}
                      buyAmount
                      buyAmountInUsd: buyAmount(in: USD)
                      buyCurrency {{
                        symbol
                        address
                      }}
                      sellAmount
                      sellAmountInUsd: sellAmount(in: USD)
                      sellCurrency {{
                        symbol
                        address
                      }}
                      sellAmountInUsd: sellAmount(in: USD)
                      tradeAmount(in: USD)
                      transaction {{
                        gasValue
                        gasPrice
                        gas
                      }}
                    }}
                  }}
                }}
            }}
        """
        return run_query(query)

