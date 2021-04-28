import datetime
import ccxt
import pandas as pd

print(ccxt.__version__)
print(pd.__version__)

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option("display.max_rows", 500)


class BA(ccxt.binance):

    def __init__(self):
        super().__init__({
            'apiKey': '',  # 自己的api key
            'secret': '',  # 自己的secret
            # 翻墙时代理设置 我用的翻墙服务商是：https://mqk4azjxg8skg6gfelpb.stcserver-cloud.com/auth/register?code=flyer
            # 'proxies': {
            #     'http': 'http://127.0.0.1:1087',
            #     'https': 'http://127.0.0.1:1087'
            # }
        })
        self.quarterly_symbols_info = self.__get_quarterly_symbols_info()
        self.spot_fee_rate = 0  # 根据自己的手续费进行修改
        self.future_fee_rate = 4 / 10000  # 根据自己的手续费进行修改

    def __get_quarterly_symbols_info(self):
        symbols = {}
        markets = self.load_markets()
        for symbol in self.dapiPublicGetExchangeInfo()['symbols']:
            future_symbol = symbol['symbol']
            if '06' in future_symbol:
                spot_symbol = future_symbol[0:-10] + '/USDT'
                symbols[future_symbol[0:-10]] = (future_symbol,
                                                 int(symbol['pricePrecision']),  # 期货精度
                                                 int(symbol['contractSize']),  # 期货每张合约的价格
                                                 spot_symbol,
                                                 markets[spot_symbol]['precision']['price'],  # 现货价格精度
                                                 markets[spot_symbol]['precision']['amount'])  # 现货数量精度

        return symbols

    def get_spread_info(self):
        spot_future_spread = []
        for symbol_info in self.quarterly_symbols_info.values():
            symbol_future = symbol_info[0]
            symbol_spot = symbol_info[3]
            symbol_spot_temp = symbol_spot.replace('/', '')
            spot_buy1_price = float(self.publicGetTickerBookTicker(params={'symbol': symbol_spot_temp})['bidPrice'])
            spot_sell1_price = float(self.publicGetTickerBookTicker(params={'symbol': symbol_spot_temp})['askPrice'])
            future_buy1_price = float(
                self.dapiPublicGetTickerBookTicker(params={'symbol': symbol_future})[0]['bidPrice'])
            future_sell1_price = float(
                self.dapiPublicGetTickerBookTicker(params={'symbol': symbol_future})[0]['askPrice'])
            open_spread = future_buy1_price / spot_sell1_price - 1
            close_spread = future_sell1_price / spot_buy1_price - 1
            spot_future_spread.append((
                symbol_future, symbol_spot,
                open_spread,  # 2
                future_buy1_price, spot_sell1_price,
                close_spread,  # 5
                future_sell1_price, spot_buy1_price))
        df = pd.DataFrame(spot_future_spread)

        df.columns = ['symbol_future', 'symbol_spot',
                      'open_spread', 'future_buy1_price', 'spot_sell1_price',
                      'close_spread', 'future_sell1_price', 'spot_buy1_price']
        print(df.sort_values('open_spread').to_string(index=False))  # 按照开仓价格排序，可以按需修改成按照平仓价格排序，交易的时候可以去掉该行

        open_info = df[df['open_spread'] == df['open_spread'].max()].values[0].tolist()[0:5]

        close_info = df[df['close_spread'] == df['close_spread'].min()].values[0].tolist()
        close_info = close_info[0:2] + close_info[5:]

        print(datetime.datetime.now())
        print('开仓交易所需信息:', '开仓价差', '期货买一价', '现货卖一价')
        print(open_info)
        print('平仓仓交易所需信息:', '平仓价差', '期货卖一价', '现货买一价')
        print(close_info)
        return open_info, close_info


BA().get_spread_info()
