"""Samaritan
Copyright (C) 2021 Samari.finance

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
---------------------------------------------------------------------"""

from datetime import timedelta

from samaritan import MARKDOWN_V2

shilltg = '🌜 Samari is about to EXPLODE! 🌛\n' \
          'While charity alone is great, development focused on bringing utility will in the long run cause more ' \
          'donations. At Samari we want to bring all the aspects of DEFI under one umbrella' \
          ', to provide people and animals in need a better future\n' \
          'TELEGRAM & Twitter contests starting soon with prizes determined by CONTRACT FEES, ' \
          'together with a 10 day campaign with KSI VIDEO EDITOR: MO SYED\n' \
          'WebsiteV2 coming up as well. 5M MC = KSI Shoutout. You don\'t want to miss this\n\n' \
          'Join the SAMARITANS on TG \n\n' \
          'TELEGRAM: t.me/SamariFinance\n' \
          'WEBSITE: Samari.finance\n\n' \
          '👉 Team doxxed\n' \
          '👉 Active community\n' \
          '👉 Charitable Organization\n' \
          '👉 Marketing Strategy\n' \
          '👉 $100K MC at launch – stable liquidity, no p&d scheme\n' \
          '👉 Sustainable tokenomics\n\n' \
          '💰 BUY $Samari (V2): https://exchange.pancakeswap.finance/#/swap?outputCurrency=0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be\n' \
          '📈 CHART (V2): https://poocoin.app/tokens/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be\n' \
          '🔒 LIQUIDITY Locked: https://dxsale.app/app/pages/dxlockview?id=0&add\n' \
          '✅ VERIFIED CONTRACT: https://bscscan.com/token/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be\n'
shillreddit = 'Samari finance | Charity platform, 1k holders, devs are doxxed\n' \
              'Welcome Samaritans!\n' \
              '🏵 What is Samari?\n' \
              '$SAMA is a deflationary, community-powered charitable organization. Samari offers a yield generating protocol' \
              ' – by holding' \
              'The 3% redistribution fee allows for passive income, which means,' \
              'the more you hold, the more you shall receive! This is accomplished by charging a 10% tax on all transactions, ' \
              'from which 3% are redistributed to existing holders, 2% is added to the charity wallet, 1% to the marketing wallet' \
              'and 5% to the liquidity pool, creating price support and stability.\n\n' \
              'What is the utility of $SAMA?\n' \
              'Philanthropy is for the public good, focusing on quality of life. We – the community - wish to make a difference ' \
              'where it really counts by donating to local small charitable organizations, where bureaucracy doesn’t consume ' \
              'most resources. Whether it be for animal shelters, the global pandemic ongoing crisis, planet earth ' \
              'or an entirely different matter ' \
              'that could use a helping hand, we do not limit ourselves to a specific cause. The community will have their say in' \
              'this with the weighted voting system. Together the Samaritans can make a difference! ' \
              '$SAMA’s charity wallet is designed as such, that each % transaction fee is immediately liquidated to BNB, ' \
              'refraining from any sudden dumps by selling out from the charity wallet. The wallet will be locked ' \
              'for 2 weeks at a time. Once unlocked, the profits in BNB will be donated to a desired organization ' \
              'determined by the community.\n\n' \
              '💸 Tokenomics:\n' \
              '10% Tax\n• 5% to the liquidity pool\n• 3% redistribution to existing holders\n' \
              '• 2% to the charity wallet\n• 1% to the marketing wallet' \
              'Burn: 5%\nTeam: 20%\nPancakeSwap LP: 75%\nTotal Supply: 1,273,628,335,437\n' \
              '\n⚖️ Anti-Whale Tokenomics:\n' \
              'Each wallet can at max only sell 1% of total supply in a timeframe of 3 hours\n' \
              '\n🌐 Team & Community:\n' \
              'The team consists of five members, that compliment one another’s skill sets in terms of development, marketing,' \
              ' and legal entities. Three members have doxxed themselves, with personal information' \
              ' (Facebook, LinkedIn) and pictures widely available, and that are working full time on this project.' \
              ' The remaining two members are not dismissive of this but are currently reluctant due to work' \
              ' and legal matters. The telegram currently consists of a very active, involved community of 300 members,' \
              ' that is rapidly growing.\n' \
              '\n💰 Wallet addresses:\n' \
              'Charity & Marketing contract: https://bscscan.com/address/0xf56846f6a95ef3ab07b048940df054b5eb842ca1\n' \
              'Team & Burn: https://bscscan.com/token/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be?a=0x2d045410f002a95efcee67759a92518fa3fce677\n' \
              '\n▶️ LINKS:\n🧿 Contract Address: https://bscscan.com/address/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be\n' \
              '🌍 Website: https://Samari.finance\n' \
              '📱 Telegram: t.me/SamariFinance\n' \
              '🕊️ Twitter: twitter.com/SamariFinance\n' \
              '🥞 PancakeSwap: https://exchange.pancakeswap.finance/#/swap?outputCurrency=0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be \n' \
              '💩 PooCoin: https://poocoin.app/tokens/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be\n'
