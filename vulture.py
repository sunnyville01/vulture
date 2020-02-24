import os
import json
import time
import sqlite3
import requests
from os import path
import urllib.request
from operator import itemgetter
from settings import Settings
from bittrex import bittrex
from playsound import playsound


class Vulture:

    def __init__(self):

        # Settings
        self.settings = Settings()

        # Routes
        self.exchanges = self.settings.exchanges
        self.singles = self.settings.singles
        self.couples = self.settings.couples
        self.profit_threshold = self.settings.profit_threshold

        # Coins
        self.coins = {
        "crex": self.settings.crex,
        "coinex": self.settings.coinex,
        "bittrex": self.settings.bittrex,
        "hitbtc": self.settings.hitbtc,
        "cbridge": self.settings.cbridge,
        "livecoin": self.settings.livecoin,
        }

        # Prices
        self.coinex_prices = {}
        self.crex_prices = {}
        self.bittrex_prices = {}
        self.hitbtc_prices = {}
        self.cbridge_prices = {}
        self.livecoin_prices = {}

        # Coinex Markets
        with open('coinex_markets.json', 'r') as myfile:
            coinex_markets_data=myfile.read()
        self.coinex_markets = json.loads(coinex_markets_data)

        # Results
        self.results = []
        self.old_results = []
        self.new_results = []
        self.current_results = []

        while True:

            ### Update prices of all cois in all the exchanges
            # Call functions that updates prices and stores them in memory
            ###
            if "cbridge" in self.exchanges:
                self.cbridge_update_prices()
            if "crex" in self.exchanges:
                self.crex_update_prices()
            if "coinex" in self.exchanges:
                self.coinex_update_prices()
            if "bittrex" in self.exchanges:
                self.bittrex_update_prices()
            if "hitbtc" in self.exchanges:
                self.hitbtc_update_prices()
            if "livecoin" in self.exchanges:
                self.livecoin_update_prices()

            os.system('cls')

            self.current_results = self.results

            # Results
            self.results = []
            self.old_results = []
            self.new_results = []

            ### For each route find results
            self.loop_markets()

            ### Notify if new results
            self.check_new_results()

            ### Save and display results
            self.save_and_display_results()

            print("Restaring in 10 seconds")
            time.sleep(5)
            print("Restaring in 5 seconds")
            time.sleep(5)


    # Loop through all the routes
    def loop_markets(self):
        for single in self.singles:
            exchange_A = single[0]
            exchange_B = single[1]
            self.get_results(exchange_A, exchange_B, 'single')
        for couple in self.couples:
            exchange_A = couple[0]
            exchange_B = couple[1]
            self.get_results(exchange_A, exchange_B, 'couple')


    # Find Arbritrage opporunities for a route
    def get_results(self, exchange_A, exchange_B, route_type):
        p = [self.coins[exchange_A], self.coins[exchange_B]]
        common = set(p[0])
        for s in p[1:]:
            common.intersection_update(s)
        common = sorted(common)
        print(exchange_A.title(), ' to ', exchange_B.title(), '. Route Type:', route_type)

        if route_type == 'single':
            for coin in common:
                ask_price, bid_price = 0, 0
                try:
                    ask_price = float(self.get_price(coin, exchange_A, 'ASK'))
                    bid_price = float(self.get_price(coin, exchange_B, 'BID'))
                except Exception as e:
                    # print(e, coin, exchange_A, exchange_B, route_type)
                    continue
                else:
                    if (bid_price is None) or (ask_price is None) :
                        # print('Error obtaining bid or ask', coin, exchange_A, exchange_B, route_type)
                        continue
                    elif bid_price == 0 or float(ask_price) == 0:
                        # print("Problem with 0 division", coin, exchange_A, exchange_B, route_type)
                        continue
                    else:
                        pct_change = ((bid_price - ask_price) / ask_price) * 100.0

                        # Check if arbritrage is possible
                        if bid_price > ask_price:
                            if pct_change > self.profit_threshold:
                                result = {'Buy at': exchange_A.title(), 'Sell at': exchange_B.title(), 'Coin': coin, 'Ask': ask_price, 'Bid': bid_price, 'Profit': pct_change}
                                self.results.append(result)
        else:
            for coin in common:
                ask_price_A, bid_price_A, ask_price_B, bid_price_B = 0, 0, 0, 0
                try:
                    ask_price_A = float(self.get_price(coin, exchange_A, 'ASK'))
                    bid_price_A = float(self.get_price(coin, exchange_A, 'BID'))
                    ask_price_B = float(self.get_price(coin, exchange_B, 'ASK'))
                    bid_price_B = float(self.get_price(coin, exchange_B, 'BID'))
                except Exception as e:
                    # print(e, coin, exchange_A, exchange_B, route_type)
                    continue
                else:
                    if (ask_price_A is None) or (ask_price_B is None) or (bid_price_A is None) or (bid_price_B is None) :
                        # print('Error obtaining bid or ask', coin, exchange_A, exchange_B, route_type)
                        continue
                    elif float(ask_price_A) == 0 or float(bid_price_A) == 0 or float(ask_price_B) == 0 or float(bid_price_B) == 0:
                        # print("Problem with 0 price", coin, exchange_A, exchange_B, route_type)
                        continue
                    else:
                        if (ask_price_A < bid_price_B) or (ask_price_B < bid_price_A):
                            if ask_price_A < bid_price_B:
                                ask_price = ask_price_A
                                bid_price = bid_price_B
                                buy_at = exchange_A
                                sell_at = exchange_B

                            elif ask_price_B < bid_price_A:
                                ask_price = ask_price_B
                                bid_price = bid_price_A
                                buy_at = exchange_B
                                sell_at = exchange_A

                            pct_change = ((bid_price - ask_price) / ask_price) * 100.0
                            # Check if arbritrage is possible
                            if bid_price > ask_price:
                                if pct_change > self.profit_threshold:
                                    result = {'Buy at': buy_at.title(), 'Sell at': sell_at.title(), 'Coin': coin, 'Ask': ask_price, 'Bid': bid_price, 'Profit': pct_change}
                                    self.results.append(result)

    # Call the right function depending on the exchange
    def get_price(self, coin, exchange, price_type):
        price_type = price_type.lower()
        exchange_functions = {
            'coinex': self.coinex_prices,
            'crex': self.crex_prices,
            'bittrex': self.bittrex_prices,
            'hitbtc': self.hitbtc_prices,
            'cbridge': self.cbridge_prices,
            'livecoin': self.livecoin_prices,
        }
        try:
            price = exchange_functions[exchange][coin][price_type]
        except Exception as e:
            pass
            # print(e, coin, exchange, price_type)
        else:
            return price

    # Check if there are new results in results
    def check_new_results(self):
        for result in self.results:
            self.filter_new_results(result)

    # Check if there are new results
    def filter_new_results(self, result):

        present = False
        for item in self.current_results:
            if (result['Buy at'] == item['Buy at'] and result['Sell at'] == item['Sell at'] and result['Coin' ] == item['Coin']):
                new_profit = float(result['Profit'])
                old_profit = float(item['Profit'])
                present = True
                if new_profit > 2 * old_profit:
                    self.new_results.append(result)
                    break
                else:
                    self.old_results.append(result)
                    break

        if present == False:
            self.new_results.append(result)

    def save_and_display_results(self):
        # Final and Save Results
        # Clear Screen
        print("\n\nResults:")
        self.old_results = sorted(self.old_results, key=itemgetter('Buy at'), reverse=True)
        for result in self.old_results:
            print(result['Buy at'] +' to '+ result['Sell at'] +': '+ result['Coin'] + '. Ask: '+ str(result['Ask']) +'- Bid:'+ str(result['Bid']) +'- Profit: '+ str(result['Profit']) + '%')

        if self.new_results:
            print("\n\nNew Results:")
            self.new_results = sorted(self.new_results, key=itemgetter('Buy at'), reverse=True)
            alert_worthy = False
            for result in self.new_results:
                print(result['Buy at'] +' to '+ result['Sell at'] +': '+ result['Coin'] + '. Ask: '+ str(result['Ask']) +'- Bid:'+ str(result['Bid']) +'- Profit: '+ str(result['Profit']) + '%')
                if result['Profit'] > 2:
                    alert_worthy = True
            # Play sound
            if alert_worthy == True:
                playsound('more.mp3')



    ###
    # Queriing prices from Apis
    ###

    # Update Cbridge Prices Table
    def cbridge_update_prices(self):
        try:
            url = 'https://api.crypto-bridge.org/api/v1/ticker'
            json_data = requests.get(url, timeout=5).json()
        except Exception as e:
            print(e, 'Cbridge')
        else:
            for item in json_data: # Add new prices to table
                if item["id"].endswith('_BTC'):
                    coin = item["id"][:-4]
                    ask = item["ask"]
                    bid = item["bid"]
                    self.cbridge_prices[coin] = {"ask": ask, "bid": bid}
    # Update Crex Prices Table
    def crex_update_prices(self):
        try:
            # Market IDs and prices
            url = 'https://api.crex24.com/v2/public/tickers'
            json_data = requests.get(url, timeout=5).json()
        except Exception as e:
            print(e, 'Crex')
        else:
            for item in json_data: # Add new prices to table
                instrument = item["instrument"]
                if instrument.endswith('BTC'):
                    coin = instrument[:-4]
                    bid = item["bid"]
                    ask = item["ask"]
                    self.crex_prices[coin] = {"ask": ask, "bid": bid}
    # Update Crex Prices Table
    def livecoin_update_prices(self):
        try:
            # Market IDs and prices
            url = 'https://api.livecoin.net/exchange/ticker'
            json_data = requests.get(url, timeout=5).json()
        except Exception as e:
            print(e, 'Livecoin')
        else:
            for item in json_data: # Add new prices to table
                symbol = item["symbol"]
                if symbol.endswith('BTC'):
                    coin = symbol[:-4]
                    bid = item["best_bid"]
                    ask = item["best_ask"]
                    self.livecoin_prices[coin] = {"ask": ask, "bid": bid}
    # Update Coinex Prices Table
    def coinex_update_prices(self):
        try:
            # Market IDs and prices
            url = 'https://www.coinexchange.io/api/v1/getmarketsummaries'
            json_data = requests.get(url, timeout=5).json()["result"]
        except Exception as e:
            print(e, 'Coinex')
        else:
            for item in json_data: # Add new prices to table
                market_id = item["MarketID"]
                try:
                    coin = [i for i in self.coinex_markets if i['MarketID'] == market_id][0]['MarketAssetCode']
                except Exception as e:
                    continue
                else:
                    bid = float(item["BidPrice"])
                    ask = float(item["AskPrice"])
                    self.coinex_prices[coin] = {"ask": ask, "bid": bid}
    # Update Bittrex Prices Table
    def bittrex_update_prices(self):
        try:
            url = 'https://api.bittrex.com/api/v1.1/public/getmarketsummaries'
            json_data = requests.get(url, timeout=5).json()["result"]
        except Exception as e:
            print(e, "Bittrex")
        else:
            for item in json_data: # Add new prices to table
                if item["MarketName"].startswith('BTC'):
                    coin = item["MarketName"][4:]
                    ask = item["Ask"]
                    bid = item["Bid"]
                    self.bittrex_prices[coin] = {"ask": ask, "bid": bid}
    # Update Hitbtc Prices Table
    def hitbtc_update_prices(self):
        try:
            url = 'https://api.hitbtc.com/api/2/public/ticker'
            json_data = requests.get(url, timeout=5).json()
        except Exception as e:
            print(e, "Hitbtc")
        else:
            for item in json_data: # Add new prices to table
                if item["symbol"].endswith('BTC'):
                    coin = item["symbol"][:-3]
                    ask = item["ask"]
                    bid = item["bid"]
                    self.hitbtc_prices[coin] = {"ask": ask, "bid": bid}

if __name__ == '__main__':
    i = Vulture()


# coins = []
# coins.append(coin)

# coins = set(coins)
# coins = sorted(list(coins))
# print(coins)