commands = {
    "start": {'text': 'Heya, I\'m your local Samaritan ❤️ \nAvailable commands:\n'
                      '\nGeneral:\n'
                      '/commands - list of all commands\n'
                      '/website - Samari.finance\n'
                      '/chart - Poocoin chart\n'
                      '/price - current price on PancakeSwap\n'
                      '/marketcap or /mc - current marketcap of $SAMA\n'
                      '\nShilling:\n'
                      '/shillist - list of places to shill\n'
                      '/shill or /shillin - templates for shilling on different platforms\n'
                      '/shillreddit - template for reddit shill\n'
                      '/shilltelegram or /shilltg - template for shill on Telegram\n'
                      '/shilltwitter - template for twitter shill\n',
              'type': 'command',
              'aliases': ['start', 'help']},
    "website": {'text': '[Samari\\.finance](https://Samari.finance)',
                'regex': ['website'],
                'type': 'command',
                'parse_mode': MARKDOWN_V2},
    "contract": {'text': 'https://bscscan.com/address/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be',
                 'disable_web_page_preview': True,
                 'regex': ['contract', 'sc']},
    "socials": {'text': '🌐 Website: https://Samari.finance\n'
                        '🐦 Twitter: https://twitter.com/SamariFinance\n'
                        '📱 Telegram: https://t.me/SamariFinanec\n'
                        '🎮 Discord: https://discord.gg/557bPEUB\n'},
    "chart": {'text': 'https://poocoin.app/tokens/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be',
              'regex': ['chart']},
    "trade": {'text': 'https://exchange.pancakeswap.finance/#/swap?outputCurrency'
                      '=0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be',
              'regex': ['pcs', 'pancakeswap'],
              'aliases': ['trade', 'buy']},
    "price": {'text': '🚀 Current price of $SAMA is: $',
              'type': 'util'},
    "mc": {'text': '🚀 Current market cap of $SAMA is: $',
           'type': 'util',
           'aliases': ['mc', 'marketcap']},
    "shillist": {'text': '\n@uniswaptalk\n@gemcollectors\n@cryptoM00NShots\n@gemdiscussion\n@gemtalkc\n@rocketmangem'
                          '\n@dexgemschat\n@moonhunters\n@uniswapresearch\n@infinitygainzz\n@InfinityBotz'
                          '\n@tehMoonwalkeRs\n@uniswaplegit\n@uniswapgemtargets\n@acmecrypto\n@cryptomindsgroup'
                          '\n@oddgemsfamilia\n@thegemhunterstg\n@GoodFellas_Cryptopicks\n@BitSquad\n@themoonboyschat'
                          '\n@Farmingroom\n@uniswapgemspumpz\n@Pumpchads\n@BitSquad\n@WhalersClub101\n@uniswapresearch'
                          '\n@Uniswapelite\n@uniswapone\n@Uniswapchina\n@UniswapOTCexchange\n@shitcoincz'
                          '\n@gemcollectors\n@Satoshi_club\n@gemcollectors\n@shitcoincz\n@CryptoVIPSignalTA'
                          '\n@uniswap_gem_alerts\n@mrsjenny\n@binancedextrading\n@Cryptosupportservices\n@uniswapgem123'
                          '\n@DeFiRaccoons\n@uniswapunofficial\n@CryptoFamilyGroup\n@CryproPriceTalks'
                          '\n@UniswapEarlyCalls\n@elliotradescrypto\n@TradeCoinUnderGround\n@uniswapgemsv2\n@DevoToken'
                          '\n@gemsfordegensgroup\n@uniswaptalk\n@crypto_revolution1\n\nHere is your shill list'
                          '\n@BitSquad\n@WhalersClub101\n@uniswapresearch\n@Uniswapelite\n@uniswapone\n@Uniswapchina'
                          '\n@UniswapOTCexchange\n@shitcoincz\n@gemcollectors\n@Satoshi_club\n@gemcollectors'
                          '\n@shitcoincz\n@CryptoVIPSignalTA\n@uniswap_gem_alerts\n@binancedextrading'
                          '\n@Cryptosupportservices\n@uniswapgem123\n@DeFiRaccoons\n@uniswapunofficial'
                          '\n@CryptoFamilyGroup\n@cryptopricetalks\n@UniswapEarlyCalls\n@elliotradescrypto'
                          '\n@TradeCoinUnderGround\n\nHere\'s the complete list of Telegram channels for shilling:'
                          '\n@illuminatiGem\n@overdose_gems_group\n@SuicidalPumpGroup\n@elliotradescrypto'
                          '\n@dexgemschat\n@GemSnipers\n@uniswapgemspumpz\n@defisearch\n@InfinityGainzz\n@gemcollectors'
                          '\n@cryptodakurobinhooders\n@moonhunters\n@unigemchatz\n@supergemhunter\n@themoonboyschat'
                          '\n@UniswapGemGroup\n@Uniswap_Gem_Dicuss\n@jumpsquad\n@BitSquad\n@WhalersClub101'
                          '\n@uniswapresearch\n@Uniswapelite\n@uniswapone\n@Uniswapchina\n@UniswapOTCexchange'
                          '\n@shitcoincz\n@Satoshi_club\n@CryptoVIPSignalTA\n@uniswap_gem_alerts\n@mrsjenny'
                          '\n@binancedextrading\n@Cryptosupportservices\n@uniswapgem123\n@DeFiRaccoons'
                          '\n@uniswapunofficial''\n@CryptoFamilyGroup\n@CryproPriceTalks\n@UniswapEarlyCalls'
                          '\n@TradeCoinUnderGround\n@uniswapgemsv2\n@defigemchat\n@sgdefi\n@The_Trading_Pit'
                          '\n@uniswapgemtargets\n@de_fi\n@deficrew',
                 'type': 'timed',
                 'delay': 1800},
    "too_fast": {'text': 'Check this [message](https://t.me/c',
                 'type': 'util',
                 'parse_mode': MARKDOWN_V2},
    "shillin": {'text': 'Available versions of shill are available:\n'
                        '/shillreddit\n'
                        '/shilltelegram or /shilltg\n'
                        '/shilltwitter',
                'aliases': ['shillin', 'shill']},
    "shillreddit": {'text': shillreddit,
                    'parse_mode': MARKDOWN_V2,
                    'type': 'timed',
                    'delay': 600},
    "shilltelegram": {'text': shilltg,
                      'aliases': ['shilltg', 'shilltelegram']},
    "shilltwitter": {'text': 'Samari.finance, charity platform with 1k holders, doxxed devs, '
                             'marketing roadmap, actual products coming up #SamariFinance'},  # todo
    "lp": {'text': 'Locked on [DxSale](https://dxsale.app/app/pages/dxlockview?id=0&add'
                   '=0x1F79B8aef7854D86e2cC89Ada44CB95a33cd72Cf&type=lplock&chain=BSC)',
           'regex': ['lp locked', 'liquidity locked', 'locked', 'lp'],
           'parse_mode': MARKDOWN_V2,
           'disable_web_page_preview': True},
    "version": {'text': 'V2',
                'regex': ['version', 'v1', 'v2']},
    "invite": {'text': f"\nPress below to recieve your personal invite link 👇",
               'type': 'util'},
    "captcha_challenge": {'text': '👇 Enter the correct answer below 👇',
                          'type': 'captcha'},
    "captcha_failed": {'text': 'Incorrect answer. Try again! ',
                       'type': 'captcha'},
    "captcha_complete": {'text': 'Congratulations, and welcome to the Samaritan family 💪\n\n'
                                 '🌜 Why Samari? 🌛\n' 
                                  'While charity alone is great, development focused on bringing utility will in the '
                                  'long run cause more donations. At Samari we want to bring all the aspects of DEFI under one umbrella' 
                                  ', to provide all living creatures in need a better future\n' 
                                  'TELEGRAM & Twitter contests starting soon with prizes determined by CONTRACT FEES, ' 
                                  'together with a 10 day campaign with KSI VIDEO EDITOR: MO SYED\n\n' 
                                  'Join the SAMARITANS on TG \n' 
                                  'TELEGRAM: t.me/SamariFinance\n' 
                                  'WEBSITE: Samari.finance\n\n' 
                                  '👉 Team doxxed\n' 
                                  '👉 Active community\n' 
                                  '👉 Charitable Organization\n' 
                                  '👉 $100K MC at launch – stable liquidity, no p&d scheme\n' 
                                  '👉 Sustainable tokenomics\n\n' 
                                  '💰 BUY $Samari (V2): https://exchange.pancakeswap.finance/#/swap?outputCurrency=0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be\n' 
                                  '📈 CHART (V2): https://poocoin.app/tokens/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be\n' 
                                  '🔒 LIQUIDITY Locked: https://dxsale.app/app/pages/dxlockview?id=0&add\n' 
                                  '✅ VERIFIED CONTRACT: https://bscscan.com/token/0xb255cddf7fbaf1cbcc57d16fe2eaffffdbf5a8be\n\n'
                                 '👇 Return to the group 👇'
                         },
    "admin_menu": {'text': 'Select option from menu to edit',
                   'type': 'admin'}
}
